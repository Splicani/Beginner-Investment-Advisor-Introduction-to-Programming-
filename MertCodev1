# universe_config.py
# Full pipeline: predefined universes + data fetch + filtering + scoring +
# questionnaire + interactive CLI

import time
import yfinance as yf
from typing import List, Dict, Tuple, Any

# 1. Predefined asset universe per region and asset class
#ASSET_UNIVERSE: Dict[str, Dict[str, List[str]]] = {
    #"Europe": {
        #"etf":    ["IEUR.DE", "VWCE.DE", "EXW1.DE", "DBX1.DE", "CSPX.DE",
                   #"XESC.DE", "SXR8.DE", "EUNL.DE", "XMWO.DE", "EUN2.DE"],
        #"bonds":  ["EBND.DE", "EUNA.DE", "BND.DE", "AGGG.DE", "XG7S.DE",
                   #"IBCI.DE", "IBGS.DE", "XDWD.DE", "VETY.DE", "DBEF.DE"],
        #"stocks": ["SAP.DE", "ASML.AS", "LIN.DE", "NOVO-B.CO", "OR.PA",
                   #"RDSA.AS", "SIE.DE", "AD.AS", "NESN.SW", "VIV.PA"]
    #},
    #"North America": {
        #"etf":    ["SPY", "QQQ", "VTI", "IVV", "DIA", "IWM", "XLF", "XLK", "XLV", "VOO"],
        #"bonds":  ["AGG", "BND", "TLT", "LQD", "HYG", "BNDX", "MBB", "TIP", "SHY", "EMB"],
        #"stocks": ["AAPL", "MSFT", "AMZN", "GOOGL", "JPM", "XOM", "TSLA", "JNJ", "BRK-B", "META"]
    #},
    #"Emerging Markets": {
        #"etf":    ["EEM", "IEMG", "VWO", "SCHE.DE", "XMMC.DE", "EEMA", "EEMV", "CEMB.DE", "GMMB.DE", "GML.DE"],
        #"bonds":  ["EMB", "VWOB", "IGOV", "PCY", "EMLC", "EMHY", "ILTB", "FLQE.DE", "SCHE.DE", "EIRL.DE"],
        #"stocks": ["BABA", "TSM", "TCS.NS", "INFY.NS", "VALE3.SA", "NIO", "HDFCBANK.NS", "TCEHY", "005930.KS", "601318.SS"]
    #}
#}

ASSET_UNIVERSE: Dict[str, Dict[str, List[str]]] = {
    "Europe": {
        "etf":    ["IEUR.DE", "VWCE.DE", "EXW1.DE", "DBX1.DE", "CSPX.DE",
                   "XESC.DE", "SXR8.DE", "EUNL.DE", "XMWO.DE", "EUN2.DE"],
        "bonds":  ["EBND.DE", "EUNA.DE", "BND.DE", "AGGG.DE", "XG7S.DE",
                   "IBCI.DE", "IBGS.DE", "XDWD.DE", "VETY.DE", "DBEF.DE"],
        "stocks": ["SAP.DE", "ASML.AS", "LIN.DE", "NOVO-B.CO", "OR.PA",
                   "RDSA.AS", "SIE.DE", "AD.AS", "NESN.SW", "VIV.PA"]
    },
    "North America": {
        "etf":    ["SPY", "QQQ", "VTI", "IVV", "DIA", "IWM", "XLF", "XLK", "XLV", "VOO"],
        "bonds":  ["AGG", "BND", "TLT", "LQD", "HYG", "BNDX", "MBB", "TIP", "SHY", "EMB"],
        "stocks": ["AAPL", "MSFT", "AMZN", "GOOGL", "JPM", "XOM", "TSLA", "JNJ", "BRK-B", "META"]
    },
    "Emerging Markets": {
        "etf": [
            "EEM",       # iShares MSCI Emerging Markets ETF
            "VWO",       # Vanguard FTSE Emerging Markets ETF
            "IEMG",      # iShares Core MSCI Emerging Markets ETF
            "EMQQ",      # EMQQ The Emerging Markets Internet ETF
            "EEMX",      # SPDR MSCI Emerging Markets Fossil Fuel Reserves Free ETF
            "SCHE",      # Schwab Emerging Markets Equity ETF
            "XMME.DE",   # Xtrackers MSCI Emerging Markets UCITS ETF 1C
            "EEMS",      # iShares MSCI Emerging Markets Small‑Cap ETF
            "EMXC",      # iShares MSCI Emerging Markets ex China ETF
            "HMEF.L"     # HSBC MSCI Emerging Markets UCITS ETF (LSE)
        ],
        "bonds":  ["EMB", "VWOB", "IGOV", "PCY", "EMLC", "EMHY", "ILTB", "FLQE.DE", "SCHE.DE", "EIRL.DE"],
        "stocks": ["BABA", "TSM", "TCS.NS", "INFY.NS", "VALE3.SA", "NIO", "HDFCBANK.NS", "TCEHY", "005930.KS", "601318.SS"]
    }
}

# 2. Mapping region and risk level to profile name & primary ETF
REGION_RISK_ETF: Dict[str, Dict[int, Tuple[str, str]]] = {
    "Europe":          {1: ("Defensive", "EBND.DE"), 3: ("Balanced", "IEUR.DE"), 5: ("Growth", "IEUS.DE")},
    "North America":   {1: ("Defensive", "SHY"),      3: ("Balanced", "SPY"),      5: ("Growth", "IWM")},
    "Emerging Markets":{1: ("Defensive", "EMB"),      3: ("Balanced", "IEMG"),     5: ("Growth", "EEMS")}
}

# 3. Define risk profiles: weights and hard filters per risk level
RISK_PROFILE = {
    1: {  # Defensive
        "weights": {"value": 30, "yield": 30, "growth": 10, "risk": 20, "esg": 10},
        "filters": {"trailingPE": (None, 20), "dividendYield": (0.02, None), "beta": (None, 1.0)}
    },
    3: {  # Balanced
        "weights": {"value": 20, "yield": 20, "growth": 30, "risk": 20, "esg": 10},
        "filters": {"trailingPE": (None, 25), "dividendYield": (0.01, None), "beta": (None, 1.2)}
    },
    5: {  # Growth
        "weights": {"value": 10, "yield": 10, "growth": 40, "risk": 30, "esg": 10},
        "filters": {"trailingPE": (None, 30), "dividendYield": (None, None), "beta": (1.0, None)}
    }
}

ASSET_CLASSES = ["etf", "bonds", "stocks"]

# 4. Helper to get universe tickers
def get_user_universe(region: str, asset_class: str) -> List[str]:
    if region == "Any":
        combined = []
        for reg in ASSET_UNIVERSE:
            combined += ASSET_UNIVERSE[reg].get(asset_class, [])
        return combined
    return ASSET_UNIVERSE.get(region, {}).get(asset_class, [])

# 5. Helper to get primary ETF
def get_region_risk_etf(region: str, risk_level: int) -> Dict[str, str]:
    if region == "Any":
        return {"profile": "Balanced", "ticker": "EUNL.DE"}
    profile, ticker = REGION_RISK_ETF.get(region, {}).get(risk_level, (None, None))
    return {"profile": profile, "ticker": ticker}

# 6. Fetch metrics in batch from Yahoo Finance
def fetch_batch_metrics(tickers: List[str]) -> List[Dict[str, Any]]:
    yfobj = yf.Tickers(" ".join(tickers))
    results = []
    for t in tickers:
        info = {}
        try:
            info = yfobj.tickers[t].info
        except Exception:
            pass
        results.append({
            "ticker": t,
            "marketCap": info.get("marketCap", 0),
            "trailingPE": info.get("trailingPE"),
            "dividendYield": info.get("dividendYield"),
            "beta": info.get("beta"),
            # placeholders for growth and esg
            "revenueGrowth": info.get("revenueGrowth"),
            "earningsGrowth": info.get("earningsQuarterlyGrowth"),
            "esgScore": None
        })
    return results

# 7. Apply hard filters
def apply_filters(items: List[Dict[str, Any]], filters: Dict[str, Tuple[Any, Any]]) -> List[Dict[str, Any]]:
    def passes(item):
        for key, (mn, mx) in filters.items():
            val = item.get(key)
            if val is None:
                continue
            if mn is not None and val < mn:
                return False
            if mx is not None and val > mx:
                return False
        return True
    return [itm for itm in items if passes(itm)]

# 8. Score single item
def score_item(item: Dict[str, Any], weights: Dict[str, float]) -> float:
    # normalize PE (lower is better)
    pe = item.get("trailingPE") or 0
    norm_value = max(0, min(1, (30 - pe) / 30))
    # yield (higher is better, 5% maps to 1)
    dy = item.get("dividendYield") or 0
    norm_yield = min(1, dy / 0.05)
    # growth (capped at 1)
    gr = item.get("revenueGrowth") or 0
    norm_growth = max(0, min(1, gr))
    # risk (beta inverted around 1.5)
    beta = item.get("beta") or 1
    norm_risk = max(0, min(1, (1.5 - beta) / 1.5))
    # esg placeholder
    esg = item.get("esgScore") or 0.5
    score = (
        norm_value * weights["value"] +
        norm_yield * weights["yield"] +
        norm_growth * weights["growth"] +
        norm_risk * weights["risk"] +
        esg * weights["esg"]
    )
    return score

# 9. Map to recommendations
def map_user_to_recommendations(region: str, asset_class: str, risk_level: int) -> List[Dict[str, Any]]:
    tickers = get_user_universe(region, asset_class)
    raw = fetch_batch_metrics(tickers)
    cfg = RISK_PROFILE[risk_level]
    filtered = apply_filters(raw, cfg["filters"])
    scored = []
    for itm in filtered:
        sc = score_item(itm, cfg["weights"])
        itm["score"] = sc
        scored.append(itm)
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored

# 10. Questionnaire definition
QUESTIONNAIRE = [
    {"id": 0, "text": "What is your primary investment objective?",
     "options": ["Wealth accumulation","Regular income","Capital preservation","Saving for a specific goal"]},
    {"id": 1, "text": "Over what period do you plan to keep your money invested?",
     "options": ["<1 year","1-3 years","3-5 years","5-10 years",">10 years"]},
    {"id": 2, "text": "How comfortable are you with market ups and downs?",
     "options": ["Very uncomfortable","Somewhat uncomfortable","Neutral","Somewhat comfortable","Very comfortable"]},
    {"id": 3, "text": "If your portfolio lost 20% in a year, what would you do?",
     "options": ["Sell everything","Sell some","Do nothing","Buy more"]},
    {"id": 4, "text": "What is the minimum annual return you expect?",
     "options": ["<2%","2-5%","5-8%","8-12%",">12%"]},
    {"id": 5, "text": "How important is quick access to your money?",
     "options": ["Very important","Somewhat important","Not very important","Not important at all"]},
    {"id": 6, "text": "How much investing experience do you have?",
     "options": ["None","<1 year","1-3 years",">3 years"]},
    {"id": 7, "text": "What percentage of your savings will you invest?",
     "options": ["<10%","10-25%","25-50%","50-75%",">75%"]},
    {"id": 8, "text": "Which best describes your risk vs reward?",
     "options": ["Protect capital","Balanced","Accept losses for gains","Seek maximum growth"]},
    {"id": 9, "text": "How stable do you expect your income to be?",
     "options": ["Very stable","Somewhat stable","Uncertain","Likely to decrease"]},
    {"id":10, "text": "Do you anticipate any major expenses in the next three years?",
     "options": ["Yes","No"]},
    {"id":11, "text": "What percentage of your assets is in cash now?",
     "options": ["None","<10%","10-25%","25-50%",">50%"]},
    {"id":12, "text": "If an investment underperforms for six months, what would you do?",
     "options": ["Sell immediately","Re-evaluate","Hold through","Buy more"]},
    {"id":13, "text": "Are you interested in ESG-focused investments?",
     "options": ["Yes","No","Unsure"]},
    {"id":14, "text": "Would you consider using margin or leverage?",
     "options": ["Never","Only if recommended","Yes, comfortable"]}
]

# 11. Map raw answers to profile
def map_answers_to_profile(ans: Dict[int, int]) -> Dict[str, Any]:
    profile = {}
    profile["objective"]          = QUESTIONNAIRE[0]["options"][ans[0]]
    profile["time_horizon"]       = QUESTIONNAIRE[1]["options"][ans[1]]
    profile["risk_tolerance"]     = QUESTIONNAIRE[2]["options"][ans[2]]
    profile["behavioral_reaction"]= QUESTIONNAIRE[3]["options"][ans[3]]
    profile["return_expectation"] = QUESTIONNAIRE[4]["options"][ans[4]]
    profile["liquidity_need"]     = QUESTIONNAIRE[5]["options"][ans[5]]
    profile["experience"]         = QUESTIONNAIRE[6]["options"][ans[6]]
    profile["investment_capacity"]= QUESTIONNAIRE[7]["options"][ans[7]]
    profile["risk_philosophy"]    = QUESTIONNAIRE[8]["options"][ans[8]]
    profile["income_stability"]   = QUESTIONNAIRE[9]["options"][ans[9]]
    profile["upcoming_expenses"]  = QUESTIONNAIRE[10]["options"][ans[10]]
    profile["cash_allocation"]    = QUESTIONNAIRE[11]["options"][ans[11]]
    profile["loss_persistence"]   = QUESTIONNAIRE[12]["options"][ans[12]]
    profile["esg_preference"]     = QUESTIONNAIRE[13]["options"][ans[13]]
    profile["leverage_comfort"]   = QUESTIONNAIRE[14]["options"][ans[14]]
    return profile

# 12. Derive asset class automatically
def derive_asset_class(profile: Dict[str, Any]) -> str:
    rt   = profile["risk_tolerance"]
    rexp = profile["return_expectation"]
    if rt in ["Very uncomfortable","Somewhat uncomfortable"] or rexp in ["<2%","2-5%"]:
        return "bonds"
    if rt in ["Somewhat comfortable","Neutral"] or rexp in ["5-8%","8-12%"]:
        return "etf"
    return "stocks"

# 13. PRODUCT_INFO mapping for final output
PRODUCT_INFO: Dict[str, Tuple[str, str]] = {
    # ETFs
    "IEUR.DE": ("iShares Core MSCI Europe UCITS ETF", "ETF"),
    "VWCE.DE": ("Vanguard FTSE All-World UCITS ETF",    "ETF"),
    "SPY":     ("SPDR S&P 500 ETF Trust",               "ETF"),
    "QQQ":     ("Invesco QQQ Trust",                    "ETF"),
    "EEM":     ("iShares MSCI Emerging Markets ETF",    "ETF"),
    # Bonds
    "EBND.DE": ("iShares Core € Govt Bond UCITS ETF",   "Bond ETF"),
    "SHY":     ("iShares 1-3 Year Treasury Bond ETF",   "Bond ETF"),
    "EMB":     ("iShares J.P. Morgan USD Emerging Mkts", "Bond ETF"),
    # Stocks
    "AAPL":    ("Apple Inc.",                            "Stock"),
    "SAP.DE":  ("SAP SE",                                "Stock"),
    # (add the rest similarly)
}

# 14. Generate recommendation object
def generate_recommendation(
    answers: Dict[int, int],
    region: str,
    asset_class: str
) -> Dict[str, Any]:
    profile    = map_answers_to_profile(answers)
    # risk level from question 2
    rt_choice  = answers[2]
    if rt_choice <= 1:
        risk_level = 1
    elif rt_choice == 2:
        risk_level = 3
    else:
        risk_level = 5

    primary    = get_region_risk_etf(region, risk_level)
    recs       = map_user_to_recommendations(region, asset_class, risk_level)

    return {
        "investor_profile": profile,
        "risk_level":       risk_level,
        "primary_etf":      primary,
        "recommendations":  recs
    }

# 15. Interactive CLI
if __name__ == "__main__":
    print("Welcome to the Beginner Investment Advisor!\n")
    answers = {}
    for q in QUESTIONNAIRE:
        print(q["text"])
        for idx, opt in enumerate(q["options"]):
            print(f"  {idx}: {opt}")
        while True:
            try:
                choice = int(input(f"Select (0-{len(q['options'])-1}): "))
                if 0 <= choice < len(q["options"]):
                    answers[q["id"]] = choice
                    break
            except ValueError:
                continue
        print()

    profile     = map_answers_to_profile(answers)
    asset_class = derive_asset_class(profile)
    print(f"Detected asset class: {asset_class}\n")

    regions = list(ASSET_UNIVERSE.keys()) + ["Any"]
    print("Choose a region (or Any):")
    for idx, r in enumerate(regions):
        print(f"  {idx}: {r}")
    while True:
        try:
            r_idx = int(input(f"Select (0-{len(regions)-1}): "))
            if 0 <= r_idx < len(regions):
                region = regions[r_idx]
                break
        except ValueError:
            continue
    print()

    result = generate_recommendation(answers, region, asset_class)

    # Print investor profile
    print("Your Investor Profile:", result["investor_profile"])
    print(f"Risk Level: {result['risk_level']} ({get_region_risk_etf(region, result['risk_level'])['profile']})\n")

    # Primary recommendation
    pef = result["primary_etf"]["ticker"]
    name, cls = PRODUCT_INFO.get(pef, (pef, asset_class.capitalize()))
    print(f"Primary Recommendation: {name} ({cls}) [{pef}]\n")

    # Top 5 recommendations
    print("Top 5 Recommendations:")
    for itm in result["recommendations"][:5]:
        tkr = itm["ticker"]
        name, cls = PRODUCT_INFO.get(tkr, (tkr, asset_class.capitalize()))
        print(
            f"- {name} ({cls}) [{tkr}]: "
            f"Price={itm.get('price','N/A')}, "
            f"PE={itm.get('trailingPE','N/A')}, "
            f"DY={itm.get('dividendYield','N/A')}, "
            f"Score={itm.get('score',0):.2f}"
        )
