"""Bourse Direct operation-notice adapter for the reviewed engine boundary."""

import re
from html.parser import HTMLParser
from urllib.parse import parse_qs, urljoin, urlsplit

CHAINS = {
    "open_calendar": [
        {"method": "locator", "arguments": [{"selector": "a[href='/fr/page/avis-operes']"}]},
        {"method": "first"},
        {"method": "click"},
        {"method": "frame_locator", "arguments": [{"selector": "iframe[src*='avis-operes.php']"}]},
        {"method": "locator", "arguments": [{"selector_or_locator": "body"}]},
        {"method": "inner_html"},
    ],
    "calendar": [
        {"method": "frame_locator", "arguments": [{"selector": "iframe[src*='avis-operes.php']"}]},
        {"method": "locator", "arguments": [{"selector_or_locator": "body"}]},
        {"method": "inner_html"},
    ],
    "previous_month": [
        {"method": "frame_locator", "arguments": [{"selector": "iframe[src*='avis-operes.php']"}]},
        {"method": "locator", "arguments": [{"selector_or_locator": "a[title='Mois précédent']"}]},
        {"method": "click"},
        {"method": "locator", "arguments": [{"selector_or_locator": "body"}]},
        {"method": "inner_html"},
    ],
}

_NOTICE = "/priv/new/releveOpe.php"
_EMPTY = "Vous n'avez pas effectué d'opération ce mois-ci."


class _Document(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.accounts, self.links, self.text = [], [], []
        self._select = False
        self._option = None
        self._anchor = None
        self.select_count = 0
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "select":
            self._select = values.get("id") == "nc"
            self.select_count += int(self._select)
        elif tag == "option" and self._select:
            self._option = {"value": values.get("value"), "selected": "selected" in values, "text": ""}
            self.accounts.append(self._option)
        elif tag == "a":
            self._anchor = dict(values, text="")
            self.links.append(self._anchor)

    def handle_endtag(self, tag):
        if tag == "select":
            self._select = False
        elif tag == "option":
            self._option = None
        elif tag == "a":
            self._anchor = None

    def handle_data(self, data):
        self.text.append(data)
        if self._option is not None:
            self._option["text"] += data
        if self._anchor is not None:
            self._anchor["text"] += data


def _account(document, kind):
    pattern = re.compile(r"\(Compte\s+" + re.escape(kind) + r"\)\s*$", re.IGNORECASE)
    found = [item for item in document.accounts if pattern.search(" ".join(item["text"].split()))]
    if (document.select_count != 1 or len(found) != 1 or not found[0]["value"]
            or len({item["value"] for item in document.accounts}) != len(document.accounts)):
        raise ValueError("account identity is ambiguous")
    return found[0]


def _target(value, account, period, *, pdf=False):
    parts = urlsplit(value)
    if parts.path != _NOTICE or parts.fragment or parts.username or parts.password:
        raise ValueError("notice source path is not proven")
    query = parse_qs(parts.query, keep_blank_values=True)
    expected = {"nc", "type", "year", "month", "day", "trash"} | ({"pdf"} if pdf else set())
    if set(query) != expected or any(len(items) != 1 or not items[0] for items in query.values()):
        raise ValueError("notice identity is incomplete")
    if query["nc"][0] != account or query["type"][0] != "RO" or query["trash"][0] != "/avis.pdf":
        raise ValueError("notice identity changed")
    if pdf and query["pdf"] != ["1"]:
        raise ValueError("original link is not a PDF")
    observed = (int(query["year"][0]), int(query["month"][0]))
    if observed != period:
        raise ValueError("notice month changed")
    return value, (int(query["year"][0]), int(query["month"][0]), int(query["day"][0]))


def _calendar(document, account, period):
    selected = [item for item in document.accounts if item["selected"]]
    if (len(selected) != 1 or selected[0]["value"] != account or document.select_count != 1):
        raise ValueError("selected account changed")
    previous = [re.fullmatch(r"javascript:MoisPrecedent\('RO',([0-9]+),([0-9]+),([0-9]+)\)", item.get("href", ""))
                for item in document.links]
    previous = [item for item in previous if item]
    if len(previous) != 1 or previous[0][1] != account or (int(previous[0][3]), int(previous[0][2])) != period:
        raise ValueError("calendar month is not proven")
    offered = []
    for item in document.links:
        match = re.fullmatch(r"(?:javascript:)?ouvrePopup\('([^']+)'(?:,[^)]*)?\);?", item.get("href", ""))
        if "linkE" in item.get("class", "").split():
            if not match:
                raise ValueError("offered notice control changed")
            offered.append(_target(urljoin("https://www.boursedirect.fr/", match[1]), account, period))
    if not offered and _EMPTY not in "".join(document.text):
        raise ValueError("empty month is not proven")
    if len({url for url, _ in offered}) != len(offered):
        raise ValueError("offered notice identity is ambiguous")
    return offered


def collect(api, options):
    """Traverse bounded offered months and save each unchanged original PDF."""
    account_type = options["account_type"]
    months = api.months
    html = api.call("open_calendar")
    document = _Document(html)
    account = _account(document, account_type)
    if not account["selected"]:
        raise ValueError("configured account is not selected")
    account = _account(document, account_type)
    account_id = account["value"]
    for index, period in enumerate(months):
        document = _Document(document if isinstance(document, str) else api.call("calendar"))
        confirmed = _account(document, account_type)
        if confirmed["value"] != account_id:
            raise ValueError("account changed")
        offered = _calendar(document, account_id, period)
        api.offered(len(offered))
        for notice_url, day in offered:
            notice = _Document(api.read(notice_url).decode("utf-8", "replace"))
            links = [item["href"] for item in notice.links if item.get("href") and item.get("text", "").strip() == "Format PDF"]
            if len(links) != 1:
                raise ValueError("original PDF link is not unique")
            pdf_url, pdf_day = _target(urljoin(notice_url, links[0]), account_id, period, pdf=True)
            if pdf_day != day:
                raise ValueError("original PDF date changed")
            api.save_original(pdf_url, f"BourseDirect_{account_type}_{day[0]:04d}-{day[1]:02d}-{day[2]:02d}.pdf")
        if index + 1 < len(months):
            document = api.call("previous_month")
