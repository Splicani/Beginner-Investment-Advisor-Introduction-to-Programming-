# universe_config.py
# Full pipeline: predefined universes + data fetch + filtering + scoring +
# questionnaire + interactive CLI with ESG-only filtering and multi-class allocations

import time
import yfinance as yf
from typing import List, Dict, Tuple, Any

# 0. Global risk‐bucket names
RISK_LEVEL_NAME = {
    1: "Defensive",
    2: "Conservative",
    3: "Balanced",
    4: "Growth Tilt",
    5: "Aggressive"
}

# Define tick_labels for risk levels
tick_labels = {
    1: "Defensive",
    2: "Conservative",
    3: "Balanced",
    4: "Growth Tilt",
    5: "Aggressive"
}

# 1. Predefined asset universe per region and asset class (15 tickers each)
ASSET_UNIVERSE: Dict[str, Dict[str, List[str]]] = {
    "Europe": {
        "etf": [
            "IESG.L", "IUSK.DE", "IUSK.F", "IESE.AS", "IDSE.AS",
            "IEUR", "VWCE.DE", "EXW1.DE", "DBX1.DE", "CSP1.L",
            "XESC.DE", "SXR8.DE", "EUNL.DE", "IWDA.AS", "EUN2.DE"
        ],
        "bonds": [
            "GRNB.L", "EMB", "AGGG.L", "USAG.SW", "BGRN",
            "EBND.DE", "EUNA.DE", "BND", "AGG", "XG7S.DE",
            "IBCI.DE", "IBGS.DE", "XDWD.DE", "VETY.DE", "DBEF.DE"
        ],
        "stocks": [
            "ORSTED.CO", "ADS.DE", "PHIA.AS", "SIE.DE", "SAP.DE",
            "ASML.AS", "LIN.DE", "NOVO-B.CO", "OR.PA", "AD.AS",
            "NESN.SW", "VIV.PA", "BMW.DE", "SHEL.L", "SU.TO"
        ]
    },
    "North America": {
        "etf": [
            "SUSA", "ESGV", "SPYL.DE", "SPY", "QQQ",
            "VTI", "IVV", "DIA", "IWM", "XLF",
            "XLK", "XLV", "VOO", "CSP1.L", "IWDA.AS"
        ],
        "bonds": [
            "BGRN", "USAG.SW", "IGSB", "SJNK", "AGG",
            "BND", "TLT", "LQD", "HYG", "BNDX",
            "MBB", "TIP", "SHY", "EMB", "SPDR_BRE"
        ],
        "stocks": [
            "AAPL", "MSFT", "ADBE", "CRM", "JNJ",
            "AMZN", "GOOGL", "JPM", "XOM", "TSLA",
            "BRK-B", "META", "NVDA", "PG", "UNH"
        ]
    },
    "Emerging Markets": {
        "etf": [
            "ESGE", "EEMX", "EEM", "VWO", "IEMG",
            "EMQQ", "SCHE", "XMME.DE", "EEMS", "EMXC",
            "HMEF.L", "EMB", "VWOB", "IGOV", "PCY"
        ],
        "bonds": [
            "HYGD", "EMBB", "IGOV", "EMLC", "EMHY",
            "ILTB", "EMB", "VWOB", "SCHP", "TIP",
            "BGRN", "AGG", "BND", "TLT", "LQD"
        ],
        "stocks": [
            "TSM", "BABA", "INFY.NS", "TCS.NS", "VALE3.SA",
            "NIO", "HDFCBANK.NS", "TCEHY", "005930.KS", "601318.SS",
            "ITUB", "PBR", "MTN", "SU.TO", "GOLD"
        ]
    }
}

# 2. Primary ETF mapping per region & risk_level
REGION_RISK_ETF: Dict[str, Dict[int, Tuple[str, str]]] = {
    "Europe": {
        1: ("Defensive",    "EBND.DE"),
        2: ("Conservative", "EUNA.DE"),
        3: ("Balanced",     "IEUR"),
        4: ("Growth Tilt",  "EXW1.DE"),
        5: ("Aggressive",   "IWDA.AS")
    },
    "North America": {
        1: ("Defensive",    "SHY"),
        2: ("Conservative", "AGG"),
        3: ("Balanced",     "SPY"),
        4: ("Growth Tilt",  "QQQ"),
        5: ("Aggressive",   "IWM")
    },
    "Emerging Markets": {
        1: ("Defensive",    "EMB"),
        2: ("Conservative", "VWOB"),
        3: ("Balanced",     "IEMG"),
        4: ("Growth Tilt",  "EEM"),
        5: ("Aggressive",   "EEMS")
    }
}

# 3. Risk profile weights & filters
RISK_PROFILE = {
    1: {"weights": {"ev_ebitda":35,"fcf_yield":35,"volatility":20,"esgScore":10},
        "filters": {"ev_ebitda":(None,15),"volatility":(None,0.20)}},
    2: {"weights": {"ev_ebitda":30,"fcf_yield":30,"volatility":20,"esgScore":20},
        "filters": {"ev_ebitda":(None,18),"volatility":(None,0.25)}},
    3: {"weights": {"ev_ebitda":25,"fcf_yield":25,"volatility":25,"esgScore":25},
        "filters": {"ev_ebitda":(None,20),"volatility":(None,0.30)}},
    4: {"weights": {"ev_ebitda":20,"fcf_yield":30,"volatility":25,"esgScore":25},
        "filters": {"ev_ebitda":(None,25),"volatility":(None,0.35)}},
    5: {"weights": {"ev_ebitda":15,"fcf_yield":35,"volatility":25,"esgScore":25},
        "filters": {"ev_ebitda":(None,None),"volatility":(None,0.40)}}
}

# 4. Risk level → asset-class allocation
RISK_ALLOCATION = {
    1: {"bonds":1.0, "etf":0.0, "stocks":0.0},
    2: {"bonds":0.7, "etf":0.3, "stocks":0.0},
    3: {"bonds":0.0, "etf":1.0, "stocks":0.0},
    4: {"bonds":0.0, "etf":0.7, "stocks":0.3},
    5: {"bonds":0.0, "etf":0.0, "stocks":1.0}
}

ASSET_CLASSES = ["bonds","etf","stocks"]

# 5. Fetch and compute metrics
def fetch_batch_metrics(tickers: List[str]) -> List[Dict[str, Any]]:
    results=[]
    for t in tickers:
        try:
            tk       = yf.Ticker(t)
            info     = tk.info
        except:
            info     = {}
        ev, ebitda = info.get("enterpriseValue"), info.get("ebitda")
        ev_ebitda  = ev/ebitda if ev and ebitda else None
        fcf, mcap  = info.get("freeCashflow"), info.get("marketCap")
        fcf_yield  = fcf/mcap if fcf and mcap else None
        try:
            hist = tk.history(period="3mo", interval="1d")["Close"].pct_change().dropna()
            vol  = hist.std()*(252**0.5)
        except:
            vol  = None
        results.append({
            "ticker":     t,
            "ev_ebitda":  ev_ebitda,
            "fcf_yield":  fcf_yield,
            "volatility": vol,
            "esgScore":   info.get("esgScore",50)
        })
        time.sleep(0.1)
    return results

# 6. Hard filters
def apply_filters(items, filters):
    def ok(it):
        for k,(mn,mx) in filters.items():
            v=it.get(k)
            if v is None: continue
            if (mn is not None and v<mn) or (mx is not None and v>mx): return False
        return True
    return [it for it in items if ok(it)]

# 7. Scoring
def score_item(item, weights):
    ev = item.get("ev_ebitda")
    fcf = item.get("fcf_yield")
    vol = item.get("volatility")
    esg = item.get("esgScore")

    if ev is None or ev <= 0:
        ev = 20
    if fcf is None:
        fcf = 0.02
    if vol is None:
        vol = 0.3
    if esg is None:
        esg = 50

    score_ev = max(0, min(1, (20 - ev) / 15))
    score_fcf = max(0, min(1, fcf / 0.10))
    score_vol = max(0, min(1, (0.5 - vol) / 0.4))
    score_esg = max(0, min(1, esg / 100))

    total_score = (
        score_ev * weights["ev_ebitda"] +
        score_fcf * weights["fcf_yield"] +
        score_vol * weights["volatility"] +
        score_esg * weights["esgScore"]
    ) / 100

    return total_score

# 8. Universe helper
def get_user_universe(region,asset_class,esg_only):
    if region=="Any":
        full = sum((ASSET_UNIVERSE[r][asset_class] for r in ASSET_UNIVERSE),[])
    else:
        full = ASSET_UNIVERSE.get(region,{}).get(asset_class,[])
    return full[:5] if esg_only else full

# 9. Recommendations per class
def map_user_to_recommendations(region,asset_class,risk_level,esg_only):
    tks= get_user_universe(region,asset_class,esg_only)
    raw= fetch_batch_metrics(tks)
    cfg= RISK_PROFILE[risk_level]
    flt= apply_filters(raw,cfg["filters"])
    for it in flt: it["score"]=score_item(it,cfg["weights"])
    return sorted(flt,key=lambda x:x["score"],reverse=True)

# 10. Questionnaire
QUESTIONNAIRE=[
    {"id":0, "text":"What is your primary investment objective?","options":["Wealth accumulation","Regular income","Capital preservation","Saving for a specific goal"]},
    {"id":1, "text":"Over what period do you plan to keep your money invested?","options":["<1 year","1-3 years","3-5 years","5-10 years",">10 years"]},
    {"id":2, "text":"How comfortable are you with market ups and downs?","options":["Very uncomfortable","Somewhat uncomfortable","Neutral","Somewhat comfortable","Very comfortable"]},
    {"id":3, "text":"If your portfolio lost 20% in a year, what would you do?","options":["Sell everything","Sell some","Do nothing","Buy more"]},
    {"id":4, "text":"What is the minimum annual return you expect?","options":["<2%","2-5%","5-8%","8-12%",">12%"]},
    {"id":5, "text":"How important is quick access to your money?","options":["Very important","Somewhat important","Not very important","Not important at all"]},
    {"id":6, "text":"How much investing experience do you have?","options":["None","<1 year","1-3 years",">3 years"]},
    {"id":7, "text":"What percentage of your savings will you invest?","options":["<10%","10-25%","25-50%","50-75%",">75%"]},
    {"id":8, "text":"Which best describes your risk vs reward?","options":["Protect capital","Balanced","Accept losses for gains","Seek maximum growth"]},
    {"id":9, "text":"How stable do you expect your income to be?","options":["Very stable","Somewhat stable","Uncertain","Likely to decrease"]},
    {"id":10,"text":"Do you anticipate any major expenses in the next three years?","options":["Yes","No"]},
    {"id":11,"text":"What percentage of your assets is in cash now?","options":["None","<10%","10-25%","25-50%",">50%"]},
    {"id":12,"text":"If an investment underperforms for six months, what would you do?","options":["Sell immediately","Re-evaluate","Hold through","Buy more"]},
    {"id":13,"text":"Are you interested in ESG-focused investments?","options":["Yes","No","Unsure"]},
    {"id":14,"text":"Would you consider using margin or leverage?","options":["Never","Only if recommended","Yes, comfortable"]}
]

# 11. Map answers → profile
def map_answers_to_profile(a):
    profile = {}
    for q in QUESTIONNAIRE:
        qid = q["id"]
        if qid in a:
            answer_index = a[qid]
            options = q["options"]
            if 0 <= answer_index < len(options):
                profile[qid] = options[answer_index]
    return profile

# 12. Composite risk level
def derive_risk_level(a):
    required_keys = [1, 2, 4, 7, 8]
    if not all(k in a for k in required_keys):
        return 3  # Default to balanced if incomplete

    w = {1: 0.20, 2: 0.30, 4: 0.20, 7: 0.15, 8: 0.15}
    s1, s2, s4, s7, s8 = a[1]/4, a[2]/4, a[4]/4, a[7]/4, a[8]/3
    comp = s1*w[1] + s2*w[2] + s4*w[4] + s7*w[7] + s8*w[8]

    if comp < 0.20: return 1
    if comp < 0.40: return 2
    if comp < 0.60: return 3
    if comp < 0.80: return 4
    return 5

# 13. Allocation overrides
def get_allowed_allocations(a):
    rl=derive_risk_level(a)
    alloc=RISK_ALLOCATION[rl].copy()
    if a.get(1) == 0:
        return {"bonds":1.0,"etf":0.0,"stocks":0.0}
    if a.get(6, 99) <= 1:
        alloc["stocks"]=0.0
        s=alloc["bonds"]+alloc["etf"]
        if s>0:
            alloc["bonds"]/=s;alloc["etf"]/=s
    return alloc

# 14. Primary ETF
def get_region_risk_etf(region,rl):
    if region=="Any":
        return {"profile":"Balanced","ticker":"EUNL.DE"}
    p,t=REGION_RISK_ETF[region][rl]
    return {"profile":p,"ticker":t}

# 15. PRODUCT_INFO (partial; add all tickers)
PRODUCT_INFO={
    "EBND.DE":("iShares Core € Govt Bond UCITS ETF","Bond ETF"),
    "EUNA.DE":("iShares Euro Corporate Bond UCITS ETF","Bond ETF"),
    "IEUR":("iShares Core MSCI Europe ETF","ETF"),
    "SPY":("SPDR S&P 500 ETF Trust","ETF"),
    "IWM":("iShares Russell 2000 ETF","ETF"),
   
}
def generate_full_recommendation(answers):
    return generate_recommendation(answers)

def generate_recommendation(ans):
    profile = map_answers_to_profile(ans)
    esg_only = profile.get(13, "No") == "Yes"
    rl = derive_risk_level(ans)
    alloc = get_allowed_allocations(ans)

    combined = []

    for region in ["Europe", "North America", "Emerging Markets"]:
        region_products = []

        for cls, w in alloc.items():
            if w <= 0:
                continue

            recs = map_user_to_recommendations(region, cls, rl, esg_only)
            for r in recs:
                r["region"] = region
                r["asset_class"] = cls
                r["class_weight"] = w
                r["final_score"] = r["score"] * w

                if r["ticker"] not in PRODUCT_INFO:
                    try:
                        info = yf.Ticker(r["ticker"]).info
                        long_name = info.get("longName", r["ticker"])
                        sector = info.get("sector", cls.capitalize())
                        PRODUCT_INFO[r["ticker"]] = (long_name, sector)
                    except:
                        PRODUCT_INFO[r["ticker"]] = (r["ticker"], cls.capitalize())

            region_products += recs

        top_region_recs = sorted(region_products, key=lambda x: x["final_score"], reverse=True)[:2]
        combined += top_region_recs

    primary = get_region_risk_etf("Europe", rl)

    return {
        "investor_profile": profile,
        "risk_level": rl,
        "primary_etf": primary,
        "recommendations": combined
    }