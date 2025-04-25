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
def score_item(it,w):
    ev=it.get("ev_ebitda") or 30
    f =it.get("fcf_yield") or 0
    v =it.get("volatility") or 0.40
    e =it.get("esgScore")   or 50
    ne=max(0,min(1,(30-ev)/30))
    nf=min(1,f/0.05)
    nv=max(0,min(1,(0.40-v)/0.40))
    ns=max(0,min(1,e/100))
    return ne*w["ev_ebitda"]+nf*w["fcf_yield"]+nv*w["volatility"]+ns*w["esgScore"]

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
    return {q["id"]:QUESTIONNAIRE[q["id"]]["options"][a[q["id"]]] for q in QUESTIONNAIRE}

# 12. Composite risk level
def derive_risk_level(a):
    w={1:0.20,2:0.30,4:0.20,7:0.15,8:0.15}
    s1,s2,s4,s7,s8=a[1]/4,a[2]/4,a[4]/4,a[7]/4,a[8]/3
    comp=s1*w[1]+s2*w[2]+s4*w[4]+s7*w[7]+s8*w[8]
    if comp<0.20: return 1
    if comp<0.40: return 2
    if comp<0.60: return 3
    if comp<0.80: return 4
    return 5

# 13. Allocation overrides
def get_allowed_allocations(a):
    rl=derive_risk_level(a)
    alloc=RISK_ALLOCATION[rl].copy()
    if a[1]==0:
        return {"bonds":1.0,"etf":0.0,"stocks":0.0}
    if a[6]<=1:
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
    # … expand for all tickers …
}

# 16. Generate recommendation
def generate_recommendation(ans,region):
    profile=map_answers_to_profile(ans)
    esg_only=(profile[13]=="Yes")
    rl=derive_risk_level(ans)
    primary=get_region_risk_etf(region,rl)
    alloc=get_allowed_allocations(ans)

    combined=[]
    for cls,w in alloc.items():
        if w<=0: continue
        recs=map_user_to_recommendations(region,cls,rl,esg_only)
        for r in recs:
            r["asset_class"],r["class_weight"]=cls,w
            r["final_score"]=r["score"]*w
        combined+=recs

    final=sorted(combined,key=lambda x:x["final_score"],reverse=True)
    return {
        "investor_profile":profile,
        "risk_level":rl,
        "primary_etf":primary,
        "recommendations":final
    }

# 17. Interactive CLI
if __name__=="__main__":
    print("Welcome to the Beginner Investment Advisor!\n")
    answers={}
    for q in QUESTIONNAIRE:
        print(q["text"])
        for i,opt in enumerate(q["options"]):
            print(f"  {i}: {opt}")
        while True:
            try:
                c=int(input(f"Select (0-{len(q['options'])-1}): "))
                if 0<=c<len(q["options"]):
                    answers[q["id"]]=c
                    break
            except ValueError:
                pass
        print()

    profile=map_answers_to_profile(answers)
    print("Your Investor Profile:",profile)

    regions=list(ASSET_UNIVERSE.keys())+["Any"]
    print("\nChoose a region (or Any):")
    for i,r in enumerate(regions):
        print(f"  {i}: {r}")
    while True:
        try:
            ri=int(input(f"Select (0-{len(regions)-1}): "))
            if 0<=ri<len(regions):
                region=regions[ri]
                break
        except ValueError:
            pass
    print()

    result=generate_recommendation(answers,region)
    rl=result["risk_level"]
    # print correct global risk-bucket name
    print(f"Risk Level: {rl} ({RISK_LEVEL_NAME[rl]})")

    pef=result["primary_etf"]["ticker"]
    name,cls=PRODUCT_INFO.get(pef,(pef,"ETF"))
    print(f"Primary Recommendation: {name} ({cls}) [{pef}]\n")

    print("Top 5 Recommendations:")
    for itm in result["recommendations"][:5]:
        t=itm["ticker"]
        name,cls=PRODUCT_INFO.get(t,(t,itm["asset_class"].capitalize()))
        ev=itm.get("ev_ebitda");evs=f"{ev:.2f}" if ev else "N/A"
        fcf=itm.get("fcf_yield");fcfs=f"{fcf:.2%}" if fcf else "N/A"
        vol=itm.get("volatility");vols=f"{vol:.2%}" if vol else "N/A"
        esg=itm.get("esgScore");esgs=f"{esg:.0f}" if esg else "N/A"
        fs=itm.get("final_score",0)
        print(f"- {name} ({cls}) [{t}]: EV/EBITDA={evs}, FCF Yield={fcfs}, Vol={vols}, ESG={esgs}, Score={fs:.2f}")
