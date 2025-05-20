from selectolax.parser import HTMLParser
import requests, hashlib, json, utils, datetime as dt

def run(portal):
    html = HTMLParser(requests.get(portal["url"], timeout=30).text)
    for tr in html.css(portal["selector"]):
        cols = [c.text(strip=True) for c in tr.css("td")]
        if portal["id"] == "privacy_rights":
            # PRC: entity, breach_date, notice_date, records, breach_type, entity_type, state, notice_url
            if len(cols) < 8: continue
            row = {
                "entity": cols[0],
                "breach_date": cols[1],
                "notice_date": cols[2],
                "records": int(cols[3].replace(",", "") or 0),
                "breach_type": cols[4],
                "entity_type": cols[5],
                "state": cols[6],
                "notice_url": tr.css_first("a")['href'] if tr.css_first("a") else None,
                "_portal": portal["id"]
            }
        else:
            if len(cols) < 3: continue
            row = {
                "notice_date": cols[0],
                "entity": cols[1],
                "records": int(cols[2].replace(",", "") or 0),
                "_portal": portal["id"]
            }
        utils.insert_row(row)
