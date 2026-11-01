"""把模板式报告的边框与字体内联到单元格，确保 html-to-doc 能转出边框。"""

from pathlib import Path
from bs4 import BeautifulSoup

RID = "40592fbf-5ca6-4125-b4ac-099880a1489e"
p = Path(__file__).resolve().parents[2] / "output" / RID / "stage2" / "formatted-实验六报告.html"

FORM = "border:0.5pt solid #000000;padding:5pt 7pt;vertical-align:top;"
FORM_HEAD = FORM + 'font-family:"黑体",SimHei,sans-serif;font-size:12pt;'
T3_HEAD = (
    "border-top:1.5pt solid #000000;border-bottom:0.75pt solid #000000;"
    'padding:3pt 4pt;text-align:left;font-weight:bold;font-family:"黑体",SimHei,sans-serif;'
)
T3_BOT = "border-bottom:1.5pt solid #000000;padding:3pt 4pt;"
T3_MID = "padding:3pt 4pt;"

soup = BeautifulSoup(p.read_text(encoding="utf-8"), "html.parser")

outer = soup.find_all("table")[0]
for tr in outer.find_all("tr"):
    for td in tr.find_all("td", recursive=False):
        is_head = "head-td" in (td.get("class") or [])
        td["style"] = FORM_HEAD if is_head else FORM

for tbl in soup.find_all("table", class_="t3"):
    tbl["style"] = "border-collapse:collapse;width:100%;font-size:10.5pt;"
    for th in tbl.find_all("th"):
        th["style"] = T3_HEAD + ("text-align:center;" if "c" in (th.get("class") or []) else "")
    for tb in tbl.find_all("tbody"):
        rows = tb.find_all("tr")
        if not rows:
            continue
        for td in rows[-1].find_all("td"):
            td["style"] = T3_BOT + ("text-align:center;" if "c" in (td.get("class") or []) else "")
        for tr in rows[:-1]:
            for td in tr.find_all("td"):
                td["style"] = T3_MID + ("text-align:center;" if "c" in (td.get("class") or []) else "")

p.write_text(str(soup), encoding="utf-8")
print("外框单元格:", len(outer.find_all("td")), "三线表:", len(soup.find_all("table", class_="t3")))
