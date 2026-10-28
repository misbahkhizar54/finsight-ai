from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from src.report_search import search_report, search_statements
from src.ai_answer import answer_from_extracts
import json
import sqlite3
import base64
from html import escape

st.set_page_config(page_title="FinSight AI · PSX", page_icon="📈", layout="wide")
ROOT = Path(__file__).resolve().parent

st.markdown('''<style>
.stApp {background:#0c111b;color:#e8edf5;}
[data-testid="stHeader"] {background:#0c111b;}
.block-container {max-width:1440px;padding:3.6rem 2.2rem 2rem;}
[data-testid="stSidebar"] {display:none;}
h1,h2,h3,p,label {color:#e8edf5;}
h3 {font-size:1.05rem !important;}
.brandbar {display:flex;align-items:center;justify-content:space-between;
 border-bottom:1px solid #263044;padding-bottom:16px;margin-bottom:24px;gap:12px;}
.brand {font-size:19px;font-weight:750;letter-spacing:-.5px;color:#f1f5fb;}
.brand b {color:#51d3b4;}
.status {font-size:11px;color:#95a5bb;letter-spacing:.7px;}
.company {display:flex;align-items:center;gap:14px;margin-bottom:8px;}
.symbol {background:#18352f;color:#6fe1c3;border:1px solid #2a5549;
 border-radius:9px;padding:13px 12px;font-size:15px;font-weight:750;}
.company-name {font-size:25px;font-weight:650;color:#eef3fb;letter-spacing:-.7px;}
.meta {font-size:12px;color:#9aabc1;margin-top:4px;}
.cards {display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));
 gap:12px;margin:22px 0 20px;}
.card {background:#141d2b;border:1px solid #263449;border-radius:12px;
 padding:16px 18px;min-width:0;}
.card-label {color:#9aabc1;font-size:12px;}
.card-value {color:#f2f6fc;font-size:28px;font-weight:650;line-height:1.5;
 letter-spacing:-.7px;font-variant-numeric:tabular-nums;overflow-wrap:anywhere;}
.card-value small {font-size:13px;color:#9aabc1;font-weight:400;letter-spacing:0;}
.change {font-size:12px;color:#9aabc1;}
.negative {color:#ff8396;}.positive {color:#66d9bb;}
.insights {display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
 gap:12px;margin-top:10px;}
.insight {border-left:2px solid #41668b;background:#111b29;padding:13px 16px;
 border-radius:0 8px 8px 0;color:#b4c1d3;font-size:13px;line-height:1.6;}
.insight strong {color:#e5edf8;display:block;font-size:13px;margin-bottom:4px;}
.foot {font-size:11px;color:#8192aa;border-top:1px solid #263044;
 padding-top:16px;margin-top:26px;}
@media(max-width:700px) {
 .block-container {padding-left:1rem;padding-right:1rem;}
 .company-name {font-size:21px;}.status {max-width:145px;text-align:right;}
 .cards {grid-template-columns:repeat(2,minmax(0,1fr));}
 .card {padding:12px;}.card-value {font-size:23px;}
}
@media(max-width:380px) {.cards {grid-template-columns:1fr;}}

/* FinSight interface polish */
.block-container {max-width:1360px;padding:3.5rem 1.8rem 2rem;}
[data-testid="stVerticalBlock"] {gap:.8rem;}
.brandbar {padding:8px 0 18px;margin-bottom:12px;}
.brand {font-size:23px;letter-spacing:-.8px;}
.status {background:#132923;color:#81ddc6;border:1px solid #254a40;
 padding:6px 10px;border-radius:6px;font-size:10px;}
.company {padding:16px 18px;background:#111b29;border:1px solid #263449;
 border-radius:12px;margin:6px 0;}
.company-name {font-size:clamp(20px,2vw,28px);line-height:1.3;}
.symbol {padding:12px;border-radius:8px;}
[data-testid="stWidgetLabel"] p {font-size:13px;font-weight:500;}
[data-testid="stCaptionContainer"] p {font-size:12px;line-height:1.6;color:#9aabc1;}
[data-baseweb="select"] > div,
[data-baseweb="input"], [data-baseweb="textarea"] {
 background:#141e2c;border-radius:8px;border-color:#304158;}
[data-baseweb="select"] > div:focus-within,
[data-baseweb="input"]:focus-within,
[data-baseweb="textarea"]:focus-within {border-color:#51d3b4;}
[data-testid="stButton"] button,
[data-testid="stDownloadButton"] button,
[data-testid="stLinkButton"] a {
 min-height:38px;border-radius:8px;border:1px solid #34465d;
 background:#172335;color:#e8edf5;padding:7px 14px;}
[data-testid="stButton"] button p,
[data-testid="stDownloadButton"] button p,
[data-testid="stLinkButton"] a p {font-size:13px;}
[data-testid="stButton"] button:hover:not(:disabled),
[data-testid="stDownloadButton"] button:hover:not(:disabled),
[data-testid="stLinkButton"] a:hover {
 border-color:#51d3b4;background:#1c3534;color:#8fe8d1;}
button:focus-visible,a:focus-visible {outline:2px solid #51d3b4;outline-offset:3px;}
button:disabled {opacity:.45;}
[data-baseweb="tab-list"] {
 gap:6px;background:#111b29;padding:5px;border-radius:10px;
 border:1px solid #263449;overflow-x:auto;}
[data-baseweb="tab"] {
 height:39px;padding:0 15px;border-radius:7px;white-space:nowrap;}
[data-baseweb="tab"] p {font-size:13px;}
[data-baseweb="tab"][aria-selected="true"] {background:#1b3733;color:#8fe8d1;}
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] {display:none;}
[data-testid="stExpander"] details {border:1px solid #29394e;border-radius:12px;}
[data-testid="stExpander"] summary {background:#111b29;border-radius:11px;padding:12px 16px;}
[data-testid="stExpander"] summary:hover {background:#172335;}
[data-testid="stMetric"], .card {
 background:linear-gradient(135deg,#172333,#111b29);
 border:1px solid #2b3c52;border-radius:12px;padding:18px;min-width:0;}
[data-testid="stMetricLabel"] p,.card-label {font-size:12px;color:#a6b7cc;}
[data-testid="stMetricValue"] {font-size:clamp(22px,2.3vw,32px);font-weight:650;}
[data-testid="stMetricValue"] > div {white-space:normal;overflow-wrap:anywhere;}
.card-value {font-size:clamp(24px,2.3vw,32px);line-height:1.6;}
.cards {gap:14px;margin:16px 0;}
.insight {border:1px solid #263449;border-left:3px solid #51d3b4;
 border-radius:9px;padding:16px;}
[data-testid="stDataFrame"], [data-testid="stDataEditor"] {
 border:1px solid #29394e;border-radius:9px;}
[data-testid="stFileUploaderDropzone"] {
 background:#111b29;border:1px dashed #416078;border-radius:12px;}
[data-testid="stAlert"] {border-radius:10px;}
h2 {font-size:1.4rem !important;letter-spacing:-.4px;}
h3 {font-size:1.08rem !important;letter-spacing:-.2px;}
.foot {margin-top:20px;line-height:1.7;}
@media(max-width:700px) {
 .block-container {padding:3.3rem 1rem 1.5rem;}
 .company {padding:12px;gap:10px;}
 .cards {grid-template-columns:repeat(2,minmax(0,1fr));}
 .card,[data-testid="stMetric"] {padding:12px;}
 [data-baseweb="tab"] {padding:0 10px;}
}
@media(max-width:380px) {.cards {grid-template-columns:1fr;}}


/* FinSight typography refresh: screen sizes in px, print sizes in pt. */
[data-testid="stMarkdownContainer"] p {font-size:16px;line-height:1.65;}
[data-testid="stCaptionContainer"] p {font-size:13px;line-height:1.55;}
h2 {font-size:22px!important;line-height:1.3!important;}
h3 {font-size:18px!important;line-height:1.35!important;}
.card-label,[data-testid="stMetricLabel"] p {font-size:13px!important;}
.card-value,[data-testid="stMetricValue"] {font-size:30px!important;font-variant-numeric:tabular-nums;}
.insight {font-size:14px;line-height:1.6;}
.katex-display {margin:1rem 0;overflow-x:auto;overflow-y:hidden;padding:6px 0;}
.katex-display > .katex {font-size:1.05em;}
</style>''', unsafe_allow_html=True)

st.markdown('<div class="brandbar"><div class="brand">FinSight <b>AI</b></div>'
            '<div class="status">PSX RESEARCH</div></div>', unsafe_allow_html=True)

def _build_base_analyst_report(data):
    """Build source-linked analysis from reviewed financial figures."""
    import math

    years = sorted(data["figures"], key=int)
    if len(years) < 2:
        raise ValueError("At least two annual periods are required.")

    prior, current = years[-2:]
    if int(current) - int(prior) != 1:
        raise ValueError("Two consecutive annual periods are required.")

    if (
        data.get("default_unit") != "PKR thousands"
        or data.get("unit_overrides", {}).get("eps") != "PKR per share"
    ):
        raise ValueError("Review the dataset units.")

    definitions = data.get("definitions", {})
    if (
        definitions.get("assets") != "Current assets"
        or definitions.get("liabilities") != "Current liabilities"
    ):
        raise ValueError("Current assets/liabilities must be identified.")

    a = data["figures"][prior]
    b = data["figures"][current]
    pages = data["pdf_pages"]

    required = [
        "sales", "gross", "profit", "assets",
        "liabilities", "cash", "eps",
    ]

    def valid_number(value):
        return (
            not isinstance(value, bool)
            and isinstance(value, (int, float))
            and math.isfinite(value)
        )

    for year, values in [(prior, a), (current, b)]:
        for key in required:
            if not valid_number(values.get(key)):
                raise ValueError(f"Invalid {key} for {year}.")
        if values["sales"] <= 0 or values["liabilities"] <= 0:
            raise ValueError(
                "Revenue and current liabilities must be positive."
            )

    def cite(*keys):
        references = sorted({int(pages[key]) for key in keys})
        return "[PDF pages " + ", ".join(map(str, references)) + "]"

    def bn(value):
        return f"PKR {value / 1_000_000:,.2f} billion"

    def growth(key):
        if a[key] <= 0:
            return "percentage growth is not reported for a non-positive base"
        change = (b[key] / a[key] - 1) * 100
        direction = "increase" if change >= 0 else "decrease"
        return f"{abs(change):.2f}% {direction}"

    labels = [
        ("Net sales", "sales"),
        ("Gross profit", "gross"),
        ("Net profit", "profit"),
        ("Current assets", "assets"),
        ("Current liabilities", "liabilities"),
        ("Net operating cash flow", "cash"),
        ("Basic EPS", "eps"),
    ]

    rows = [
        [
            label,
            f"{a[key]:,.2f}",
            f"{b[key]:,.2f}",
            "PKR/share" if key == "eps" else "PKR thousands",
            str(pages[key]),
        ]
        for label, key in labels
    ]

    gm_a = a["gross"] / a["sales"] * 100
    gm_b = b["gross"] / b["sales"] * 100
    nm_a = a["profit"] / a["sales"] * 100
    nm_b = b["profit"] / b["sales"] * 100
    cr_a = a["assets"] / a["liabilities"]
    cr_b = b["assets"] / b["liabilities"]
    wc_a = a["assets"] - a["liabilities"]
    wc_b = b["assets"] - b["liabilities"]

    cost_a = a["sales"] - a["gross"]
    cost_b = b["sales"] - b["gross"]

    revenue_effect = (
        (b["sales"] - a["sales"]) * a["gross"] / a["sales"]
    )
    margin_effect = (
        b["sales"]
        * (b["gross"] / b["sales"] - a["gross"] / a["sales"])
    )

    sections = [
        ("Executive assessment", [
            f"In {current}, revenue recorded a {growth('sales')} "
            f"and net profit recorded a {growth('profit')}. "
            f"{cite('sales', 'profit')}",

            f"Gross margin changed by {gm_b - gm_a:+.2f} percentage "
            f"points; net margin changed by "
            f"{nm_b - nm_a:+.2f} percentage points. "
            f"{cite('sales', 'gross', 'profit')}",

            f"Operating cash flow was {bn(b['cash'])}, compared with "
            f"net profit of {bn(b['profit'])}. Current assets covered "
            f"current liabilities {cr_b:.2f} times. "
            f"{cite('cash', 'profit', 'assets', 'liabilities')}",
        ]),

        ("Revenue, profit and shareholder earnings", [
            f"Revenue moved from {bn(a['sales'])} "
            f"in {prior} to {bn(b['sales'])} in {current}: "
            f"{growth('sales')}. Absolute change: "
            f"{bn(b['sales'] - a['sales'])}. {cite('sales')}",

            f"Net profit moved from {bn(a['profit'])} to "
            f"{bn(b['profit'])}: {growth('profit')}. "
            f"{cite('profit')}",

            f"Basic EPS was PKR {b['eps']:.2f} per share "
            f"versus PKR {a['eps']:.2f}: {growth('eps')}. "
            f"EPS and total profit can grow at different rates because "
            f"of share-count changes and profit attribution; these "
            f"causes are not established by the supplied fields. "
            f"{cite('eps', 'profit')}",
        ]),

        ("Profitability and cost efficiency", [
            f"Gross margin was {gm_b:.2f}% versus {gm_a:.2f}%. "
            f"For every PKR 100 of sales, gross profit was "
            f"PKR {gm_b:.2f}, compared with PKR {gm_a:.2f}. "
            f"{cite('gross', 'sales')}",

            f"Cost of sales, calculated as revenue less gross profit, "
            f"was {bn(cost_b)} versus {bn(cost_a)}. Its share of "
            f"revenue changed from {100 - gm_a:.2f}% to "
            f"{100 - gm_b:.2f}%. {cite('sales', 'gross')}",

            f"Net margin was {nm_b:.2f}% versus {nm_a:.2f}%. "
            f"This represents a {nm_b - nm_a:+.2f} percentage-point "
            f"change after all items included in reported net profit. "
            f"{cite('profit', 'sales')}",
        ]),

        ("What changed in gross profit", [
            f"Gross profit changed by {bn(b['gross'] - a['gross'])}. "
            f"An arithmetic breakdown attributes "
            f"{bn(revenue_effect)} to the revenue change at the prior "
            f"gross margin, and {bn(margin_effect)} to the margin "
            f"change applied to current revenue. "
            f"{cite('sales', 'gross')}",

            "This breakdown explains the numerical relationship. "
            "It does not establish whether pricing, volumes, exchange "
            "rates, costs or business mix caused the change.",
        ]),

        ("Liquidity and working capital", [
            f"Current assets were {bn(b['assets'])}; current "
            f"liabilities were {bn(b['liabilities'])}. "
            f"The current ratio was {cr_b:.2f}x versus {cr_a:.2f}x. "
            f"{cite('assets', 'liabilities')}",

            f"Net working capital was {bn(wc_b)}, compared with "
            f"{bn(wc_a)}. Change: {bn(wc_b - wc_a)}. "
            f"{cite('assets', 'liabilities')}",

            (
                "Current liabilities exceed current assets. Review "
                "payment timing, financing facilities and asset "
                "collectability; this alone does not establish default."
                if cr_b < 1
                else
                "Current assets exceed or equal current liabilities. "
                "This provides accounting coverage, but receivables "
                "and other current assets are not necessarily "
                "immediately available cash."
            ),
        ]),

        ("Cash flow performance", [
            f"Net operating cash flow was {bn(b['cash'])} versus "
            f"{bn(a['cash'])}, an absolute change of "
            f"{bn(b['cash'] - a['cash'])}. {cite('cash')}",

            f"Operating cash-flow margin was "
            f"{b['cash'] / b['sales'] * 100:.2f}% versus "
            f"{a['cash'] / a['sales'] * 100:.2f}%. "
            f"This compares operating cash generation with revenue. "
            f"{cite('cash', 'sales')}",
        ]),
    ]

    quality = []
    for year, values in [(prior, a), (current, b)]:
        if values["profit"] > 0:
            conversion = values["cash"] / values["profit"]
            quality.append(
                f"{year}: operating cash flow / net profit was "
                f"{conversion:.2f}x. {cite('cash', 'profit')}"
            )
        else:
            quality.append(
                f"{year}: cash conversion ratio is not reported "
                f"because net profit was non-positive. "
                f"{cite('profit')}"
            )

    quality.extend([
        f"In {current}, operating cash flow minus net profit was "
        f"{bn(b['cash'] - b['profit'])}. "
        f"{cite('cash', 'profit')}",

        "Cash conversion above or below 1.00x is a review signal, "
        "not a standalone verdict on earnings quality. Working "
        "capital, tax payments, non-cash items and cash-flow "
        "classification can affect the comparison.",
    ])
    sections.append(("Cash conversion and earnings quality", quality))

    investment_keys = ("ppe_cash", "intangibles_cash")
    investment_labels = {
        "ppe_cash": "Cash purchases of PPE",
        "intangibles_cash": "Cash purchases/development of intangibles",
    }
    available = []

    for key in investment_keys:
        if (
            valid_number(a.get(key))
            and valid_number(b.get(key))
            and key in pages
        ):
            available.append(key)
            rows.append([
                investment_labels[key],
                f"{a[key]:,.2f}",
                f"{b[key]:,.2f}",
                "PKR thousands",
                str(pages[key]),
            ])

    investment = [
        f"{investment_labels[key]}: {bn(abs(b[key]))} in {current}, "
        f"versus {bn(abs(a[key]))} in {prior}, expressed as "
        f"cash-spending magnitudes. {cite(key)}"
        for key in available
    ]

    if len(available) == 2:
        spending_a = sum(abs(a[key]) for key in investment_keys)
        spending_b = sum(abs(b[key]) for key in investment_keys)
        fcf_a = a["cash"] - spending_a
        fcf_b = b["cash"] - spending_b

        investment.extend([
            f"Free cash flow proxy was {bn(fcf_b)} versus "
            f"{bn(fcf_a)}. Calculation: operating cash flow less "
            f"cash purchases of PPE and intangibles. "
            f"{cite('cash', *investment_keys)}",

            "This proxy excludes acquisitions, purchases of financial "
            "investments and asset-sale proceeds. It is not free cash "
            "flow to equity or a valuation forecast. The two spending "
            "rows must be separate, non-overlapping amounts.",
        ])
    else:
        investment.append(
            "Free cash flow is not calculated because the saved "
            "dataset does not establish both PPE and intangible "
            "cash purchases. This does not mean those amounts are "
            "absent from the original annual report. Missing amounts "
            "must not be treated as zero."
        )

    sections.append((
        "Investment spending and free cash flow",
        investment,
    ))

    sections.extend([
        ("Business explanations and research priorities", [
            "To explain revenue and margin movements, inspect "
            "management discussion and segment results for pricing, "
            "volume, business mix and currency effects. These causes "
            "have not been extracted into this report.",

            "For liquidity, examine receivable ageing, contract assets, "
            "cash availability and debt maturities. For cash conversion, "
            "inspect the working-capital and tax reconciliation.",

            "Review customer concentration, commitments, related-party "
            "transactions and the auditor opinion before forming an "
            "investment view.",
        ]),

        ("Valuation coverage", [
            "This report does not yet combine a dated market price, "
            "share count, debt breakdown, peer multiples and forecast "
            "assumptions. Target prices and buy/sell ratings are "
            "therefore not produced.",
        ]),

        ("Method and source", [
            f"Source: {data['source']}. "
            f"Scope: {data['scope']}. "
            f"Extraction: "
            f"{data.get('extraction_method', 'not specified')}. "
            "Calculations use the saved reviewed dataset; the report "
            "generator does not independently verify the original PDF.",

            "Growth = (current / prior - 1) x 100, only for a positive "
            "prior value. Margin = corresponding profit / revenue "
            "x 100. Current ratio = current assets / current "
            "liabilities. Working capital = current assets minus "
            "current liabilities. Cash conversion = operating cash "
            "flow / net profit, only for positive net profit.",

            "Monetary table figures are normalized to PKR thousands; "
            "EPS remains PKR per share. PKR billions = PKR thousands "
            "/ 1,000,000. Calculations use unrounded inputs.",

            "This is calculated historical financial analysis, not "
            "an investment recommendation. PDF references identify "
            "pages in the source file.",
        ]),
    ])
    evidence = data.get("business_evidence", [])

    if evidence:
        paragraphs = [
            "Automatically selected keyword matches from the uploaded "
            "report. These are source excerpts, not verified explanations "
            "of the financial changes. Check the original page for "
            "context, reporting period and company scope."
        ]

        for item in evidence:
            paragraphs.append(
                f"{item['topic']} — Source excerpt: "
                f"\"{item['text']}\" [PDF page {item['page']}]"
            )

        sections.insert(
            -2,
            ("Business commentary — source excerpts", paragraphs),
        )
    return {
        "title": f"{data['company']} ({data['symbol']})",
        "subtitle": (
            f"{current} vs {prior} | "
            f"{data['scope'].title()} annual results"
        ),
        "prior": prior,
        "current": current,
        "rows": rows,
        "sections": sections,
    }

# Additional figures remain optional and use the existing review/unit workflow.
EXTRA_METRICS = {
    'operating_profit': ('Operating profit', r'^operating profit\s+', 'income'),
    'other_income': ('Other income', r'^other income\s+', 'income'),
    'finance_cost': ('Finance costs', r'^finance costs?\s+', 'income'),
    'pbt': ('Profit before taxation (after levy)', r'^profit before taxation\s+', 'income'),
    'tax': ('Taxation', r'^taxation\s+', 'income'),
    'selling': ('Selling and distribution expenses', r'^(?:selling and distribution|distribution) expenses\s+', 'income'),
    'admin': ('Administrative expenses', r'^administrative expenses\s+', 'income'),
    'total_assets': ('Total assets', r'^total assets\s+', 'balance'),
    'total_equity': ('Total equity', r'^total equity\s+', 'balance'),
    'total_liabilities': ('Total liabilities', r'^total liabilities\s+', 'balance'),
    'receivables': ('Trade debts / receivables', r'^(?:trade debts|trade receivables)(?:\s*[-–]\s*net)?\s+', 'balance'),
    'inventory': ('Stock-in-trade / inventories', r'^(?:stock-in-trade|inventories)\s+', 'balance'),
    'cash_balance': ('Cash and bank balances', r'^cash and bank balances\s+', 'balance'),
    'finance_paid': ('Finance costs paid', r'^finance costs? paid\s+', 'cash'),
    'tax_paid': ('Taxes and levy paid', r'^(?:taxes and levy paid|taxes paid|income tax paid)\s+', 'cash'),
    'acquisitions': ('Cash acquisition of subsidiaries', r'^acquisition of subsidiar(?:y|ies)\s+', 'cash'),
    'dividends_paid': ('Dividends paid', r'^dividends? paid\s+', 'cash'),
}

RESEARCH_TOPICS = {
    'Revenue and business drivers': ['revenue growth', 'growth in revenue', 'growth', 'geographical', 'geographic', 'segment revenue', 'organic growth', 'acquisitions', 'currency depreciation'],
    'Margins and operating costs': ['gross margin', 'gross margins', 'operating margins', 'net margin', 'profitability', 'staff costs', 'salary', 'cost of revenue', 'administrative expenses', 'finance costs'],
    'Cash flow and working capital': ['working capital', 'trade debts', 'trade receivables', 'contract assets', 'collections', 'cash generated from operations', 'taxes paid'],
    'Debt and liquidity': ['borrowings', 'debt maturity', 'liquidity risk', 'covenants', 'lease liabilities', 'credit facilities'],
    'Investment and acquisitions': ['acquisition', 'goodwill', 'purchase consideration', 'capital expenditure', 'intangibles', 'software development'],
    'Risks and concentration': ['credit risk', 'currency risk', 'customer concentration', 'major customer', 'sensitivity analysis', 'contingencies'],
    'Audit and governance': ['key audit matter', 'qualified opinion', 'basis for opinion', 'related party', 'related parties', 'internal control'],
    'Strategy and outlook': ['future outlook', 'prospects', 'strategy', 'expansion', 'inorganic growth', 'outlook'],
}


def collect_research_evidence(sections):
    """Retrieve bounded passages, carrying local scope and rejecting company-only notes."""
    import re, hashlib
    items = []
    scope = 'unverified'
    for section in sorted(sections, key=lambda x: (int(x['page']), {'full':0,'left':0,'right':1}.get(x.get('side'),0))):
        text = section.get('text', '')
        header = text[:400]
        if re.match(r'\s*unconsolidated (?:statement|financial)', header, re.I):
            scope = 'company-only'
        elif re.match(r'\s*consolidated (?:statement|financial)', header, re.I):
            scope = 'group'
        if re.search(r'\b(?:unconsolidated financial statements|unconsolidated statement)\b', text, re.I):
            local_scope = 'company-only'
        elif re.search(r'\b(?:consolidated financial statements|consolidated statement)\b', text, re.I):
            local_scope = 'group'
        else:
            local_scope = scope
        if local_scope == 'company-only':
            continue
        if re.search(r'(?:summari[sz]ed financial|financial statements of the associated company)', text, re.I):
            continue
        management = bool(re.search(r"(?:CEO|Chairman|Directors?).{0,12}(?:Message|Report)|Future Outlook|North America.*Europe|Principal Risk", header, re.I))
        policy = bool(re.search(r'accounting polic|recognised|recognized|initially measured|subsequently measured', text, re.I))
        lines = [x.strip() for x in text.splitlines() if x.strip()]
        for start in range(0, len(lines), 10):
            passage = '\n'.join(lines[start:start+20])
            if len(passage) < 140 or '(cid:' in passage:
                continue
            # Do not mix associate/subsidiary summaries with group financial drivers.
            if re.search(r'(?:summari[sz]ed financial.*associat|financial statements of the associated)', passage, re.I):
                continue
            passage = passage[:1400]
            items.append({'id': hashlib.sha256(f"{section['page']}:{section.get('side','full')}:{passage}".encode()).hexdigest()[:16],
                          'page': int(section['page']), 'side': section.get('side','full'),
                          'scope': local_scope, 'management': management, 'policy': policy, 'text': passage})
    output = {}
    for topic, terms in RESEARCH_TOPICS.items():
        ranked = []
        for item in items:
            lower = item['text'].lower()
            matches = sum(term in lower for term in terms)
            if not matches:
                continue
            if topic == 'Cash flow and working capital' and re.search(r'currency risk|future cash flows.*fluctuate|accounting polic',lower):
                continue
            if topic == 'Margins and operating costs' and not re.search(r'margin|profitability',lower):
                continue
            if topic in ('Revenue and business drivers','Margins and operating costs') and re.search(r'future outlook|will continue|we will|expected to',lower):
                continue
            if topic == 'Audit and governance' and re.search(r'communicate with those charged|responsibilities of the auditor',lower):
                continue
            causal = bool(re.search(r'\b(?:due to|driven by|because|attributable to|resulted from)\b', lower))
            prose = sum(c.isdigit() for c in lower) / max(1,len(lower)) < .15
            score = matches + int(causal)*2 + int(prose) - 4*int(item['policy'])
            if topic in ('Revenue and business drivers','Margins and operating costs','Strategy and outlook'):
                score += 6*int(item['management']) - 6*int(item['policy'])
            if score > 0:
                ranked.append((score, item))
        ranked.sort(key=lambda pair: (-pair[0], pair[1]['page']))
        chosen, pages = [], set()
        for _, item in ranked:
            if item['page'] in pages:
                continue
            chosen.append(item); pages.add(item['page'])
            if len(chosen) == 3:
                break
        output[topic] = chosen
    return output


def extended_analysis_sections(data):
    """Deterministic analytics; no unknown figure is imputed as zero."""
    import math
    prior, current = sorted(data['figures'], key=int)[-2:]
    a, b = data['figures'][prior], data['figures'][current]
    pages = data['pdf_pages']
    result = []
    def have(*keys):
        return all(k in pages and all(isinstance(v.get(k),(int,float)) and not isinstance(v.get(k),bool) and math.isfinite(v[k]) for v in (a,b)) for k in keys)
    def ref(*keys):
        return '[PDF pages '+', '.join(str(p) for p in sorted({int(pages[k]) for k in keys}))+']'
    def bn(x):
        return f'PKR {x/1e6:,.2f} billion'
    costs=[]
    if have('operating_profit','sales'):
        ma,mb=100*a['operating_profit']/a['sales'],100*b['operating_profit']/b['sales']
        costs += [f'Finding: Operating margin was {mb:.2f}% versus {ma:.2f}%; change {mb-ma:+.2f} percentage points. '+ref('operating_profit','sales'),
                  'Interpretation: This isolates the reported operating result from subsequent financing, tax and other below-operating items. A business cause requires the related expense or management disclosures.']
    for k in ('selling','admin','finance_cost'):
        if have(k,'sales'):
            costs.append(f'{EXTRA_METRICS[k][0]}: {bn(abs(b[k]))} versus {bn(abs(a[k]))}; share of revenue {100*abs(b[k])/b["sales"]:.2f}% versus {100*abs(a[k])/a["sales"]:.2f}%. '+ref(k,'sales'))
    if have('operating_profit','finance_cost') and abs(b['finance_cost'])>0:
        costs.append(f'Operating profit / finance-cost magnitude: {b["operating_profit"]/abs(b["finance_cost"]):.2f}x. This is an accounting coverage proxy, not a covenant or debt-service coverage calculation. '+ref('operating_profit','finance_cost'))
    if have('other_income','profit') and b['profit']>0:
        costs.append(f'Other income was {bn(b["other_income"])} ({100*b["other_income"]/b["profit"]:.2f}% of net profit). This compares a pre-tax line with after-tax profit; it is not an after-tax contribution or proof that income is non-recurring. Review its components. '+ref('other_income','profit'))
    if have('tax','pbt') and b['pbt']>0 and a['pbt']>0:
        costs.append(f'Tax expense magnitude / profit before taxation: {100*abs(b["tax"])/b["pbt"]:.2f}% versus {100*abs(a["tax"])/a["pbt"]:.2f}%. Review tax credits, deferred tax and any separately presented levy. '+ref('tax','pbt'))
    result.append(('Operating performance and earnings composition',costs or ['Additional reviewed operating-profit and expense rows are unavailable.']))
    liquidity=[]
    if have('cash_balance','liabilities'):
        liquidity.append(f'Cash and bank balances / current liabilities: {b["cash_balance"]/b["liabilities"]:.2f}x versus {a["cash_balance"]/a["liabilities"]:.2f}x. Restricted cash and investments are not assessed by this proxy. '+ref('cash_balance','liabilities'))
    if have('inventory','assets','liabilities'):
        liquidity.append(f'Inventory-excluded current-asset coverage: {(b["assets"]-b["inventory"])/b["liabilities"]:.2f}x. Prepayments and other less-liquid balances may remain, so this is not a fully adjusted quick ratio. '+ref('inventory','assets','liabilities'))
    if have('receivables','sales'):
        days=(a['receivables']+b['receivables'])/2/b['sales']*365
        liquidity.append(f'Average trade receivables / annual revenue x 365: {days:.1f} days for {current}. Revenue is used as a proxy for credit sales; this is not actual collection time. Compare ageing, impairment and contract assets before drawing a conclusion. '+ref('receivables','sales'))
    if have('total_liabilities','total_assets') and b['total_assets']>0:
        liquidity.append(f'Total liabilities / total assets: {100*b["total_liabilities"]/b["total_assets"]:.2f}%. Total liabilities include operating balances and must not be called interest-bearing debt. '+ref('total_liabilities','total_assets'))
    result.append(('Balance-sheet resilience and collection exposure',liquidity or ['Cash composition, receivables and total balance-sheet fields were not reliably mapped. Review the retrieved notes below.']))
    returns=[]
    for key,name in [('total_assets','Return on average total assets'),('total_equity','Return on average total equity')]:
        if have(key,'profit') and a[key]>0 and b[key]>0:
            returns.append(f'{name} ({current}): {100*b["profit"]/((a[key]+b[key])/2):.2f}%. Uses total group profit and the simple average of opening/closing group balances. This is not parent-shareholder ROE. '+ref(key,'profit'))
    result.append(('Returns on assets and equity',returns or ['ROA/ROE require reviewed opening and closing total assets/equity. Missing values are not estimated.']))
    allocation=[]
    if have('cash','ppe_cash','intangibles_cash','acquisitions'):
        residual=b['cash']-abs(b['ppe_cash'])-abs(b['intangibles_cash'])-abs(b['acquisitions'])
        allocation.append(f'Operating cash remaining after PPE, intangible purchases and subsidiary acquisitions: {bn(residual)}. Acquisition cash outflow: {bn(abs(b["acquisitions"]))}. This residual excludes other investing/financing movements and is not a valuation cash-flow forecast. '+ref('cash','ppe_cash','intangibles_cash','acquisitions'))
    if have('dividends_paid','cash'):
        allocation.append(f'Cash dividends paid: {bn(abs(b["dividends_paid"]))}; operating cash flow: {bn(b["cash"])}. Payment timing may relate to prior-year declarations. '+ref('dividends_paid','cash'))
    result.append(('Capital allocation and cash commitments',allocation or ['Acquisition/dividend cash payments are not available as reviewed rows.']))
    return result


def add_research_to_report(report, data):
    # Replace keyword-only commentary; keep the existing core calculations.
    report['sections']=[s for s in report['sections'] if s[0] not in ('Business commentary — source excerpts','Business explanations and research priorities')]
    insert_at = next((i for i,s in enumerate(report['sections']) if s[0]=='Valuation coverage'),len(report['sections']))
    prior,current=report['prior'],report['current']
    for key,(label,_,_) in EXTRA_METRICS.items():
        if key in data['figures'][prior] and key in data['figures'][current] and key in data['pdf_pages']:
            report['rows'].append([label, f"{data['figures'][prior][key]:,.2f}", f"{data['figures'][current][key]:,.2f}", 'PKR thousands', str(data['pdf_pages'][key])])
    additions=extended_analysis_sections(data)
    evidence=data.get('research_evidence',{})
    narratives=data.get('research_narratives',{})
    for topic in RESEARCH_TOPICS:
        paragraphs=[]
        draft=narratives.get(topic)
        if draft and draft.get('status')=='supported' and draft.get('engine_version')==4:
            paragraphs += ['AI explanation (draft, not independently verified): '+draft['explanation'],
                           'Source evidence: "'+draft['quote']+'" [PDF page '+str(draft['page'])+']; scope: '+draft['scope']+'.',
                           'AI interpretation: '+draft['implication'], 'Uncertainty / review point: '+draft['uncertainty']]
        else:
            continue
        additions.append((topic+' — reasons and evidence',paragraphs))
    additions.append(('Coverage and research limitations',[
        'Coverage is driven by available reviewed figures and retrieved report passages. It is not a complete audit or a full investment valuation. Multi-year trends, segment contribution, net debt and peer valuation require additional structured inputs.',
        'AI passages are saved as drafts. Exact-quote and source checks do not independently establish that an explanation follows from the evidence. Management outlook is not a forecast verified by FinSight.',
        'Ratio interpretation here is intended for non-financial businesses. Bank/insurance capital, liquidity and solvency analysis requires a separate sector model.'
    ]))
    report['sections'][insert_at:insert_at]=additions
    return report


def render_research_builder(dataset):
    """One requested topic at a time; reuse saved results and show elapsed time."""
    import hashlib, time, os
    from concurrent.futures import ThreadPoolExecutor
    from datetime import datetime, timezone
    from src.ai_answer import generate_research_note
    st.subheader('Reasons and supporting evidence')
    evidence=dataset.get('research_evidence',{})
    if not evidence:
        st.info('Read the source PDF and save extracted figures to enable research.')
        return dataset
    topic=st.selectbox('Explanation topic',list(RESEARCH_TOPICS),key='research_topic_'+dataset['symbol'])
    items=evidence.get(topic,[])[:2]
    with st.expander('Read evidence before generating'):
        for item in items:
            st.caption(f"PDF page {item['page']} · {item.get('scope','unverified')}")
            st.text(item['text'])
    fingerprint=hashlib.sha256(json.dumps([dataset.get('source_sha256'),dataset['figures'],topic,items,4],sort_keys=True).encode()).hexdigest()
    state_key='research_v4_'+fingerprint
    saved=dataset.get('research_narratives',{}).get(topic,{})
    if saved.get('fingerprint')==fingerprint and state_key not in st.session_state:
        st.session_state[state_key]=saved
    draft=st.session_state.get(state_key)
    regenerate=st.checkbox('Regenerate this topic',key='redo_'+fingerprint) if draft else False
    st.caption('One topic per request. Saved answers are reused. Elapsed time is measured, not an estimated completion time.')
    if st.button('Generate selected topic',key='generate_'+fingerprint,disabled=not items or bool(draft and not regenerate)):
        status=st.empty(); started=time.monotonic()
        pool=ThreadPoolExecutor(max_workers=1)
        future=pool.submit(generate_research_note,topic,items,dataset['company'],max(dataset['figures'],key=int),'')
        try:
            while not future.done():
                elapsed=int(time.monotonic()-started)
                status.info(f'{topic} · {elapsed//60:02d}:{elapsed%60:02d} elapsed · local model running')
                time.sleep(.5)
            draft=future.result()
            draft.update(fingerprint=fingerprint,engine_version=4,elapsed_seconds=round(time.monotonic()-started,1))
            st.session_state[state_key]=draft
        except RuntimeError as exc:
            st.error(str(exc)); draft=None
        finally:
            pool.shutdown(wait=False);status.empty()
    if draft:
        if draft.get('status')=='supported':
            st.write(draft['explanation'])
            st.caption(f"PDF page {draft['page']} · {draft['scope']} · {draft.get('elapsed_seconds',0)} seconds")
            st.write('Interpretation: '+draft['implication'])
            st.write('Review point: '+draft['uncertainty'])
            st.caption('Source matching checks the quotation, not the accuracy of the AI interpretation.')
            if st.button('Save this explanation to report',key='save_'+fingerprint):
                notes=dict(dataset.get('research_narratives',{}));notes[topic]=draft
                updated=dict(dataset,research_narratives=notes,research_generated_at=datetime.now(timezone.utc).isoformat())
                path=ROOT/'data'/'processed'/f"{dataset['symbol']}_{max(dataset['figures'],key=int)}_reviewed_financials.json"
                try:
                    temporary=path.with_suffix('.tmp')
                    temporary.write_text(json.dumps(updated,indent=2,allow_nan=False),encoding='utf-8')
                    os.replace(temporary,path);dataset=updated
                    st.success('Selected explanation saved; other topics preserved.')
                except (OSError,ValueError) as exc:
                    st.error(f'Could not save: {exc}')
        else:
            st.info('These passages do not establish a supported explanation. Calculated analysis remains available.')
    return dataset



def build_analyst_report(data):
    report = add_research_to_report(_build_base_analyst_report(data), data)
    report['calculation_data'] = data
    return report


def report_formula_specs():
    """Label, numerator, denominator, suffix, and matching dashboard LaTeX."""
    return [
        ('Year-on-year growth', 'Current value - Prior value', 'Prior value', 'x 100%', r'\mathrm{Growth}\;(\%)=\frac{\mathrm{Current}-\mathrm{Prior}}{\mathrm{Prior}}\times100'),
        ('Gross margin', 'Gross profit', 'Revenue', 'x 100%', r'\mathrm{Gross\ margin}\;(\%)=\frac{\mathrm{Gross\ profit}}{\mathrm{Revenue}}\times100'),
        ('Current ratio', 'Current assets', 'Current liabilities', '', r'\mathrm{Current\ ratio}=\frac{\mathrm{Current\ assets}}{\mathrm{Current\ liabilities}}'),
        ('Cash conversion', 'Net operating cash flow', 'Net profit', '', r'\mathrm{Cash\ conversion}=\frac{\mathrm{Net\ operating\ cash\ flow}}{\mathrm{Net\ profit}}'),
        ('Operating cash-flow margin', 'Net operating cash flow', 'Revenue', 'x 100%', r'\mathrm{OCF\ margin}\;(\%)=\frac{\mathrm{Net\ operating\ cash\ flow}}{\mathrm{Revenue}}\times100'),
        ('Return on average assets', 'Net profit', '(Opening assets + Closing assets) / 2', 'x 100%', r'\mathrm{ROA}\;(\%)=\frac{\mathrm{Net\ profit}}{(\mathrm{Opening\ assets}+\mathrm{Closing\ assets})/2}\times100'),
        ('Net working capital', 'Current assets - Current liabilities', '', '', r'\mathrm{Working\ capital}=\mathrm{Current\ assets}-\mathrm{Current\ liabilities}'),
        ('Free cash flow proxy', 'Operating cash flow - PPE spending - Intangible spending', '', '', r'\mathrm{FCF\ proxy}=\mathrm{OCF}-\mathrm{PPE\ spending}-\mathrm{Intangible\ spending}'),
        ('PKR thousands to billions', 'Amount in PKR thousands', '1,000,000', '', r'\mathrm{PKR\ billions}=\frac{\mathrm{PKR\ thousands}}{1{,}000{,}000}'),
        ('Net margin','Net profit','Revenue','x 100%',r'\mathrm{Net\ margin}=\frac{\mathrm{Net\ profit}}{\mathrm{Revenue}}\times100'),
        ('Operating margin','Operating profit','Revenue','x 100%',r'\mathrm{Operating\ margin}=\frac{\mathrm{Operating\ profit}}{\mathrm{Revenue}}\times100'),
    ]


def is_formula_prose(text):
    return text.startswith('Growth = ') or text.startswith('Monetary table figures are normalized')


def render_ratio_comparison(data):
    years=sorted(data['figures'],key=int)[-2:]
    if len(years)!=2:return
    prior,current=years
    rows=[]
    definitions=[('Gross margin','gross','sales',100,'%'),('Net margin','profit','sales',100,'%'),
                 ('Operating margin','operating_profit','sales',100,'%'),('Current ratio','assets','liabilities',1,'times'),
                 ('Cash conversion','cash','profit',1,'times'),('Operating cash-flow margin','cash','sales',100,'%')]
    for label,num,den,factor,unit in definitions:
        values=[]
        for year in years:
            f=data['figures'][year]
            values.append(f[num]/f[den]*factor if num in f and den in f and f[den]>0 else None)
        if any(v is None for v in values):continue
        pages=sorted({data['pdf_pages'][k] for k in (num,den)})
        rows.append({'Measure':label,prior:f'{values[0]:.2f}{unit}',current:f'{values[1]:.2f}{unit}',
                     'Change':f'{values[1]-values[0]:+.2f} '+('pp' if unit=='%' else 'times'),
                     'PDF pages':', '.join(map(str,pages))})
    st.subheader('Financial ratios at a glance')
    st.dataframe(pd.DataFrame(rows),hide_index=True,width='stretch')
    st.caption('pp = percentage points. Ratios use unrounded saved figures. A positive change is not automatically favourable.')


def section_formulas(heading, paragraph_index):
    # Place each method beside the finding it explains, in both renderers.
    placement = {
        ('Revenue, profit and shareholder earnings', 0): [0],
        ('Profitability and cost efficiency', 0): [1],
        ('Profitability and cost efficiency', 2): [9],
        ('Operating performance and earnings composition', 0): [10],
        ('Liquidity and working capital', 0): [2],
        ('Liquidity and working capital', 1): [6],
        ('Cash flow performance', 1): [4],
        ('Cash conversion and earnings quality', 0): [3],
        ('Investment spending and free cash flow', 2): [7],
        ('Returns on assets and equity', 0): [5],
    }
    return [report_formula_specs()[i] for i in placement.get((heading, paragraph_index), [])]


def worked_formula(spec, data):
    """Use saved, unrounded inputs; displayed monetary values are PKR billions."""
    if not data:return None
    years=sorted(data['figures'],key=int)
    if len(years)<2:return None
    prior,current=years[-2:];a,b=data['figures'][prior],data['figures'][current]
    label=spec[0]
    pairs={'Gross margin':('gross','sales',100,'%'),
           'Net margin':('profit','sales',100,'%'),
           'Operating margin':('operating_profit','sales',100,'%'),
           'Current ratio':('assets','liabilities',1,'times'),
           'Cash conversion':('cash','profit',1,'times'),
           'Operating cash-flow margin':('cash','sales',100,'%')}
    num=den=None;factor=1;unit='';result=None
    if label in pairs:
        n,d,factor,unit=pairs[label]
        if n not in b or d not in b or b[d]<=0:return None
        num=f'{b[n]/1e6:,.2f}';den=f'{b[d]/1e6:,.2f}'
        result=b[n]/b[d]*factor
    elif label=='Year-on-year growth':
        if a.get('sales',0)<=0 or 'sales' not in b:return None
        num=f'{b["sales"]/1e6:,.2f} - {a["sales"]/1e6:,.2f}'
        den=f'{a["sales"]/1e6:,.2f}';factor=100;unit='%'
        result=(b['sales']/a['sales']-1)*100
    elif label=='Return on average assets':
        if not all('total_assets' in f and 'profit' in f for f in (a,b)):return None
        avg=(a['total_assets']+b['total_assets'])/2
        if avg<=0:return None
        num=f'{b["profit"]/1e6:,.2f}'
        den=f'({a["total_assets"]/1e6:,.2f} + {b["total_assets"]/1e6:,.2f}) / 2'
        factor=100;unit='%';result=b['profit']/avg*100
    elif label=='Net working capital':
        if not all(k in b for k in ('assets','liabilities')):return None
        num=f'{b["assets"]/1e6:,.2f} - {b["liabilities"]/1e6:,.2f}'
        den='';result=(b['assets']-b['liabilities'])/1e6;unit='PKR billion'
    elif label=='Free cash flow proxy':
        if not all(k in b for k in ('cash','ppe_cash','intangibles_cash')):return None
        vals=[b['cash']/1e6,abs(b['ppe_cash'])/1e6,abs(b['intangibles_cash'])/1e6]
        num=' - '.join(f'{v:,.2f}' for v in vals);den=''
        result=vals[0]-vals[1]-vals[2];unit='PKR billion'
    if result is None:return None
    suffix=('× 100 ' if factor==100 else '')+f'~ {result:,.2f} {unit}'
    latex=(r'\frac{'+num+'}{'+den+'}' if den else num)
    latex+=(r'\times 100' if factor==100 else '')
    latex+=r'\approx '+f'{result:,.2f}'+(r'\%' if unit=='%' else r'\;\mathrm{'+unit.replace(' ',r'\ ')+'}')
    return (f'{current} calculation · inputs in PKR billion',num,den,suffix,latex)


def render_report_paragraphs(heading, paragraphs, data=None):
    import re

    if heading == "Method and source":
        with st.expander("Source and methodology"):
            for paragraph in paragraphs:
                if not is_formula_prose(paragraph):
                    st.caption(paragraph)

            st.caption(
                "Growth requires a positive prior value; cash conversion "
                "requires positive net profit. Spending uses positive "
                "cash-outflow magnitudes. EPS remains PKR per share."
            )
        return

    with st.container(border=True):
        for paragraph_index, paragraph in enumerate(paragraphs):
            refs = re.findall(r"\[PDF pages? [^\]]+\]", paragraph)
            body = re.sub(r"\s*\[PDF pages? [^\]]+\]", "", paragraph)

            if body.startswith(("Interpretation:", "AI interpretation:")):
                st.markdown("**Interpretation**")
                st.write(body.split(":", 1)[1].strip())

            elif body.startswith(
                ("Uncertainty / review point:", "Review point:")
            ):
                st.caption(body)

            elif body.startswith("Source evidence:"):
                with st.expander("Supporting source passage"):
                    st.write(body)

            else:
                st.write(body)

            for spec in section_formulas(heading, paragraph_index):
                st.latex(spec[4])
                worked=worked_formula(spec,data)
                if worked:
                    st.latex(worked[4])
                    st.caption('Monetary inputs shown in PKR billion. Displayed inputs are rounded; result uses unrounded saved values.')
            if refs:
                st.caption("Source: " + " · ".join(refs))



def volume_comparison(relative):
    """Explain daily relative volume without implying a trading signal."""
    import math
    if relative is None or not math.isfinite(relative) or relative < 0:
        return 'Not available', 'Needs 20 prior sessions'
    difference = (relative - 1) * 100
    comparison = ('At average' if abs(difference) < 0.05 else
                  f'{abs(difference):.1f}% {"above" if difference > 0 else "below"} average')
    return f'{relative:.2f} times average', comparison


def analyst_pdf(report):
    from io import BytesIO
    from xml.sax.saxutils import escape as xml_escape
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Flowable, KeepTogether
    from pathlib import Path
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    regular, bold = 'Helvetica', 'Helvetica-Bold'
    for regular_path, bold_path in [
        ('C:/Windows/Fonts/arial.ttf', 'C:/Windows/Fonts/arialbd.ttf'),
        ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),
    ]:
        if Path(regular_path).exists() and Path(bold_path).exists():
            pdfmetrics.registerFont(TTFont('FinSightText', regular_path))
            pdfmetrics.registerFont(TTFont('FinSightBold', bold_path))
            regular, bold = 'FinSightText', 'FinSightBold'
            break
    class FormulaBlock(Flowable):
        def __init__(self, label, numerator, denominator, suffix):
            Flowable.__init__(self)
            self.label, self.numerator, self.denominator, self.suffix = label, numerator, denominator, suffix
            self.height=56 if denominator else 42
        def wrap(self, availWidth, availHeight):
            self.width=availWidth
            return self.width,self.height
        def draw(self):
            from reportlab.pdfbase.pdfmetrics import stringWidth
            c=self.canv; w=self.width
            c.setFillColor(colors.HexColor('#12394b'));c.setFont(bold,10)
            c.drawCentredString(w/2,self.height-10,self.label)
            size=10.5
            def width(t):return stringWidth(t,regular,size)
            while size>7 and max(width(self.numerator),width(self.denominator))+width(self.suffix)+40>w:
                size-=.5
            c.setFont(regular,size)
            if self.denominator:
                fw=max(width(self.numerator),width(self.denominator))+16
                sw=width(self.suffix)+12 if self.suffix else 0
                x=(w-fw-sw)/2; y=23
                c.drawCentredString(x+fw/2,y+6,self.numerator)
                c.setStrokeColor(colors.HexColor('#49717b'));c.setLineWidth(.7);c.line(x,y,x+fw,y)
                c.drawCentredString(x+fw/2,y-13,self.denominator)
                if self.suffix:c.drawString(x+fw+12,y-3,self.suffix)
            else:
                expression=self.numerator+(' '+self.suffix if self.suffix else '')
                while size>7 and width(expression)>w-16:
                    size-=.5
                c.setFont(regular,size)
                c.drawCentredString(w/2,12,expression)
    buffer=BytesIO()
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='ReportBody',fontName=regular,fontSize=10,leading=15,spaceAfter=10))
    styles['Title'].fontName=bold
    styles['Title'].fontSize=19
    styles['Title'].leading=24
    styles['Heading2'].fontName=bold
    styles['Heading2'].fontSize=13
    styles['Heading2'].leading=18
    styles['Heading2'].spaceBefore=14
    styles['Heading2'].spaceAfter=8
    styles['Title'].textColor=colors.HexColor('#12394b')
    doc=SimpleDocTemplate(buffer,pagesize=A4,rightMargin=38,leftMargin=38,topMargin=40,bottomMargin=40,title=report['title'],author='FinSight AI')
    clean=lambda text: str(text).translate(str.maketrans({'—':'-','–':'-','−':'-','→':'->','“':'"','”':'"','’':"'",'‑':'-'}))
    para=lambda text:Paragraph(xml_escape(clean(text)),styles['ReportBody'])
    styles.add(ParagraphStyle(name='TableCell',fontName=regular,fontSize=8.5,leading=12,spaceAfter=2))
    cell=lambda text:Paragraph(xml_escape(clean(text)),styles['TableCell'])
    story=[Paragraph('FinSight AI | Financial Research',styles['Title']),para(report['title']),para(report['subtitle']),Spacer(1,12)]
    for heading,paragraphs in report['sections']:
        if heading == 'Executive assessment':
            story.append(Paragraph(heading,styles['Heading2']))
            story.extend(para(t) for t in paragraphs)
    story.append(Paragraph('Financial evidence table',styles['Heading2']))
    table_rows=[['Measure',report['prior'],report['current'],'Unit','PDF page']]+report['rows']
    table=Table([[cell(str(v)) for v in row] for row in table_rows],colWidths=[150,96,96,120,57],repeatRows=1)
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e5f1ef')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),1,colors.HexColor('#2b7067')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f4f6f8')]),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6)]))
    story.extend([table,Spacer(1,14)])
    for i,(heading,paragraphs) in enumerate(report['sections']):
        if heading == 'Executive assessment':
            continue
        story.append(Paragraph(xml_escape(heading),styles['Heading2']))
        for paragraph_index, text in enumerate(paragraphs):
            if heading == 'Method and source' and is_formula_prose(text):
                continue
            methods=section_formulas(heading, paragraph_index)
            group=[para(text)]
            for spec in methods:
                label,num,den,suffix,_=spec
                group.append(FormulaBlock(label,num,den,suffix.replace('x 100','× 100')))
                worked=worked_formula(spec,report.get('calculation_data'))
                if worked:
                    group.append(FormulaBlock(*worked[:4]))
                    group.append(para('Inputs shown in PKR billions. ~ means approximately; results use unrounded saved values.'))
            story.append(KeepTogether(group) if methods else group[0])
        if heading == 'Method and source':
            story.append(para('Monetary table values are PKR thousands; divide by 1,000,000 for PKR billions. EPS is PKR per share. Growth requires positive prior values; cash conversion requires positive net profit. Spending uses positive cash-outflow magnitudes. Calculations use unrounded inputs.'))
    def footer(canvas,doc):
        canvas.setFont(regular,8);canvas.setFillColor(colors.HexColor('#64748b'))
        canvas.drawString(38,22,'FinSight AI | Historical financial research | Source-linked calculations')
        canvas.drawRightString(A4[0]-38,22,str(doc.page))
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    return buffer.getvalue()


def extract_financial_candidates(sections, current, prior):
    """Extract financial rows from consolidated primary statements."""
    import re
    from decimal import Decimal

    patterns = {
        "sales": (
            r"^(?:revenue(?: from contracts with customers)?"
            r"(?:\s*[-–]\s*net)?|net sales)\s+"
        ),
        "gross": r"^gross profit\s+",
        "profit": r"^profit for the year\s+",
        "assets": r"^total current assets\s+",
        "liabilities": r"^total current liabilities\s+",
        "cash": (
            r"^(?:net cash (?:generated from|from|provided by)"
            r"(?: / \(utilised in\))? operating activities"
            r"|cash flows from operating activities)\s+"
        ),
        "eps": (
            r"^(?:basic earnings per share"
            r"|earnings per share\s*[-–]\s*basic(?: and diluted)?"
            r"|[-–]?\s*basic)\s+"
        ),
        "ppe_cash": (
            r"^purchases? of "
            r"(?:property,\s*plant and equipment"
            r"|property plant and equipment"
            r"|property and equipment)\s+"
        ),
        "intangibles_cash": (
            r"^(?:purchase\s*/\s*development of intangibles"
            r"|purchases? of intangible assets"
            r"|purchases? of intangibles)\s+"
        ),
    }

    labels = {
        "sales": "Net sales / revenue",
        "gross": "Gross profit",
        "profit": "Profit for the year",
        "assets": "Current assets",
        "liabilities": "Current liabilities",
        "cash": "Net operating cash flow",
        "eps": "Basic EPS",
        "ppe_cash": "Cash purchases of PPE (optional)",
        "intangibles_cash": (
            "Cash purchases/development of intangibles (optional)"
        ),
    }

    patterns.update({k: spec[1] for k,spec in EXTRA_METRICS.items()})
    labels.update({k: spec[0]+" (optional)" for k,spec in EXTRA_METRICS.items()})

    rows = {
        key: {
            "Metric": label,
            "Key": key,
            str(prior): None,
            str(current): None,
            "Source unit": "Unknown",
            "PDF page": None,
            "Source row": "",
        }
        for key, label in labels.items()
    }

    numeric = r"(?:\(?-?\d+(?:,\d{3})*(?:\.\d+)?\)?|[-–—])"
    row_values = re.compile(
        r"^(?:\d+(?:\.\d+)?\s+)?"
        r"(" + numeric + r")\s+(" + numeric + r")$"
    )
    pair = re.compile(
        r"(?<![\w,])(" + numeric + r")\s+("
        + numeric + r")\s*$"
    )

    def number(value):
        if value in ("-", "–", "—"):
            return Decimal(0)
        return Decimal(
            value.replace(",", "").replace("(", "-").replace(")", "")
        )

    for section in sections:
        text = section.get("text") or ""
        header = text[:700]
        lines = text.splitlines()

        statement = re.match(
            r"\s*consolidated statement of "
            r"(profit|income|financial position|cash flows)",
            text,
            re.IGNORECASE,
        )
        if not statement:
            continue

        statement_type = statement.group(1).lower()

        if not re.search(r"\b(?:rupees|PKR)\b", header, re.IGNORECASE):
            continue

        # Identify column order from a row containing both years.
        year_row = next(
            (
                line for line in header.splitlines()
                if re.search(rf"\b{current}\b", line)
                and re.search(rf"\b{prior}\b", line)
            ),
            None,
        )
        if year_row is None:
            continue

        first, second = (
            (current, prior)
            if year_row.find(str(current)) < year_row.find(str(prior))
            else (prior, current)
        )

        scale = re.search(
            r"\b(thousand|million|billion)s?\b",
            header,
            re.IGNORECASE,
        )
        unit = "PKR " + scale.group(1).lower() if scale else "PKR"

        if statement_type in ("profit", "income"):
            allowed = {"sales", "gross", "profit", "eps"}
        elif statement_type == "financial position":
            allowed = {"assets", "liabilities"}
        else:
            allowed = {"cash", "ppe_cash", "intangibles_cash"}

        category = "income" if statement_type in ("profit","income") else ("balance" if statement_type == "financial position" else "cash")
        allowed.update(k for k,spec in EXTRA_METRICS.items() if spec[2] == category)

        for raw_line in lines:
            line = raw_line.strip()

            for key in allowed:
                if rows[key][str(current)] is not None:
                    continue

                label_match = re.match(
                    patterns[key], line, re.IGNORECASE
                )
                if not label_match:
                    continue

                remainder = line[label_match.end():].strip()
                values_match = row_values.fullmatch(remainder)
                if not values_match:
                    continue

                values = [
                    float(number(value))
                    for value in values_match.groups()
                ]

                rows[key].update({
                    str(first): values[0],
                    str(second): values[1],
                    "Source unit": (
                        "PKR per share" if key == "eps" else unit
                    ),
                    "PDF page": section["page"],
                    "Source row": line,
                })

        # Handle unlabeled balance-sheet subtotals.
        if statement_type != "financial position":
            continue

        for key, heading in [
            ("assets", "current assets"),
            ("liabilities", "current liabilities"),
        ]:
            if rows[key][str(current)] is not None:
                continue

            active = False
            totals = [Decimal(0), Decimal(0)]
            count = 0

            for raw_line in lines:
                line = raw_line.strip()

                if line.lower().rstrip(":") == heading:
                    active = True
                    totals = [Decimal(0), Decimal(0)]
                    count = 0
                    continue

                if not active:
                    continue

                if re.match(
                    r"^(?:total\b|non[- ]current\b|equity\b"
                    r"|current (?:assets|liabilities)\b)",
                    line,
                    re.IGNORECASE,
                ):
                    break

                match = pair.search(line)
                if not match:
                    continue

                values = [number(value) for value in match.groups()]
                prefix = line[:match.start()].strip()

                if not prefix:
                    if count >= 2 and values == totals:
                        rows[key].update({
                            str(first): float(values[0]),
                            str(second): float(values[1]),
                            "Source unit": unit,
                            "PDF page": section["page"],
                            "Source row": (
                                heading.title() + " subtotal: " + line
                                + " (reconciled to component rows "
                                "in both years)"
                            ),
                        })
                    break

                if re.search(r"[A-Za-z]", prefix):
                    totals = [
                        total + value
                        for total, value in zip(totals, values)
                    ]
                    count += 1

    return list(rows.values())


def extract_business_evidence(sections):
    """Find candidate management passages; retain original wording."""
    import re


    topics = {
        "Growth strategy and outlook": [
            "future outlook",
            "prospects for growth",
            "geographic expansion",
            "organic growth",
            "inorganic growth",
        ],
        "Reported profitability discussion": [
            "gross margin increased",
            "gross margin improved",
            "gross margin declined",
            "gross margins improved",
            "net profit increased",
            "profit after tax increased",
            "improvement in profitability",
        ],
        "Risk disclosure — company/group scope not verified": [
            "customer concentration risk",
            "credit risk",
            "liquidity risk",
            "foreign exchange risk",
            "cybersecurity risk",
        ],
    }

    output = []
    used = set()

    for topic, phrases in topics.items():
        candidates = []

        for section in sections:
            text = section.get("text") or ""

            # Prefer narrative discussion over statement tables.
            if re.match(
                r"\s*(?:unconsolidated|consolidated) statement",
                text,
                re.IGNORECASE,
            ):
                continue

            # Paragraphs where available; otherwise sentence boundaries.
            blocks = re.split(
                r"\n\s*\n|(?<=[.!?])\s+(?=[A-Z])",
                text,
            )

            for block in blocks:
                passage = re.sub(r"\s+", " ", block).strip()
                if not 100 <= len(passage) <= 1600:
                    continue
                if "(cid:" in passage:
                    continue

                
                # Skip passages likely extracted from diagrams or tables.
                if passage.count("•") >= 3:
                    continue

                if topic == "Reported profitability discussion":
                    if re.search(
                        r"\b(?:decarbonization|sbti|net zero|"
                        r"emissions|renewable energy)\b",
                        passage,
                        re.IGNORECASE,
                    ):
                        continue

                lower = passage.lower()
                matches = [p for p in phrases if p in lower]
                if not matches:
                    continue

                # Exclude passages dominated by numeric table content.
                if sum(c.isdigit() for c in passage) / len(passage) > 0.12:
                    continue

                candidates.append({
                    "topic": topic,
                    "page": int(section["page"]),
                    "text": passage,
                    "matched_terms": matches,
                    "score": len(matches),
                })

        candidates.sort(key=lambda item: (-item["score"], item["page"]))

        for candidate in candidates:
            signature = candidate["text"].lower()
            if signature in used:
                continue
            used.add(signature)
            candidate.pop("score")
            output.append(candidate)
            break

    return output


def review_financial_import(sections, content, filename, identity):
    import hashlib
    import json
    import math
    import os
    import sqlite3
    from datetime import datetime, timezone

    st.subheader("Extract financial figures → review → save")

    db = ROOT / "data" / "finsight.db"
    if not db.exists():
        st.info("Create the company database first.")
        return

    with sqlite3.connect(db) as connection:
        companies = connection.execute(
            "SELECT symbol, company_name FROM companies "
            "WHERE exchange='PSX' ORDER BY symbol"
        ).fetchall()

    if not companies:
        st.info("Import company profiles first.")
        return

    target = st.selectbox(
        "Save figures for company",
        companies,
        format_func=lambda item: f"{item[0]} · {item[1]}",
        key="financial_target",
    )

    current = int(st.number_input(
        "Current financial year",
        min_value=2000,
        max_value=2100,
        value=2025,
        step=1,
        key="import_year",
    ))
    prior = current - 1

    review_id = f"{identity}_{target[0]}_{current}_research_v3"

    if st.session_state.get("financial_review_id") != review_id:
        st.session_state["financial_review_id"] = review_id
        st.session_state.pop("financial_candidates", None)

    revision_key = "financial_extraction_revision"
    revision = st.session_state.get(revision_key, 0)

    if st.button(
        "Extract candidate figures",
        key="extract_financials",
    ):
        st.session_state["financial_candidates"] = (
            extract_financial_candidates(sections, current, prior)
        )
        revision += 1
        st.session_state[revision_key] = revision

    rows = st.session_state.get("financial_candidates")
    if rows is None:
        return

    st.caption(
        "Review company, years, source units and PDF pages. "
        "The first seven fields are required. All remaining fields "
        "are optional; leave both year cells blank "
        "if unavailable. Enter zero only when established by the PDF. "
        "Use separate, non-overlapping investment rows."
    )

    widget_id = f"{review_id}_{revision}"

    edited = st.data_editor(
        pd.DataFrame(rows),
        hide_index=True,
        width="stretch",
        key="review_" + widget_id,
        disabled=["Metric", "Key", "Source row"],
        column_config={
            "Source unit": st.column_config.SelectboxColumn(
                options=[
                    "Unknown",
                    "PKR",
                    "PKR thousand",
                    "PKR million",
                    "PKR billion",
                    "PKR per share",
                ]
            ),
            "PDF page": st.column_config.NumberColumn(
                min_value=1,
                step=1,
            ),
        },
    )

    approved = st.checkbox(
        "I checked these figures, source units, years and selected "
        "company against the PDF.",
        key="approve_" + widget_id,
    )

    if not st.button(
        "Save reviewed figures",
        key="save_reviewed",
        disabled=not approved,
    ):
        return

    try:
        factors = {
            "PKR": 0.001,
            "PKR thousand": 1,
            "PKR million": 1_000,
            "PKR billion": 1_000_000,
        }

        optional = {"ppe_cash", "intangibles_cash"} | set(EXTRA_METRICS)
        figures = {str(current): {}, str(prior): {}}
        pages = {}

        def blank(value):
            return (
                value is None
                or (isinstance(value, str) and not value.strip())
                or bool(pd.isna(value))
            )

        maximum_page = max(int(item["page"]) for item in sections)

        for row in edited.to_dict("records"):
            key = row["Key"]
            unit = row["Source unit"]
            values = [row[str(current)], row[str(prior)]]

            if key in optional and all(blank(v) for v in values):
                continue

            if any(blank(v) for v in values):
                raise ValueError(
                    f"Complete both years for {row['Metric']}. "
                    "For optional rows, you can leave both years blank."
                )

            if key == "eps":
                if unit != "PKR per share":
                    raise ValueError("EPS must use PKR per share.")
                factor = 1
            else:
                if unit not in factors:
                    raise ValueError(
                        f"Choose the source unit for {row['Metric']}."
                    )
                factor = factors[unit]

            if blank(row["PDF page"]):
                raise ValueError(
                    f"Enter a PDF page for {row['Metric']}."
                )

            page = float(row["PDF page"])
            if (
                not math.isfinite(page)
                or not page.is_integer()
                or not 1 <= page <= maximum_page
            ):
                raise ValueError(
                    f"Invalid PDF page for {row['Metric']}."
                )

            pages[key] = int(page)

            for year in (current, prior):
                value = float(row[str(year)])
                if not math.isfinite(value):
                    raise ValueError(
                        f"Invalid amount for {row['Metric']} in {year}."
                    )
                figures[str(year)][key] = value * factor

        digest = hashlib.sha256(content).hexdigest()
        report_name = f"{target[0]}_{current}_{digest[:12]}.pdf"

        dataset = {
            "company": target[1],
            "symbol": target[0],
            "scope": "consolidated",
            "source": report_name,
            "original_filename": filename,
            "source_sha256": digest,
            "extraction_method": "candidate extraction with user review",
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
            "default_unit": "PKR thousands",
            "unit_overrides": {"eps": "PKR per share"},
            "definitions": {
                "assets": "Current assets",
                "liabilities": "Current liabilities",
                "cash": "Net cash from operating activities",
                "ppe_cash": "Separate cash purchases of PPE",
                "intangibles_cash": (
                    "Separate cash purchases/development of intangibles"
                ),
            },
            "pdf_pages": pages,
            "figures": figures,
            # Convert missing optional cells to JSON null.
            "reviewed_source_rows": json.loads(
                edited.to_json(orient="records")
            ),
        }
        dataset["business_evidence"] = extract_business_evidence(sections)
        dataset["research_evidence"] = collect_research_evidence(sections)
        dataset["research_version"] = 3

        build_analyst_report(dataset)

        folder = ROOT / "data" / "processed"
        reports = ROOT / "data" / "reports"
        folder.mkdir(parents=True, exist_ok=True)
        reports.mkdir(parents=True, exist_ok=True)

        serialized = json.dumps(
            dataset,
            indent=2,
            allow_nan=False,
        )

        (reports / report_name).write_bytes(content)

        path = folder / f"{target[0]}_{current}_reviewed_financials.json"
        temporary = path.with_suffix(".tmp")
        temporary.write_text(serialized, encoding="utf-8")
        os.replace(temporary, path)

        st.success(
            f"Saved {target[0]} {current}. "
            "Open Company dashboard and select the company "
            "to view and download the updated analysis."
        )

    except (ValueError, TypeError, OSError, KeyError) as error:
        st.error(f"Not saved: {error}")

def render_reviewed_dashboard(dataset):
    dataset = render_research_builder(dataset)
    research=build_analyst_report(dataset)
    st.subheader(research['title'])
    st.caption(research['subtitle']+' · User-reviewed figures · '+dataset['original_filename'])
    a,b=(dataset['figures'][research[y]] for y in ['prior','current'])
    cols=st.columns(3)
    cols[0].metric('Revenue · PKR billion',f"{b['sales']/1e6:,.2f}")
    cols[1].metric('Net profit · PKR billion',f"{b['profit']/1e6:,.2f}")
    cols[2].metric('Current ratio',f"{b['assets']/b['liabilities']:.2f}×")
    comparison=go.Figure()
    for year in [research['prior'],research['current']]:
        comparison.add_trace(go.Bar(name=year,x=['Revenue','Net profit','Net operating cash flow'],y=[dataset['figures'][year][k]/1e6 for k in ['sales','profit','cash']]))
    comparison.update_layout(template='plotly_dark',barmode='group',yaxis_title='PKR billion',height=350)
    st.plotly_chart(comparison,width='stretch',key='reviewed_comparison')
    st.dataframe(pd.DataFrame(research['rows'],columns=['Measure',research['prior'],research['current'],'Unit','PDF page']),hide_index=True,width='stretch')
    render_ratio_comparison(dataset)
    for heading,paragraphs in research['sections']:
        st.subheader(heading)
        render_report_paragraphs(heading, paragraphs, research.get("calculation_data"))
    try:
        st.download_button('Download analyst report · PDF',analyst_pdf(research),file_name=f"{dataset['symbol']}_{research['current']}_analyst_report.pdf",mime='application/pdf')
    except ImportError:
        st.info('Install reportlab to enable PDF export: python -m pip install reportlab')
    st.download_button('Download reviewed dataset',json.dumps(dataset,indent=2),file_name=f"{dataset['symbol']}_reviewed_financials.json",mime='application/json')


def rank_uploaded_sections(sections, query, question=""):
    """Require a contiguous keyword phrase, allowing simple plural endings."""
    import re
    words = re.findall(r'[a-z0-9]+', query.lower())
    if not words:
        return []
    def token(word):
        if word.isalpha() and len(word)>3:
            return re.escape(word[:-1] if word.endswith('s') else word) + r's?'
        return re.escape(word)
    pattern = re.compile(r'\b'+r'[\s\-]+'.join(token(w) for w in words)+r'\b',re.I)
    requested = 'unconsolidated' if re.search(r'\b(?:unconsolidated|standalone|company-only)\b',question,re.I) else ('consolidated' if re.search(r'\bconsolidated\b',question,re.I) else None)
    candidates = []
    for section in sections:
        text = section['text']
        has_con = bool(re.search(r'\bconsolidated\b',text,re.I))
        has_uncon = bool(re.search(r'\b(?:unconsolidated|standalone)\b',text,re.I))
        # Mixed summaries and unknown scope are excluded for a scope-specific question.
        if requested == 'consolidated' and (not has_con or has_uncon):
            continue
        if requested == 'unconsolidated' and (not has_uncon or has_con):
            continue
        primary = bool(re.match(r'\s*(?:unconsolidated|consolidated)?\s*statement of (?:profit|income)',text,re.I))
        for match in pattern.finditer(text):
            # Preserve nearby lines and column headers rather than unrelated chunks.
            left = max(0,text.rfind('\n',0,max(0,match.start()-500)))
            excerpt = text[left:min(len(text),match.end()+1000)]
            header = text[:450]
            evidence = header+'\nMatched passage:\n'+excerpt
            tail = text[match.end():match.end()+100]
            has_amount = bool(re.match(r'\s*(?:\d{1,2}(?:\.\d+)?\s+)?\(?\d{1,3}(?:,\d{3})+(?:\.\d+)?',tail))
            statement = bool(re.search(r'statement of (?:profit|income)|finance costs?\s*\n',header,re.I))
            candidates.append({'page':section['page'],'side':section['side'],'text':evidence,
                               'score':(primary,has_amount,statement)})
    candidates.sort(key=lambda x:x['score'],reverse=True)
    results,seen = [],set()
    for item in candidates:
        identity=(item['page'],item['side'])
        if identity not in seen:
            results.append(item);seen.add(identity)
        if len(results)==3:
            break
    return results


def check_uploaded_answer_numbers(answer, extracts):
    """Reject unseen numerical values; this is not a semantic fact checker."""
    import re
    from decimal import Decimal
    pattern = r'(?<![\w.])\d+(?:,\d{3})*(?:\.\d+)?(?![\w.])'
    def values(text):
        text = re.sub(r'\[PDF page\s+\d+\]', '', text, flags=re.I)
        return {Decimal(n.replace(',','')) for n in re.findall(pattern,text)}
    evidence_numbers = values('\n'.join(item['text'] for item in extracts))
    if values(answer) - evidence_numbers:
        raise RuntimeError('Answer withheld: a number in the AI response was not found in the supplied evidence. Review the matched passage. No automatic unit conversions are accepted.')


def render_uploaded_report():
    import hashlib
    from io import BytesIO
    st.subheader('Research any annual report')
    st.caption('Upload a text-based PDF. This workspace is independent of the company selector and EFERT financial dashboard. Use Build a company analyst report below to extract, review and save figures.')
    upload = st.file_uploader('Annual report PDF (up to 32 MB)',type=['pdf'],key='research_pdf')
    if upload is None:
        return
    if upload.size > 32*1024*1024:
        st.error('Please use a PDF smaller than 32 MB.'); return
    layout = st.radio('PDF layout', ['One page per PDF page','Two printed pages side by side'],horizontal=True,key='research_layout')
    content = upload.getvalue()
    identity = hashlib.sha256(content+layout.encode()+b'scope-retrieval-v3').hexdigest()
    if st.session_state.get('research_identity') != identity:
        st.session_state['research_identity'] = identity
        st.session_state.pop('research_sections',None)
        st.session_state.pop('research_answer',None)
    st.caption(f'Active document: {upload.name}')
    if st.button('Read PDF',key='read_research_pdf'):
        st.session_state.pop('research_sections',None)
        st.session_state.pop('research_answer',None)
        try:
            import pdfplumber
            sections, empty = [], 0
            with st.spinner('Reading PDF pages. Large reports can take a few minutes...'):
                with pdfplumber.open(BytesIO(content)) as pdf:
                    if len(pdf.pages)>500:
                        raise ValueError('Maximum 500 PDF pages. Upload a smaller report or extract.')
                    progress = st.progress(0)
                    for number,page in enumerate(pdf.pages,1):
                        regions = [('full',page)]
                        if layout.startswith('Two'):
                            x0,y0,x1,y1 = page.bbox
                            mid = (x0+x1)/2
                            regions = [('left',page.crop((x0,y0,mid,y1))),('right',page.crop((mid,y0,x1,y1)))]
                        for side,region in regions:
                            text = region.extract_text() or ''
                            if text.strip():
                                sections.append({'page':number,'side':side,'text':text})
                            else:
                                empty += 1
                        progress.progress(number/len(pdf.pages))
                    progress.empty()
            st.session_state['research_sections'] = sections
            st.session_state['research_empty'] = empty
        except Exception as exc:
            st.error(f'Could not extract this PDF: {exc}')
    sections = st.session_state.get('research_sections')
    if sections is None:
        return
    if not sections:
        st.warning('No readable text found. Scanned PDFs need OCR, which is not connected yet.'); return
    st.success(f'Read {len(sections)} text sections. PDF page references refer to this uploaded file.')
    if st.session_state.get('research_empty'):
        st.caption(f"{st.session_state['research_empty']} page regions contained no extracted text; coverage is incomplete.")
    with st.expander('Build a company analyst report', expanded=False):
        review_financial_import(sections, content, upload.name, identity)
    with st.form('uploaded_report_question'):
        query = st.text_input('Search keywords',placeholder='finance cost')
        question = st.text_input('AI question',placeholder='What was the consolidated finance cost in 2025? Include units and the PDF page.')
        generate = st.checkbox('Generate AI answer',value=True)
        submit = st.form_submit_button('Search / answer uploaded PDF')
    if submit:
        saved = {'results':[], 'answer':None,'error':None,'question':question}
        st.session_state['research_answer'] = saved
        if not query.strip():
            saved['error'] = 'Enter a short metric phrase, such as finance cost, in Search keywords.'
        else:
            saved['results'] = rank_uploaded_sections(sections,query.strip(),question)
            if generate and question.strip() and saved['results']:
                try:
                    with st.spinner('Generating answer with local Ollama...'):
                        draft = answer_from_extracts(question + '\nRepeat only numbers explicitly present in the evidence. Do not convert units. If the requested scope, year or measure is not established, say Not available in the provided extracts.',saved['results'])
                        check_uploaded_answer_numbers(draft,saved['results'])
                        saved['answer'] = draft
                except (RuntimeError,ValueError) as exc:
                    saved['error'] = str(exc)
            elif generate and not question.strip():
                saved['error'] = 'Evidence retrieved. Enter a question to generate an answer.'
    saved = st.session_state.get('research_answer')
    if saved:
        if saved['error']:
            st.error(saved['error'])
        if saved['answer']:
            st.markdown(saved['answer'])
            st.caption('AI answer from the extracts below. Citations identify supplied pages, not independent verification. Check units, years and consolidated versus company-only scope.')
        if not saved['results'] and not saved['error']:
            st.info('No matching text found. Try shorter keywords; absence from search is not proof of absence from the report.')
        for item in saved['results']:
            with st.expander(f"PDF page {item['page']} | {item['side']}",expanded=True):
                st.text(item['text'])
    st.caption('Keyword retrieval may miss relevant passages. Tables, fonts and columns can affect reading order. Review the original PDF before using figures.')


company_tab, research_tab = st.tabs(['Company dashboard', 'Uploaded PDF research'])
with research_tab:
    render_uploaded_report()
with company_tab:
    st.caption('Company figures belong to the selected company. Uploaded PDFs are researched in the separate Uploaded PDF research tab.')
    DB_PATH = ROOT / "data" / "finsight.db"
    if not DB_PATH.exists():
        st.error("Company database is missing. Run src/init_db.py and import company profiles.")
        st.stop()
    
    try:
        with sqlite3.connect(DB_PATH.as_uri() + "?mode=ro", uri=True) as connection:
            connection.row_factory = sqlite3.Row
            companies = [dict(row) for row in connection.execute("""
            SELECT c.id, c.symbol, c.company_name, c.official_website,
                   l.local_path, l.status AS logo_status
            FROM companies c
            LEFT JOIN company_logos l ON l.company_id = c.id
            WHERE c.exchange = 'PSX'
            ORDER BY c.symbol
        """)]
    except sqlite3.Error as exc:
        st.error(f"Could not read company registry: {exc}")
        st.stop()
    
    if not companies:
        st.info("No company profiles loaded yet. Run the company-profile fetcher.")
        st.stop()
    
    by_symbol = {company["symbol"]: company for company in companies}
    symbols = list(by_symbol)
    symbol = st.selectbox(
        "Company", symbols,
        index=symbols.index("EFERT") if "EFERT" in symbols else 0,
        format_func=lambda value: f"{value} · {by_symbol[value]['company_name']}",
        key="selected_company",
    )
    company = by_symbol[symbol]
    if st.session_state.get("active_company") != symbol:
        st.session_state.pop("report_submission", None)
        st.session_state["active_company"] = symbol
    
    logo_html = f'<div class="symbol">{escape(symbol)}</div>'
    if company["logo_status"] == "reviewed" and company["local_path"]:
        logo_path = (ROOT / company["local_path"]).resolve()
        logo_folder = (ROOT / "data" / "logos").resolve()
        if logo_path.is_relative_to(logo_folder) and logo_path.is_file():
            mime = {".png": "image/png", ".svg": "image/svg+xml"}.get(logo_path.suffix.lower())
            if mime:
                try:
                    encoded = base64.b64encode(logo_path.read_bytes()).decode("ascii")
                    logo_html = (
                        '<div style="background:#0c111b;padding:12px;border-radius:10px;'
                        'width:180px;max-width:40%;flex-shrink:0">'
                        f'<img src="data:{mime};base64,{encoded}" '
                        f'alt="{escape(company["company_name"], quote=True)} logo" '
                        'style="display:block;width:100%;height:56px;object-fit:contain"></div>'
                    )
                except OSError:
                    pass
    
    st.markdown(
        f'<div class="company">{logo_html}<div>'
        f'<div class="company-name">{escape(company["company_name"])}</div>'
        f'<div class="meta">PSX · {escape(symbol)}</div></div></div>',
        unsafe_allow_html=True,
    )
    website = company.get("official_website")
    if website and website.startswith(("https://", "http://")):
        st.link_button("Company website", website)
    
    # Company website leadership: source-specific observations, not a merged current roster.
    with st.expander("Board & senior management", expanded=symbol != "EFERT"):
        st.caption("Official website extracts · Names and roles require source review. Coverage is not yet certified complete.")
        try:
            with sqlite3.connect(DB_PATH.as_uri() + "?mode=ro", uri=True) as leadership_db:
                leadership_db.row_factory = sqlite3.Row
                exists = leadership_db.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='leadership_fetches'"
                ).fetchone()
                snapshots = []
                if exists:
                    snapshots = [dict(row) for row in leadership_db.execute("""
                    SELECT f.* FROM leadership_fetches f
                    WHERE f.company_id=? AND f.id=(
                        SELECT f2.id FROM leadership_fetches f2
                        WHERE f2.company_id=f.company_id AND f2.source_url=f.source_url
                        ORDER BY f2.fetched_at DESC, f2.id DESC LIMIT 1
                    ) ORDER BY f.category, f.source_url
                """, (company["id"],))]
            if not snapshots:
                st.info("Website leadership has not been fetched for this company yet.")
            for snapshot in snapshots:
                st.markdown(f"**{snapshot['category'].title()} · {snapshot['status'].replace('_', ' ')}**")
                if snapshot["source_url"].startswith("https://"):
                    st.link_button("Open official source", snapshot["source_url"])
                st.caption(f"Fetched: {snapshot['fetched_at']} · Source effective date: not established")
                people = json.loads(snapshot["people_json"])
                if people:
                    st.dataframe(pd.DataFrame([
                        {"Name": p["name"], "Designation": p["role"], "Category": p["category"]}
                        for p in people
                    ]), hide_index=True, width="stretch")
                elif snapshot["status"] == "failed":
                    st.warning("The latest source fetch failed. Earlier observations remain in the database.")
                else:
                    st.warning("No name/title cards extracted. This does not mean the company has no directors.")
                if snapshot.get("error"):
                    st.caption(snapshot["error"])
        except (sqlite3.Error, ValueError, KeyError, TypeError) as exc:
            st.warning(f"Leadership records could not be displayed: {exc}")
    
    def demo_prices():
        """Reproducible fictional OHLCV; weekdays are not an exchange calendar."""
        import random
        rng = random.Random(42)
        rows = []
        previous = 100.0
        for day in pd.bdate_range('2025-01-01', periods=260):
            opening = round(previous * (1 + rng.uniform(-0.009, 0.009)), 2)
            closing = round(max(1.0, opening * (1 + rng.gauss(0.0005, 0.017))), 2)
            high = round(max(opening, closing) * (1 + rng.uniform(0.001, 0.016)), 2)
            low = round(min(opening, closing) * (1 - rng.uniform(0.001, 0.016)), 2)
            rows.append([day, opening, high, low, closing, rng.randint(50000, 900000)])
            previous = closing
        return pd.DataFrame(rows, columns=['Date','Open','High','Low','Close','Volume'])
    
    
    def validate_prices(frame):
        """Require one daily OHLCV series. Never silently repair financial rows."""
        import numpy as np
        frame = frame.copy()
        frame.columns = [str(c).strip().lower() for c in frame.columns]
        required = ['date','open','high','low','close','volume']
        if frame.columns.duplicated().any():
            raise ValueError('Duplicate column names found.')
        missing = [c for c in required if c not in frame.columns]
        if missing:
            raise ValueError('Missing columns: ' + ', '.join(missing))
        if frame.empty or len(frame) > 20000:
            raise ValueError('Upload between 1 and 20,000 daily rows.')
        for field in ('symbol', 'ticker'):
            if field in frame and frame[field].nunique(dropna=False) > 1:
                raise ValueError('Upload prices for one instrument only.')
        raw_dates = frame['date'].astype(str).str.strip()
        if not raw_dates.str.fullmatch(r'\d{4}-\d{2}-\d{2}').all():
            raise ValueError('Dates must use YYYY-MM-DD, without a time component.')
        frame['date'] = pd.to_datetime(raw_dates, format='%Y-%m-%d', errors='coerce')
        if frame['date'].isna().any() or frame['date'].duplicated().any():
            raise ValueError('Dates must be valid and unique; duplicate trading days were found or a date is invalid.')
        for col in required[1:]:
            frame[col] = pd.to_numeric(frame[col], errors='coerce')
            if not np.isfinite(frame[col].to_numpy(dtype=float)).all():
                raise ValueError(f'{col}: missing or non-finite numeric values. Use plain numbers without thousands separators.')
        if (frame[['open','high','low','close']] <= 0).any().any():
            raise ValueError('All OHLC prices must be greater than zero.')
        if (frame['volume'] < 0).any():
            raise ValueError('Volume cannot be negative.')
        frame['ohlc_issue'] = ((frame['high'] < frame[['open','close','low']].max(axis=1)) |
                               (frame['low'] > frame[['open','close','high']].min(axis=1)))
        return frame[required + ['ohlc_issue']].sort_values('date').reset_index(drop=True).rename(columns=str.title)
    
    
    
    def normalize_price_csv(frame, date_format):
        """Convert Investing.com exports without guessing date order or missing volume."""
        import re
        frame = frame.copy()
        frame.columns = [str(c).lstrip('\ufeff').strip().lower() for c in frame.columns]
        if frame.columns.duplicated().any():
            raise ValueError('Duplicate CSV headers.')
        for old,new in [('price','close'),('vol.','volume')]:
            if old in frame.columns:
                if new in frame.columns:
                    raise ValueError(f'Ambiguous columns: both {old} and {new}.')
                frame = frame.rename(columns={old:new})
        if 'date' not in frame:
            raise ValueError('Date column is missing.')
        formats = {'YYYY-MM-DD':'%Y-%m-%d','DD/MM/YYYY':'%d/%m/%Y','MM/DD/YYYY':'%m/%d/%Y'}
        if date_format not in formats:
            raise ValueError('Choose an explicit date format.')
        dates = pd.to_datetime(frame['date'].astype(str).str.strip(),format=formats[date_format],errors='coerce')
        if dates.isna().any():
            raise ValueError('Some dates do not match the selected format.')
        frame['date'] = dates.dt.strftime('%Y-%m-%d')
        for col in ['open','high','low','close']:
            if col in frame:
                frame[col] = frame[col].astype(str).str.strip().str.replace(',', '',regex=False)
        def volume(value):
            text = str(value).strip().replace(',', '')
            match = re.fullmatch(r'(\d+(?:\.\d+)?)\s*([KMB]?)',text,re.I)
            if not match:
                raise ValueError('Volume contains a missing or unsupported value; it will not be replaced with zero.')
            return float(match[1]) * {'':1,'K':1000,'M':1000000,'B':1000000000}[match[2].upper()]
        if 'volume' in frame:
            frame['volume'] = frame['volume'].map(volume)
        return validate_prices(frame)
    
    
    def price_indicators(frame):
        """SMA 20/50, Wilder RSI 14 and MACD 12/26/9, with warm-up gaps."""
        import numpy as np
        result = frame.copy()
        close = result['Close'].astype(float)
        result['SMA20'] = close.rolling(20, min_periods=20).mean()
        result['SMA50'] = close.rolling(50, min_periods=50).mean()
        rsi = pd.Series(np.nan, index=result.index, dtype=float)
        if len(close) > 14:
            delta = close.diff()
            gains = delta.clip(lower=0)
            losses = (-delta).clip(lower=0)
            avg_gain = gains.iloc[1:15].mean()
            avg_loss = losses.iloc[1:15].mean()
            def rsi_value(gain, loss):
                if gain == 0 and loss == 0: return 50.0
                if loss == 0: return 100.0
                return 100 - 100 / (1 + gain / loss)
            rsi.iloc[14] = rsi_value(avg_gain, avg_loss)
            for i in range(15, len(close)):
                avg_gain = (avg_gain * 13 + gains.iloc[i]) / 14
                avg_loss = (avg_loss * 13 + losses.iloc[i]) / 14
                rsi.iloc[i] = rsi_value(avg_gain, avg_loss)
        result['RSI14'] = rsi
        ema12 = close.ewm(span=12, adjust=False, min_periods=12).mean()
        ema26 = close.ewm(span=26, adjust=False, min_periods=26).mean()
        result['MACD'] = ema12 - ema26
        result['Signal'] = result['MACD'].ewm(span=9, adjust=False, min_periods=9).mean()
        result['Histogram'] = result['MACD'] - result['Signal']
        return result
    
    
    def render_technical_analysis():
        from io import BytesIO
        from plotly.subplots import make_subplots
        st.subheader('Price & technical analysis')
        mode = st.radio('Price source', ['Fictional demo', 'Upload CSV'], horizontal=True, key='price_source_mode')
        template = demo_prices()
        st.download_button('Download demo / CSV template', template.to_csv(index=False, date_format='%Y-%m-%d').encode(),
                           file_name='FICTIONAL_DEMO_OHLCV.csv', mime='text/csv', key='price_template')
        if mode == 'Fictional demo':
            st.info('FICTIONAL DEMO - Generated prices for DEMO, not EFERT or any selected company. Not live market data.')
            label, currency, source, adjustment = 'DEMO', 'Demo price units', 'Deterministic synthetic generator', 'Not applicable (synthetic)'
            prices = template
        else:
            st.caption('Accepts standard OHLCV or Investing.com exports: Price becomes Close; Vol. becomes Volume. K/M/B suffixes are converted to numeric units.')
            uploaded = st.file_uploader('Daily price CSV (maximum 5 MB)', type=['csv'], key='price_csv')
            if uploaded is None:
                st.info('Upload your permitted historical data, or select Fictional demo to explore the charts.')
                return
            if uploaded.size > 5_000_000:
                st.error('CSV exceeds 5 MB.'); return
            try:
                raw = pd.read_csv(BytesIO(uploaded.getvalue()), encoding='utf-8-sig')
                headers = {str(c).strip().lower(): c for c in raw.columns}
                investing = {'date','price','open','high','low','vol.','change %'}.issubset(headers)
                source = 'Investing.com export format (detected)' if investing else 'Uploaded CSV'
                import re
                label = re.sub(r' Historical Data.*$', '', Path(uploaded.name).stem, flags=re.I)
                known_efert = bool(re.fullmatch(r'Engro Fertilizers \(ENGR\)', label, flags=re.I))
                currency = 'PKR' if known_efert else 'Price units (currency not supplied)'
                adjustment = 'Unknown'
                raw_dates = raw[headers['date']].astype(str).str.strip() if 'date' in headers else pd.Series([], dtype=str)
                candidates = []
                for title, fmt in [('YYYY-MM-DD','%Y-%m-%d'),('DD/MM/YYYY','%d/%m/%Y'),('MM/DD/YYYY','%m/%d/%Y')]:
                    parsed = pd.to_datetime(raw_dates,format=fmt,errors='coerce')
                    if len(parsed) and parsed.notna().all():
                        candidates.append((title,parsed))
                if not candidates:
                    raise ValueError('Date column is missing or dates are not consistently ISO, day/month/year, or month/day/year.')
                if len(candidates)>1 and not candidates[0][1].equals(candidates[1][1]):
                    date_format = st.selectbox('These dates are ambiguous — choose their order', [c[0] for c in candidates])
                else:
                    date_format = candidates[0][0]
                with st.expander('Import details / optional overrides'):
                    st.caption('Source format is detected from headers; this does not independently verify provenance. Instrument comes from the filename. The known Engro Fertilizers (ENGR) filename maps to EFERT / PKR; other currencies remain unspecified.')
                    label = st.text_input('Instrument label', value=label)
                    currency = st.text_input('Currency / unit', value=currency)
                    source = st.text_input('Source', value=source)
                    adjustment = st.selectbox('Adjustment', ['Unknown','Unadjusted','Split-adjusted OHLC','Split-and-dividend-adjusted OHLC'])
                prices = normalize_price_csv(raw, date_format)
            except (ValueError, UnicodeError, pd.errors.ParserError) as exc:
                st.error(f'CSV rejected: {exc}'); return
            st.caption('K/M/B volume values retain the provider’s rounding. Original price values are preserved.')
        if 'Ohlc_Issue' not in prices:
            prices['Ohlc_Issue'] = False
        issues = prices.loc[prices['Ohlc_Issue']]
        st.caption(f'Loaded {len(prices):,} rows | {prices.Date.min():%Y-%m-%d} to {prices.Date.max():%Y-%m-%d}')
        if not issues.empty:
            st.warning(f'{len(issues)} rows have inconsistent OHLC values. Source prices have not been changed.')
            with st.expander('Review inconsistent rows', expanded=False):
                st.dataframe(issues, hide_index=True, width='stretch')
                st.download_button('Download flagged rows', issues.to_csv(index=False).encode('utf-8'),
                                   file_name='flagged_price_rows.csv', mime='text/csv')
            st.caption('All dates and reported closes are retained for indicators. Flagged candles are omitted; orange crosses mark their unverified closes. Indicators can be affected by source errors.')
        data = price_indicators(prices)
        st.markdown(f'**{label} | {currency}**')
        st.caption(f'Source: {source} | Adjustment: {adjustment} | Last data date: {data.Date.iloc[-1]:%Y-%m-%d} | Historical data, not live')
        if adjustment in ('Unknown','Unadjusted'):
            st.caption('Corporate actions may create price jumps and distort indicators. Use consistently adjusted OHLC when appropriate.')
        window = st.selectbox('Display window', ['All sessions','Last 60 sessions','Last 120 sessions'], key='price_window')
        count = {'Last 60 sessions':60, 'Last 120 sessions':120}.get(window, len(data))
        visible = data.tail(count)
        overlays = st.multiselect('Moving averages', ['SMA 20','SMA 50'], default=['SMA 20','SMA 50'], key='price_overlays')
        panels = st.multiselect('Indicator panels', ['RSI 14','MACD'], default=['RSI 14','MACD'], key='price_panels')
        # Summary uses full history, independently of the chart display window.
        from html import escape as html_escape
        import math

        def fmt(value, digits=2):
            try:
                return f"{float(value):,.{digits}f}" if math.isfinite(float(value)) else "Not available"
            except (TypeError, ValueError):
                return "Not available"

        last = data.iloc[-1]
        previous = data.iloc[-2] if len(data) > 1 else None
        prev_close = previous.Close if previous is not None else None
        change = (last.Close / prev_close - 1) * 100 if prev_close is not None and prev_close > 0 else None
        prior_volumes = data.Volume.iloc[:-1].tail(20)
        average = prior_volumes.mean() if len(prior_volumes) == 20 and prior_volumes.notna().all() else None
        relative = last.Volume / average if average is not None and average > 0 else None
        prev_rsi = previous.RSI14 if previous is not None else None
        rsi_change = last.RSI14 - prev_rsi if prev_rsi is not None and pd.notna(prev_rsi) and pd.notna(last.RSI14) else None
        badge = "DEMO" if mode == "Fictional demo" else "HISTORICAL"
        session = f"{last.Date:%d %b %Y}"
        price_change = f"{change:+.2f}% vs previous session" if change is not None else "Change not available"
        range_text = "Unavailable: flagged OHLC" if last.Ohlc_Issue else f"{fmt(last.Low)} – {fmt(last.High)}"
        rsi_delta = f"{rsi_change:+.2f} points" if rsi_change is not None else "Not available"

        def summary_card(title, value, subtitle, details, gauge=None):
            detail_html = "".join(
                f'<div class="ps-detail"><span>{html_escape(k)}</span><b>{html_escape(v)}</b></div>'
                for k, v in details
            )
            gauge_html = ""
            if gauge is not None and pd.notna(gauge):
                position = max(0.0, min(100.0, float(gauge)))
                gauge_html = (
                    f'<div class="ps-gauge" role="img" aria-label="RSI {position:.2f} on a 0 to 100 scale">'
                    f'<i style="left:clamp(3px,{position:.2f}%,calc(100% - 3px))"></i></div>'
                    '<div class="ps-scale"><span>0</span><span>100</span></div>'
                )
            return (
                '<div class="ps-card">'
                f'<div class="ps-head"><span>{html_escape(title)}</span><small>{badge}</small></div>'
                f'<div class="ps-value">{html_escape(value)}</div>'
                f'<div class="ps-sub">{html_escape(subtitle)}</div>'
                f'<div class="ps-details">{detail_html}</div>{gauge_html}</div>'
            )

        cards_html = summary_card("Last close", fmt(last.Close), price_change, [
            ("Previous close", fmt(prev_close)), ("Session low – high", range_text),
            ("Currency / unit", str(currency)), ("Price date", session),
        ])
        relative_label, volume_difference = volume_comparison(relative)
        cards_html += summary_card("Volume", fmt(last.Volume, 0), "Latest session · " + session, [
            ("Prior 20-session average", fmt(average, 0)),
            ("Relative volume (20)", relative_label),
            ("vs average", volume_difference),
        ])
        cards_html += summary_card("RSI (14)", fmt(last.RSI14), "Latest session · " + session, [
            ("Previous RSI", fmt(prev_rsi)), ("Change", rsi_delta),
        ], gauge=last.RSI14)
        st.markdown("""<style>
        .ps-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin:8px 0 16px}
        .ps-card{background:#131e2c;border:1px solid #2b3c52;border-radius:12px;padding:20px;min-width:0}
        .ps-head{display:flex;justify-content:space-between;align-items:center;gap:8px;color:#afbed1;font-size:13px}
        .ps-head small{font-size:9px;letter-spacing:.7px;padding:3px 6px;border:1px solid #416078;border-radius:4px;color:#9cdcca}
        .ps-value{font-size:clamp(23px,2.3vw,32px);font-weight:650;color:#f1f5fb;margin:10px 0 4px;overflow-wrap:anywhere}
        .ps-sub{font-size:12px;color:#afbed1;min-height:20px}
        .ps-details{border-top:1px solid #2b3c52;margin-top:14px;padding-top:10px}
        .ps-detail{display:flex;justify-content:space-between;gap:12px;font-size:13px;line-height:1.55;padding:5px 0;color:#aebed2}
        .ps-detail b{font-weight:500;color:#e6edf6;text-align:right;overflow-wrap:anywhere;min-width:0}
        .ps-gauge{height:6px;background:#344b65;border-radius:5px;position:relative;margin-top:16px}
        .ps-gauge i{position:absolute;top:-3px;width:4px;height:12px;background:#6ce2c2;transform:translateX(-50%);border-radius:2px}
        .ps-scale{display:flex;justify-content:space-between;color:#aebed2;font-size:10px;margin-top:5px}
        @media(max-width:800px){.ps-grid{grid-template-columns:1fr}.ps-card{padding:16px}}
        </style><div class="ps-grid">""" + cards_html + "</div>", unsafe_allow_html=True)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.78,0.22], vertical_spacing=0.035)
        candles = visible.loc[~visible['Ohlc_Issue']]
        fig.add_trace(go.Candlestick(x=candles.Date,open=candles.Open,high=candles.High,low=candles.Low,close=candles.Close,
                                    name=label,increasing_line_color='#51d3b4',decreasing_line_color='#ff8396'),row=1,col=1)
        flagged = visible.loc[visible['Ohlc_Issue']]
        if not flagged.empty:
            fig.add_trace(go.Scatter(x=flagged.Date,y=flagged.Close,mode='markers',name='Flagged close (unverified)',marker=dict(color='#ffb454',symbol='x',size=9)),row=1,col=1)
        for option,col,color in [('SMA 20','SMA20','#efc66b'),('SMA 50','SMA50','#83aaff')]:
            if option in overlays:
                fig.add_trace(go.Scatter(x=visible.Date,y=visible[col],name=option,line=dict(color=color,width=1.5)),row=1,col=1)
        fig.add_trace(go.Bar(x=visible.Date,y=visible.Volume,name='Volume',marker_color=['#51d3b4' if c>=o else '#ff8396' for c,o in zip(visible.Close,visible.Open)]),row=2,col=1)
        if st.button('Reset chart view', key='reset_price_chart'):
            st.session_state['price_chart_reset'] = st.session_state.get('price_chart_reset', 0) + 1
        reset_id = st.session_state.get('price_chart_reset', 0)
        st.caption('Drag left/right to pan. Scroll over the plot to zoom in time. Double-click or use Reset chart view to restore the view. Price scale is locked to prevent vertical drift.')
        chart_config = {'displaylogo':False, 'displayModeBar':True, 'scrollZoom':True,
                        'doubleClick':'reset', 'modeBarButtonsToRemove':['select2d','lasso2d']}
        def style_chart(chart,height):
            chart.update_layout(template='plotly_dark',height=height,paper_bgcolor='#0c111b',plot_bgcolor='#0c111b',
                                margin=dict(l=15,r=15,t=30,b=20),legend=dict(orientation='h'),hovermode='x unified',dragmode='pan')
            chart.update_xaxes(showgrid=False,rangeslider_visible=False)
            chart.update_yaxes(gridcolor='#263044',fixedrange=True)
        style_chart(fig,560)
        fig.update_yaxes(title_text=currency,row=1,col=1)
        fig.update_yaxes(title_text='Volume',row=2,col=1)
        st.plotly_chart(fig,width='stretch',theme=None,config=chart_config,key=f'price_chart_{reset_id}')
        if 'RSI 14' in panels:
            rfig=go.Figure(go.Scatter(x=visible.Date,y=visible.RSI14,name='Wilder RSI 14',line=dict(color='#b59aff')))
            rfig.add_hline(y=70,line_dash='dot',line_color='#ff8396')
            rfig.add_hline(y=30,line_dash='dot',line_color='#51d3b4')
            style_chart(rfig,230);rfig.update_yaxes(range=[0,100],title_text='RSI')
            st.plotly_chart(rfig,width='stretch',theme=None,config=chart_config,key=f'rsi_chart_{reset_id}')
        if 'MACD' in panels:
            mfig=go.Figure()
            mfig.add_trace(go.Bar(x=visible.Date,y=visible.Histogram,name='Histogram',marker_color=['#51d3b4' if pd.notna(v) and v>=0 else '#ff8396' for v in visible.Histogram]))
            for key,color in [('MACD','#83aaff'),('Signal','#efc66b')]:
                mfig.add_trace(go.Scatter(x=visible.Date,y=visible[key],name=key,line=dict(color=color)))
            style_chart(mfig,260)
            st.plotly_chart(mfig,width='stretch',theme=None,config=chart_config,key=f'macd_chart_{reset_id}')
        if len(data)<50:
            st.caption('Short history: SMA 20 needs 20 rows, SMA 50 needs 50, RSI needs 15 and MACD signal needs 34. Unavailable values remain blank.')
        with st.expander('How to read these indicators'):
            st.write('SMA shows the average closing price over 20 or 50 available sessions. RSI uses Wilder smoothing over 14 price changes; 70 and 30 are reference levels, not automatic trade instructions.')
            st.write('MACD is EMA(12) minus EMA(26). Signal is its 9-period EMA. Histogram is MACD minus signal. EMAs start from the first available close; results can differ across providers with different history or initialization.')
            st.write('Indicators use the entire uploaded history before the display window is selected. Missing dates are not filled. They describe historical prices and do not guarantee future returns or constitute a buy/sell recommendation.')
        st.download_button('Download calculated indicators',data.to_csv(index=False,date_format='%Y-%m-%d').encode(),
                           file_name='price_indicators.csv',mime='text/csv',key='price_indicators_download')
    
    
    with st.expander('Price charts & technical analysis', expanded=True):
        render_technical_analysis()
    
    
    reviewed_paths = sorted((ROOT/'data'/'processed').glob(f'{symbol}_????_reviewed_financials.json'),reverse=True)
    if reviewed_paths:
        chosen = st.selectbox('Reviewed annual dataset',reviewed_paths,format_func=lambda p:p.stem,key='reviewed_dataset')
        try:
            reviewed = json.loads(chosen.read_text(encoding='utf-8'))
            if reviewed['symbol'] != symbol:raise ValueError('Company mismatch.')
            render_reviewed_dashboard(reviewed)
        except (ValueError,KeyError,OSError) as exc:
            st.error(f'Could not load reviewed figures: {exc}')
        st.stop()

    # Only EFERT has an imported, mapped financial-report dataset at this stage.
    if symbol != "EFERT":
        st.info("Financial data not loaded yet for this company.")
        st.caption("Company profile is available. Financial charts and report search will appear after its report is imported.")
        st.markdown('<div class="foot">PSX · Company profile · Share prices and insider disclosures are not connected yet.</div>', unsafe_allow_html=True)
        st.stop()
    
    # Consolidated figures manually transcribed from EFERT Annual Report 2025.
    # PKR thousands, except EPS (PKR/share). PDF pages 160–162.
    FINANCIALS_PATH = (
        ROOT / "data" / "processed" / "EFERT_2025_financials.json"
    )
    
    try:
        financial_data = json.loads(
            FINANCIALS_PATH.read_text(encoding="utf-8")
        )
        if financial_data.get("symbol") != symbol or financial_data.get("scope") != "consolidated":
            raise ValueError("Financial dataset does not match the selected company/scope.")
        F = {
            int(year): values
            for year, values in financial_data["figures"].items()
        }
    except (OSError, ValueError, KeyError, TypeError) as exc:
        st.error(f"Could not load financial data: {exc}")
        st.stop()
    A, B = F[2024], F[2025]
    growth = lambda field: (B[field] / A[field] - 1) * 100
    margin = lambda year, field: F[year][field] / F[year]['sales'] * 100
    
    st.caption("Consolidated · Year ended 31 December 2025")
    
    st.markdown(f'''<div class="cards">
    <div class="card"><div class="card-label">Net sales · PKR billions</div>
    <div class="card-value">{B['sales']/1e6:.2f}</div>
    <div class="change negative">{growth('sales'):+.2f}% <span class="change">vs 2024</span></div></div>
    <div class="card"><div class="card-label">Net profit · PKR billions</div>
    <div class="card-value">{B['profit']/1e6:.2f}</div>
    <div class="change negative">{growth('profit'):+.2f}% <span class="change">vs 2024</span></div></div>
    <div class="card"><div class="card-label">Net profit margin</div>
    <div class="card-value">{margin(2025,'profit'):.2f}<small> %</small></div>
    <div class="change negative">{margin(2025,'profit')-margin(2024,'profit'):+.2f} pp <span class="change">vs 2024</span></div></div>
    <div class="card"><div class="card-label">Current ratio</div>
    <div class="card-value">{B['assets']/B['liabilities']:.2f}<small> ×</small></div>
    <div class="change">2024: {A['assets']/A['liabilities']:.2f}× · Below 1.00×</div></div>
    </div>''', unsafe_allow_html=True)
    
    overview, statements, evidence, report_search, analyst_report = st.tabs(
        ["Overview", "Financial statements", "Source evidence", "Report search", "Analyst report"]
    )
    def chart_style(fig, title):
        fig.update_layout(template='plotly_dark', height=285,
            paper_bgcolor='#0c111b', plot_bgcolor='#0c111b',
            font=dict(family='Arial, sans-serif', size=12, color='#aebdd1'),
            margin=dict(l=12,r=16,t=25,b=25),
            legend=dict(orientation='h',y=1.15,x=0,font=dict(color='#cdd8e7',size=11)),
            yaxis=dict(title=title,gridcolor='#263044',zerolinecolor='#526079',automargin=True),
            xaxis=dict(type='category',showgrid=False,automargin=True),
            bargap=.55)
        return fig
    
    with overview:
        st.write('')
        left,right=st.columns([1.15,1],gap='large')
        with left:
            st.subheader('Reported performance')
            selection=st.selectbox('Measure',['Net sales','Net profit','Operating cash flow'],
                                   label_visibility='collapsed')
            key={'Net sales':'sales','Net profit':'profit','Operating cash flow':'cash'}[selection]
            values=[F[y][key]/1e6 for y in [2024,2025]]
            fig=go.Figure(go.Bar(x=['2024','2025'],y=values,width=.40,
                marker_color=['#465c79','#4ed1b0'],
                text=[f'{v:,.2f}' for v in values],textposition='outside',cliponaxis=False,
                textfont=dict(color='#e4edf8',size=13),
                hovertemplate='%{x}<br>PKR %{y:,.2f} billion<extra></extra>'))
            chart_style(fig,'PKR billions')
            fig.update_yaxes(range=[min(0,min(values)*1.4),max(values)*1.24])
            st.plotly_chart(fig,theme=None,width="stretch",
                            config={'displayModeBar':False})
        with right:
            st.subheader('Profitability comparison')
            st.caption('Gross and net margins · 2024 vs 2025')
            fig=go.Figure()
            for year,color in [(2024,'#465c79'),(2025,'#4ed1b0')]:
                fig.add_trace(go.Bar(name=str(year),orientation='h',
                    y=['Net margin','Gross margin'],
                    x=[margin(year,'profit'),margin(year,'gross')],
                    marker_color=color,texttemplate='%{x:.2f}%',
                    textposition='outside',cliponaxis=False,
                    textfont=dict(color='#e4edf8',size=12),
                    hovertemplate='%{y}: %{x:.2f}%<extra>%{fullData.name}</extra>'))
            chart_style(fig,'')
            fig.update_layout(barmode='group',bargap=.45,
                xaxis=dict(type='linear',range=[0,39],ticksuffix='%',gridcolor='#263044'),
                yaxis=dict(showgrid=False,automargin=True))
            st.plotly_chart(fig,theme=None,width="stretch",
                            config={'displayModeBar':False})
        st.markdown(f'''<div class="insights">
        <div class="insight"><strong>Margin improvement</strong>Gross margin rose
        {margin(2025,'gross')-margin(2024,'gross'):.2f} percentage points despite lower sales.</div>
        <div class="insight"><strong>Cash-flow recovery</strong>Operating cash flow moved
        from PKR −3.95bn to PKR 27.86bn.</div>
        <div class="insight"><strong>Liquidity context</strong>Current assets cover
        {B['assets']/B['liabilities']*100:.1f}% of current liabilities.</div></div>''',unsafe_allow_html=True)
        st.caption('Calculated observations from annual results · Use Report search for local AI answers.')
    
    rows=[('Net sales','sales',161),('Gross profit','gross',161),
          ('Profit for the year','profit',161),('Current assets','assets',160),
          ('Current liabilities','liabilities',160),('Operating cash flow','cash',162),
          ('Earnings per share','eps',161)]
    table=pd.DataFrame([{'Item':label,'2024':A[key],'2025':B[key],
           'Unit':'PKR/share' if key=='eps' else 'PKR thousands','PDF page':page}
           for label,key,page in rows])
    with statements:
        st.subheader('Consolidated financial figures')
        st.caption('2024 comparative figures as presented in the 2025 annual report.')
        st.dataframe(table.style.format({'2024':'{:,.2f}','2025':'{:,.2f}'}),
                     hide_index=True,width="stretch")
        st.download_button('Export figures · CSV',table.to_csv(index=False).encode('utf-8'),
                           file_name='EFERT_consolidated_financials.csv',mime='text/csv')
    with evidence:
        st.subheader('Trace each figure to its source')
        st.markdown('''**EFERT Annual Report 2025 — consolidated financial statements**

| PDF page | Evidence |
|---|---|
| 160 | Financial position: current assets and liabilities |
| 161 | Profit or loss: sales, profits and EPS |
| 162 | Cash-flow statement |

PDF page numbers differ from printed report pages. Figures were manually transcribed.
''')
        with st.expander('Calculation methods'):
            st.markdown('''- Growth = (2025 ÷ 2024 − 1) × 100.
- Gross or net margin = corresponding profit ÷ net sales × 100.
- Current ratio = current assets ÷ current liabilities.
- PKR billions = reported PKR thousands ÷ 1,000,000.
- pp means percentage points.''')
        report=ROOT/'data'/'reports'/'EFERT_Annual_Report_2025.pdf'
        if report.exists():
            st.download_button('Open source report · Download PDF',report.read_bytes(),
                               file_name=report.name,mime='application/pdf')
        else:
            st.caption('Place the source PDF in data/reports to enable its download.')
    
    with report_search:
        st.subheader("Search and ask the annual report")
        st.caption("Search by keywords, then optionally generate an answer from the retrieved extracts.")
        page_filters = {
            "Consolidated main statements": {160, 161, 162},
            "Company-only main statements": {196, 197, 198},
            "Entire report": None,
        }
        with st.form("report_search_form"):
            scope = st.selectbox("Search scope", list(page_filters))
            query = st.text_input("Search keywords", placeholder="finance cost")
            question = st.text_input(
                "Question for AI (optional)",
                placeholder="What was the consolidated finance cost in 2025?",
            )
            generate = st.checkbox("Generate an AI answer", value=False)
            submitted = st.form_submit_button("Search / answer")
    
        if submitted:
            # Replace the previous submission so stale answers cannot survive a new search.
            saved = {"query": query.strip(), "question": question.strip(),
                     "scope": scope, "results": [], "answer": None, "error": None}
            st.session_state["report_submission"] = saved
            report_text = ROOT / "data" / "processed" / "EFERT_2025_pages.txt"
            if not saved["query"]:
                saved["error"] = "Enter search keywords first."
            elif scope != "Consolidated main statements" and not report_text.exists():
                saved["error"] = "Missing file: data/processed/EFERT_2025_pages.txt"
            else:
                try:
                    with st.spinner("Searching the report..."):
                        if scope == "Consolidated main statements":
                            statements_json = (
                                ROOT / "data" / "processed"
                                / "EFERT_2025_statements.json"
                            )
                            saved["results"] = search_statements(
                                statements_json,
                                saved["query"],
                            )
                        else:
                            saved["results"] = search_report(
                                report_text,
                                saved["query"],
                                allowed_pages=page_filters[scope],
                            )
                except (OSError, ValueError, KeyError, TypeError) as exc:
                    saved["error"] = f"Could not read the report: {exc}"
                if generate and saved["results"]:
                    if not saved["question"]:
                        saved["error"] = "Search completed. Enter an AI question and submit again."
                    else:
                        try:
                            with st.spinner("Generating a local AI answer. This may take a moment..."):
                                saved["answer"] = answer_from_extracts(
                                    "Selected scope: " + scope + "\n" + saved["question"],
                                    saved["results"][:3],
                                )
                        except (RuntimeError, ValueError) as exc:
                            saved["error"] = str(exc)
    
        saved = st.session_state.get("report_submission")
        if saved:
            st.caption(
                f"Last submitted search: {saved['query']} · Scope: {saved['scope']}"
            )
            if saved["error"]:
                st.error(saved["error"])
            if saved["answer"]:
                st.subheader("AI answer")
                st.write("Question:", saved["question"])
                st.markdown(saved["answer"])
                pages = ", ".join(str(r["page"]) for r in saved["results"][:3])
                st.caption(f"Extracts sent to Qwen3 1.7B: PDF pages {pages}.")
                st.warning(
                    "AI-generated answer: verify figures, units and citations against the PDF. "
                    "A citation does not automatically verify a claim."
                )
            if saved["results"]:
                st.subheader("Retrieved evidence")
                st.caption(
                    "Keyword matches. The AI receives only the first three extracts. "
                    "Tables and side-by-side pages may have mixed reading order."
                )
                for i, result in enumerate(saved["results"], 1):
                    with st.expander(
                        f"{i}. EFERT Annual Report 2025 · PDF page {result['page']} · {result.get('side', 'extract')}",
                        expanded=(i == 1),
                    ):
                        st.text(result["text"])
                        if result.get("font_warning"):
                            st.caption("Font-extraction errors detected; check the original PDF.")
            elif not saved["error"]:
                st.info(
                    "No keyword matches found. Try a shorter phrase or a different scope. "
                    "This does not prove the information is absent."
                )
    
    st.markdown('<div class="foot">EFERT · Annual report 2025 · Historical financial results'
                ' &nbsp; | &nbsp; Share prices and insider disclosures are not connected yet.</div>',
                unsafe_allow_html=True)
    
    
    with analyst_report:
        st.subheader('Automatic analyst report')
        st.caption('Calculated from the mapped annual figures. No model or paid API is needed for this report.')
        try:
            research = build_analyst_report(financial_data)
            st.markdown(f"**{research['title']}**")
            st.caption(research['subtitle'])
            render_ratio_comparison(financial_data)
            for heading,paragraphs in research['sections']:
                st.markdown(f'### {heading}')
                render_report_paragraphs(heading, paragraphs, research.get("calculation_data"))
            try:
                pdf_bytes=analyst_pdf(research)
            except ImportError:
                st.info('PDF export requires ReportLab. Install it with: python -m pip install reportlab')
            else:
                st.download_button('Download analyst report · PDF',pdf_bytes,
                    file_name=f'{symbol}_{research["current"]}_analyst_report.pdf',mime='application/pdf')
        except (ValueError,KeyError,TypeError,ZeroDivisionError) as exc:
            st.error(f'Report unavailable: review the source mapping. {exc}')
