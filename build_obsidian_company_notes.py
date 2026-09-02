from __future__ import annotations

import csv
import math
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "output" / "mops_financials_full" / "financial_statements_long.csv"
VAULT = ROOT / "output" / "mops_financials_md"
LATEST = (2026, 2)
PREVIOUS = (2025, 2)


CATEGORIES = [
    ("上游", "晶圓代工與先進封裝", "先進製程晶圓代工與高密度先進封裝", ["ASIC設計服務_IP"], ["晶片封測服務", "ABF載板_高階PCB"]),
    ("上游", "晶片封測服務", "高階晶片封裝、測試與量產驗證", ["晶圓代工與先進封裝", "ASIC設計服務_IP"], ["ABF載板_高階PCB", "伺服器ODM_整機櫃組裝"]),
    ("上游", "ASIC設計服務_IP", "客製化 AI 晶片架構、IP 整合與委託設計服務", [], ["晶圓代工與先進封裝", "晶片封測服務"]),
    ("上游", "伺服器遠端管理_傳輸", "BMC 伺服器管理晶片與 PCIe 等高速傳輸介面", ["晶圓代工與先進封裝"], ["ABF載板_高階PCB", "伺服器ODM_整機櫃組裝", "品牌伺服器與板卡"]),
    ("中游", "散熱管理", "水冷板、CDU、均熱與伺服器氣冷零組件", [], ["伺服器ODM_整機櫃組裝", "品牌伺服器與板卡"]),
    ("中游", "電源供應系統", "高瓦數伺服器電源、機櫃電源與備援電池模組", [], ["伺服器ODM_整機櫃組裝", "品牌伺服器與板卡", "邊緣運算_工業AI"]),
    ("中游", "ABF載板_高階PCB", "晶片載板、高多層伺服器主板與高速銅箔基板", ["晶圓代工與先進封裝", "晶片封測服務", "伺服器遠端管理_傳輸"], ["伺服器ODM_整機櫃組裝", "品牌伺服器與板卡", "高速網路交換器"]),
    ("中游", "伺服器滑軌與機殼", "高負重伺服器導軌與高密度伺服器機箱", [], ["伺服器ODM_整機櫃組裝", "品牌伺服器與板卡"]),
    ("中游", "高速連接器與線束", "機櫃電源線、高頻高速連接器與內部線束", [], ["伺服器ODM_整機櫃組裝", "品牌伺服器與板卡", "高速網路交換器"]),
    ("下游", "伺服器ODM_整機櫃組裝", "AI 伺服器與整機櫃設計、製造、組裝及交付", ["散熱管理", "電源供應系統", "ABF載板_高階PCB", "伺服器滑軌與機殼", "高速連接器與線束"], []),
    ("下游", "品牌伺服器與板卡", "企業級 AI 伺服器、主機板與 GPU 加速板卡", ["散熱管理", "電源供應系統", "ABF載板_高階PCB", "伺服器滑軌與機殼", "高速連接器與線束"], []),
    ("下游", "邊緣運算_工業AI", "工業自動化、嵌入式系統與邊緣 AI 運算平台", ["電源供應系統", "ABF載板_高階PCB"], []),
    ("下游", "高速網路交換器", "資料中心 400G／800G 高速乙太網路交換器", ["ABF載板_高階PCB", "高速連接器與線束"], []),
]


COMPANIES = [
    ("2330", "台積電", "晶圓代工與先進封裝", "專注晶圓代工，提供先進製程及 CoWoS 等先進封裝服務。"),
    ("3711", "日月光投控", "晶片封測服務", "提供半導體封裝、測試與電子製造服務。"),
    ("2449", "京元電子", "晶片封測服務", "以晶圓測試、成品測試及高階晶片測試服務為核心。"),
    ("3661", "世芯-KY", "ASIC設計服務_IP", "提供高階客製化 ASIC 設計與量產服務，聚焦高效能運算應用。"),
    ("3443", "創意", "ASIC設計服務_IP", "提供 ASIC 設計、SoC 整合、IP 與量產管理服務。"),
    ("3035", "智原", "ASIC設計服務_IP", "提供 ASIC 設計服務、矽智財與晶片量產支援。"),
    ("5274", "信驊", "伺服器遠端管理_傳輸", "主要產品為伺服器 BMC 遠端管理晶片。"),
    ("5269", "祥碩", "伺服器遠端管理_傳輸", "設計高速傳輸介面晶片，涵蓋 USB 與 PCIe 相關產品。"),
    ("4966", "譜瑞-KY", "伺服器遠端管理_傳輸", "提供高速介面與顯示傳輸晶片及訊號完整性解決方案。"),
    ("3017", "奇鋐", "散熱管理", "提供風扇、散熱模組、水冷板及資料中心液冷系統。"),
    ("3324", "雙鴻", "散熱管理", "提供伺服器與高效能運算的氣冷及液冷散熱方案。"),
    ("3653", "健策", "散熱管理", "提供均熱、散熱、導線架與高階伺服器相關精密零組件。"),
    ("2308", "台達電", "電源供應系統", "提供資料中心電源、散熱、能源管理與基礎設施方案。"),
    ("2301", "光寶科", "電源供應系統", "提供伺服器電源供應器、電源管理與光電產品。"),
    ("3037", "欣興", "ABF載板_高階PCB", "生產 IC 載板、印刷電路板與高密度互連板。"),
    ("8046", "南電", "ABF載板_高階PCB", "以 IC 載板與高階印刷電路板為主要產品。"),
    ("2368", "金像電", "ABF載板_高階PCB", "聚焦伺服器、網通等高多層印刷電路板。"),
    ("2383", "台光電", "ABF載板_高階PCB", "生產高速高頻銅箔基板，供伺服器與網通 PCB 使用。"),
    ("2059", "川湖", "伺服器滑軌與機殼", "提供伺服器、資料中心與高階設備使用的精密滑軌。"),
    ("8210", "勤誠", "伺服器滑軌與機殼", "設計製造伺服器機殼及資料中心硬體機構件。"),
    ("6584", "南俊國際", "伺服器滑軌與機殼", "生產伺服器與工業設備使用的滑軌及機構件。"),
    ("3665", "貿聯-KY", "高速連接器與線束", "提供資料中心、高效能運算與工業應用線束及連接方案。"),
    ("3533", "嘉澤", "高速連接器與線束", "提供處理器插槽、高速連接器與伺服器連接元件。"),
    ("6290", "良維", "高速連接器與線束", "生產電源線、連接線組與電源相關零組件。"),
    ("2317", "鴻海", "伺服器ODM_整機櫃組裝", "提供雲端與 AI 伺服器、整機櫃及電子製造服務。"),
    ("2382", "廣達", "伺服器ODM_整機櫃組裝", "透過雲端運算事業提供伺服器、AI 系統與整機櫃產品。"),
    ("6669", "緯穎", "伺服器ODM_整機櫃組裝", "專注超大型資料中心伺服器、儲存及機櫃級系統。"),
    ("3231", "緯創", "伺服器ODM_整機櫃組裝", "提供伺服器、AI 運算設備與資訊產品設計製造服務。"),
    ("2356", "英業達", "伺服器ODM_整機櫃組裝", "提供伺服器、資料中心設備與資訊產品製造服務。"),
    ("2376", "技嘉", "品牌伺服器與板卡", "提供伺服器、主機板、顯示卡與企業運算產品。"),
    ("2357", "華碩", "品牌伺服器與板卡", "提供伺服器、主機板、工作站與商用運算設備。"),
    ("2377", "微星", "品牌伺服器與板卡", "提供主機板、顯示卡、伺服器與高效能運算產品。"),
    ("3706", "神達", "品牌伺服器與板卡", "提供雲端運算伺服器、儲存與企業級運算系統。"),
    ("2395", "研華", "邊緣運算_工業AI", "提供工業電腦、邊緣運算、物聯網與自動化平台。"),
    ("6166", "凌華", "邊緣運算_工業AI", "提供邊緣 AI、嵌入式運算、量測與自動化平台。"),
    ("2345", "智邦", "高速網路交換器", "設計製造資料中心與電信網路交換器及網通設備。"),
]


def slug(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff_-]+", "_", value).strip("_")


def company_page(stock_id: str, name: str) -> str:
    return f"{stock_id} {name}"


def category_page(category: str) -> str:
    return f"次領域-{category}"


def stage_page(stage: str) -> str:
    return f"供應鏈-{stage}"


def wiki_list(names: list[str]) -> str:
    return "、".join(f"[[{name}]]" for name in names) if names else "無（本研究範圍的邊界）"


def number(value: str | None) -> float | None:
    if value in (None, "", "--"):
        return None
    try:
        result = float(value)
    except ValueError:
        return None
    return result if math.isfinite(result) else None


def percent(value: float | None) -> str:
    return "無資料" if value is None else f"{value:.2f}%"


def amount(value: float | None) -> str:
    return "無資料" if value is None else f"{value / 100_000:,.2f} 億元"


def change(current: float | None, previous: float | None) -> float | None:
    if current is None or previous in (None, 0):
        return None
    return (current / previous - 1) * 100


def ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return numerator / denominator * 100


def load_financials() -> dict[tuple[str, int, int], dict[str, float]]:
    wanted = {
        "營業收入": "revenue",
        "營業毛利（毛損）": "gross_profit",
        "營業利益（損失）": "operating_income",
        "本期淨利（淨損）": "net_income",
    }
    result: dict[tuple[str, int, int], dict[str, float]] = defaultdict(dict)
    with SOURCE.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["statement"] != "income_statement" or row["account"] not in wanted:
                continue
            key = (row["stock_id"], int(row["year"]), int(row["quarter"]))
            metric = wanted[row["account"]]
            value = number(row["value"])
            if value is not None and metric not in result[key]:
                result[key][metric] = value
    return result


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def profitability(financials: dict[tuple[str, int, int], dict[str, float]], stock_id: str) -> str:
    current = financials.get((stock_id, *LATEST), {})
    previous = financials.get((stock_id, *PREVIOUS), {})
    revenue = current.get("revenue")
    gross = current.get("gross_profit")
    operating = current.get("operating_income")
    net = current.get("net_income")
    revenue_yoy = change(revenue, previous.get("revenue"))
    operating_yoy = change(operating, previous.get("operating_income"))
    net_yoy = change(net, previous.get("net_income"))
    status = "獲利" if operating is not None and operating > 0 else "營業虧損"
    trend = "成長" if revenue_yoy is not None and revenue_yoy > 0 else "衰退或持平"
    return f"""資料期間為 2026Q2 累計，年增率以 2025Q2 累計為基準。金額依 MOPS 千元欄位換算為億元。

| 指標 | 2026Q2 累計 | 年增率／比率 |
|---|---:|---:|
| 營業收入 | {amount(revenue)} | {percent(revenue_yoy)} |
| 營業毛利 | {amount(gross)} | 毛利率 {percent(ratio(gross, revenue))} |
| 營業利益 | {amount(operating)} | 年增 {percent(operating_yoy)}；營益率 {percent(ratio(operating, revenue))} |
| 本期淨利 | {amount(net)} | 年增 {percent(net_yoy)}；淨利率 {percent(ratio(net, revenue))} |

**數據摘要：** 目前為{status}狀態，營收年增方向為{trend}。此摘要只描述財報數字，不構成估值或投資建議。"""


def build() -> None:
    category_info = {category: (stage, role, upstream, downstream) for stage, category, role, upstream, downstream in CATEGORIES}
    companies_by_category: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for stock_id, name, category, _ in COMPANIES:
        companies_by_category[category].append((stock_id, name))

    financials = load_financials()

    for stock_id, name, category, scope in COMPANIES:
        stage, role, upstream, downstream = category_info[category]
        peers = [company_page(peer_id, peer_name) for peer_id, peer_name in companies_by_category[category] if peer_id != stock_id]
        up_pages = [category_page(item) for item in upstream]
        down_pages = [category_page(item) for item in downstream]
        content = f"""---
type: company
stock_id: "{stock_id}"
company: "{name}"
stage: "{stage}"
category: "{category}"
tags:
  - AI供應鏈
  - 公司
  - {stage}
---

# {name}（{stock_id}）

> [!summary] 供應鏈定位
> [[{stage_page(stage)}]] → [[{category_page(category)}]] → [[{company_page(stock_id, name)}]]

## 業務範圍

{scope}

在本研究分類中主要扮演「{role}」角色。

## 供應鏈關係

- 上游相關次領域：{wiki_list(up_pages)}
- 下游相關次領域：{wiki_list(down_pages)}
- 同次領域公司：{wiki_list(peers)}

> [!warning] 關係解讀
> 上述連結表示產業鏈位置相鄰或同業關係，不等同已證實的直接交易、供貨或客戶關係。

## 盈利狀況

{profitability(financials, stock_id)}

## 研究入口

- [[AI供應鏈投資研究]]
- [[供應鏈關係圖]]
- [[{category_page(category)}]]
"""
        write(VAULT / "公司" / f"{company_page(stock_id, name)}.md", content)

    for stage, category, role, upstream, downstream in CATEGORIES:
        company_links = [company_page(stock_id, name) for stock_id, name in companies_by_category[category]]
        content = f"""---
type: category
stage: "{stage}"
category: "{category}"
tags:
  - AI供應鏈
  - 次領域
  - {stage}
---

# {category}

## 定位

[[{stage_page(stage)}]]中的次領域，主要角色為：{role}。

## 公司

{chr(10).join(f'- [[{item}]]' for item in company_links)}

## 產業鏈相鄰關係

- 上游相關次領域：{wiki_list([category_page(item) for item in upstream])}
- 下游相關次領域：{wiki_list([category_page(item) for item in downstream])}

> [!note]
> 相鄰關係用於產業研究與 Obsidian Graph 導覽，不代表公司間必然存在直接交易。

## 導覽

- [[AI供應鏈投資研究]]
- [[供應鏈關係圖]]
"""
        write(VAULT / "次領域" / f"{category_page(category)}.md", content)

    for stage in ["上游", "中游", "下游"]:
        categories = [category_page(category) for item_stage, category, *_ in CATEGORIES if item_stage == stage]
        content = f"""---
type: stage
stage: "{stage}"
tags:
  - AI供應鏈
  - 供應鏈環節
---

# {stage}

## 次領域

{chr(10).join(f'- [[{item}]]' for item in categories)}

## 供應鏈導覽

- [[供應鏈-上游]]
- [[供應鏈-中游]]
- [[供應鏈-下游]]
- [[供應鏈關係圖]]
- [[AI供應鏈投資研究]]
"""
        write(VAULT / "供應鏈" / f"{stage_page(stage)}.md", content)

    index_rows = []
    for stock_id, name, category, _ in COMPANIES:
        stage = category_info[category][0]
        index_rows.append(f"| [[{company_page(stock_id, name)}]] | [[{stage_page(stage)}]] | [[{category_page(category)}]] |")
    index = f"""---
type: index
tags:
  - AI供應鏈
  - MOC
---

# AI 供應鏈投資研究

## 供應鏈入口

- [[供應鏈-上游]]
- [[供應鏈-中游]]
- [[供應鏈-下游]]
- [[供應鏈關係圖]]

## 公司索引

| 公司 | 供應鏈環節 | 次領域 |
|---|---|---|
{chr(10).join(index_rows)}

## 資料說明

- 盈利資料來源：`../mops_financials_full/financial_statements_long.csv`
- 財報數字為 2026Q2 累計，年增比較基期為 2025Q2 累計。
- 供應鏈連結代表產業位置關聯；未經公開資料驗證，不宣稱公司間存在直接交易。
"""
    write(VAULT / "AI供應鏈投資研究.md", index)

    graph_lines = []
    stage_ids = {"上游": "STAGE_UP", "中游": "STAGE_MID", "下游": "STAGE_DOWN"}
    category_ids = {category: f"CAT{index:02d}" for index, (_, category, *_) in enumerate(CATEGORIES, start=1)}
    for stage, category, *_ in CATEGORIES:
        graph_lines.append(
            f'    {stage_ids[stage]}["[[{stage_page(stage)}|{stage}]]"] --> '
            f'{category_ids[category]}["[[{category_page(category)}|{category}]]"]'
        )
    for stock_id, name, category, _ in COMPANIES:
        graph_lines.append(f'    {category_ids[category]} --> C{stock_id}["[[{company_page(stock_id, name)}|{name} {stock_id}]]"]')
    graph = f"""---
type: graph
tags:
  - AI供應鏈
  - 關係圖
---

# 供應鏈關係圖

以下圖表呈現「供應鏈環節 → 次領域 → 公司」。點擊節點可開啟對應筆記。

```mermaid
flowchart LR
{chr(10).join(graph_lines)}
```

## 跨次領域關係

{chr(10).join(f'- [[{category_page(category)}]]：上游 {wiki_list([category_page(item) for item in upstream])}；下游 {wiki_list([category_page(item) for item in downstream])}' for _, category, _, upstream, downstream in CATEGORIES)}

> [!warning]
> 本圖是產業結構圖，不是已驗證的公司供貨關係圖。

返回 [[AI供應鏈投資研究]]。
"""
    write(VAULT / "供應鏈關係圖.md", graph)


if __name__ == "__main__":
    build()
