import time
import yfinance as yf
from typing import List, Dict, Any, Tuple
import jinja2
import weasyprint
import smtplib
from email.message import EmailMessage

# === CONFIGURATION ===
# Risk bucket labels
tick_labels: Dict[int, str] = {
    1: "Defensive",
    2: "Conservative",
    3: "Balanced",
    4: "Growth Tilt",
    5: "Aggressive"
}

# Predefined asset universe (stub: fill with your tickers)
ASSET_UNIVERSE: Dict[str, Dict[str, List[str]]] = {
    # ... your region -> class -> tickers mapping ...
}

# Realistic risk profile settings
RISK_PROFILE: Dict[int, Dict[str, Any]] = {
    1: {"weights": {"ev_ebitda": 30, "fcf_yield": 30, "volatility": 20, "esgScore": 20},
        "filters": {"ev_ebitda": (None, 12), "fcf_yield": (0.02, None), "volatility": (None, 0.15), "esgScore": (50, None)}},
    2: {"weights": {"ev_ebitda": 25, "fcf_yield": 30, "volatility": 20, "esgScore": 25},
        "filters": {"ev_ebitda": (None, 15), "fcf_yield": (0.03, None), "volatility": (None, 0.20), "esgScore": (40, None)}},
    3: {"weights": {"ev_ebitda": 20, "fcf_yield": 25, "volatility": 25, "esgScore": 30},
        "filters": {"ev_ebitda": (None, 18), "fcf_yield": (0.04, None), "volatility": (None, 0.25), "esgScore": (30, None)}},
    4: {"weights": {"ev_ebitda": 15, "fcf_yield": 20, "volatility": 30, "esgScore": 35},
        "filters": {"ev_ebitda": (None, 25), "fcf_yield": (0.05, None), "volatility": (None, 0.30), "esgScore": (20, None)}},
    5: {"weights": {"ev_ebitda": 10, "fcf_yield": 15, "volatility": 40, "esgScore": 35},
        "filters": {"ev_ebitda": (None, None), "fcf_yield": (0.05, None), "volatility": (None, 0.35), "esgScore": (None, None)}}
}

# Questionnaire for profile mapping
QUESTIONNAIRE: List[Dict[str, Any]] = [
    {"id": 0, "text": "Primary investment objective?", "options": ["Wealth accumulation", "Regular income", "Capital preservation", "Saving for a goal"]},
    {"id": 1, "text": "Investment horizon?", "options": ["<1y", "1-3y", "3-5y", "5-10y", ">10y"]},
    {"id": 2, "text": "Comfort with market ups/downs?", "options": ["Very uncomfortable", "Somewhat uncomfortable", "Neutral", "Somewhat comfortable", "Very comfortable"]},
    {"id": 4, "text": "Minimum expected annual return?", "options": ["<2%", "2-5%", "5-8%", "8-12%", ">12%"]},
    {"id": 7, "text": "% of savings to invest?", "options": ["<10%", "10-25%", "25-50%", "50-75%", ">75%"]},
    {"id": 8, "text": "Risk vs reward?", "options": ["Protect capital", "Balanced", "Accept losses for gains", "Seek max growth"]},
    {"id": 13, "text": "Interested in ESG?", "options": ["Yes", "No", "Unsure"]}
]

PRODUCT_INFO: Dict[str, Tuple[str, str]] = {
    # ticker -> (name, class)
}

# === PROFILE MAPPING ===
def map_answers_to_profile(answers: Dict[int, int]) -> Dict[str, Any]:
    return {q['text']: q['options'][answers[q['id']]] for q in QUESTIONNAIRE}

# Composite risk level from key questions
def derive_risk_level(answers: Dict[int, int]) -> int:
    # weighted: horizon(1), comfort(2), return(4), allocation(7), risk_reward(8)
    w = {1: 0.2, 2: 0.3, 4: 0.2, 7: 0.15, 8: 0.15}
    s = sum((answers[i] / (len(next(q for q in QUESTIONNAIRE if q['id']==i)['options'])-1)) * w[i]
            for i in w)
    return min(5, int(s * 5) + 1)

def get_allowed_allocations(answers: Dict[int, int], rl: int) -> Dict[str, float]:
    alloc = RISK_PROFILE[rl]['weights']  # reuse weights keys as classes stub
    # example override: short horizon -> bonds only
    if answers[1] == 0:
        return {'bonds': 1.0, 'etf': 0.0, 'stocks': 0.0}
    # default equal split
    return {'bonds': 0.3, 'etf': 0.4, 'stocks': 0.3}

def get_region_risk_etf(region: str, rl: int) -> Dict[str, Any]:
    # stub: return primary ETF per region & risk
    return {'ticker': 'SPY', 'profile': tick_labels[rl]}

# === METRICS & SCORING ===
def fetch_metrics(ticker: str) -> Dict[str, Any]:
    tk = yf.Ticker(ticker)
    info = tk.info or {}
    ev = info.get('enterpriseValue')
    ebitda = info.get('ebitda')
    ev_ebitda = ev/ebitda if ev and ebitda else None
    fcf = info.get('freeCashflow')
    mcap = info.get('marketCap')
    fcf_yield = fcf/mcap if fcf and mcap else None
    vol = None
    try:
        hist = tk.history(period='3mo', interval='1d')['Close'].pct_change().dropna()
        vol = hist.std() * (252**0.5)
    except:
        pass
    esg = info.get('esgScore', 50)
    return {'ticker': ticker, 'ev_ebitda': ev_ebitda, 'fcf_yield': fcf_yield, 'volatility': vol, 'esgScore': esg}

def apply_filters(items: List[Dict[str, Any]], flt: Dict[str, Tuple[Any, Any]]) -> List[Dict[str, Any]]:
    def keep(it):
        for k, (mn, mx) in flt.items():
            v = it.get(k)
            if v is None or (mn is not None and v < mn) or (mx is not None and v > mx):
                return False
        return True
    return [it for it in items if keep(it)]

def normalize(v: float, mn: float, mx: float) -> float:
    if v is None: return 0.0
    if mx is not None and v > mx: v = mx
    if mn is not None and v < mn: v = mn
    return (v - (mn or 0)) / ((mx - (mn or 0)) or 1)

def score_item(item: Dict[str, Any], cfg: Dict[str, Any]) -> Tuple[float, Dict[str, str]]:
    w = cfg['weights']; flt = cfg['filters']
    total = 0.0; reasons = {}
    # EV/EBITDA
    ev = item['ev_ebitda']; mn, mx = flt['ev_ebitda']
    ev_s = normalize(ev, 0, mx); total += ev_s*w['ev_ebitda']
    reasons['EV/EBITDA'] = f"EV/EBITDA={ev:.2f} normalized to {ev_s:.2f}."
    # FCF Yield
    fcf = item['fcf_yield']; mn, mx = flt['fcf_yield']
    f_s = normalize(fcf, mn, mx); total += f_s*w['fcf_yield']
    reasons['FCF Yield'] = f"FCF Yield={fcf:.2%} normalized to {f_s:.2f}."
    # Volatility (lower better)
    vol = item['volatility']; mn, mx = flt['volatility']
    v_s = normalize((mx or vol) - (vol or 0), 0, mx); total += v_s*w['volatility']
    reasons['Volatility'] = f"Volatility={vol:.2%} normalized to {v_s:.2f} (lower is better)."
    # ESG
    esg = item['esgScore']; mn, _ = flt['esgScore']
    e_s = normalize(esg, mn, 100); total += e_s*w['esgScore']
    reasons['ESG Score'] = f"ESG Score={esg} normalized to {e_s:.2f}."
    return total, reasons

def get_universe(region: str, asset_class: str, esg_only: bool) -> List[str]:
    tickers = []
    if region == 'Any':
        for r in ASSET_UNIVERSE: tickers.extend(ASSET_UNIVERSE[r].get(asset_class, []))
    else:
        tickers = ASSET_UNIVERSE.get(region, {}).get(asset_class, [])
    # ESG-only filter placeholder
    return tickers

# Generate top-n recommendations per class
def generate_recommendations(region: str, rl: int, esg_only: bool, asset_class: str, top_n: int=5) -> List[Dict[str, Any]]:
    tks = get_universe(region, asset_class, esg_only)
    metrics = [fetch_metrics(t) for t in tks]
    cfg = RISK_PROFILE[rl]
    flt = apply_filters(metrics, cfg['filters'])
    scored = []
    for it in flt:
        sc, reasons = score_item(it, cfg)
        scored.append({**it, 'score': sc, 'reasons': reasons})
    scored.sort(key=lambda x: x['score'], reverse=True)
    return scored[:top_n]

# Full recommendation including profile, allocations, primary ETF, and reports
def generate_full_recommendation(answers: Dict[int,int], region: str) -> Dict[str, Any]:
    profile = map_answers_to_profile(answers)
    rl = derive_risk_level(answers)
    esg_only = profile.get('Interested in ESG?') == 'Yes'
    alloc = get_allowed_allocations(answers, rl)
    primary = get_region_risk_etf(region, rl)

    all_recs = []
    for cls, w in alloc.items():
        recs = generate_recommendations(region, rl, esg_only, cls)
        for r in recs:
            r['asset_class'] = cls
            r['class_weight'] = w
            r['final_score'] = r['score'] * w
        all_recs.extend(recs)
    all_recs.sort(key=lambda x: x['final_score'], reverse=True)

    return {
        'investor_profile': profile,
        'risk_level': {'level': rl, 'label': tick_labels[rl]},
        'primary_etf': primary,
        'recommendations': all_recs
    }

# Reporting: HTML to PDF and email
REPORT_TEMPLATE = jinja2.Template("""
<h1>Investment Recommendation Report</h1>
<p>Risk Level: {{ rec.risk_level.label }} ({{ rec.risk_level.level }})</p>
<h2>Primary ETF: {{ rec.primary_etf.ticker }}</h2>
<ul>
{% for key, val in rec.investor_profile.items() %}
  <li><strong>{{ key }}:</strong> {{ val }}</li>
{% endfor %}
</ul>
<h2>Recommendations</h2>
<table border="1" cellpadding="5">
<tr><th>Ticker</th><th>Class</th><th>Score</th><th>Reasons</th></tr>
{% for it in rec.recommendations %}
<tr>
  <td>{{ it.ticker }}</td>
  <td>{{ it.asset_class }}</td>
  <td>{{ "%.2f"|format(it.final_score) }}</td>
  <td>
    <ul>
    {% for k,v in it.reasons.items() %}
      <li>{{ k }}: {{ v }}</li>
    {% endfor %}
    </ul>
  </td>
</tr>
{% endfor %}
</table>
""")

def create_pdf_report(rec: Dict[str, Any], output_path: str) -> None:
    html = REPORT_TEMPLATE.render(rec=rec)
    weasyprint.HTML(string=html).write_pdf(output_path)


def send_email_report(
    sender: str,
    recipient: str,
    subject: str,
    body: str,
    attachment_path: str
) -> None:
    msg = EmailMessage()
    msg['From'] = sender
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.set_content(body)

    with open(attachment_path, 'rb') as f:
        data = f.read()
        msg.add_attachment(data, maintype='application', subtype='pdf', filename='report.pdf')

    with smtplib.SMTP('localhost') as smtp:
        smtp.send_message(msg)
