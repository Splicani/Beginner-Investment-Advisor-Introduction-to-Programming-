
import time
import yfinance as yf
import random
from typing import List, Dict, Tuple, Any

# =========================================================================
# 1. GLOBAL CONSTANTS AND DEFINITIONS
# =========================================================================

# Risk level names
RISK_LEVEL_NAME = {
    1: "Defensive",
    2: "Conservative",
    3: "Balanced",
    4: "Growth Tilt",
    5: "Aggressive"
}

# Risk level labels for UI
tick_labels = {
    1: "Defensive",
    2: "Conservative",
    3: "Balanced",
    4: "Growth Tilt",
    5: "Aggressive"
}

# Define the asset classes
ASSET_CLASSES = ["bonds", "etf", "stocks"]

# Predefined asset universe per region and asset class
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

# Primary ETF mapping per region & risk_level
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

# Risk profile weights & filters
RISK_PROFILE = {
    1: {"weights": {"ev_ebitda":35,"fcf_yield":35,"volatility":20,"esgScore":10,"dividend_yield":0},
        "filters": {"ev_ebitda":(None,15),"volatility":(None,0.20)}},
    2: {"weights": {"ev_ebitda":30,"fcf_yield":30,"volatility":20,"esgScore":20,"dividend_yield":0},
        "filters": {"ev_ebitda":(None,18),"volatility":(None,0.25)}},
    3: {"weights": {"ev_ebitda":25,"fcf_yield":25,"volatility":25,"esgScore":25,"dividend_yield":0},
        "filters": {"ev_ebitda":(None,20),"volatility":(None,0.30)}},
    4: {"weights": {"ev_ebitda":20,"fcf_yield":30,"volatility":25,"esgScore":25,"dividend_yield":0},
        "filters": {"ev_ebitda":(None,25),"volatility":(None,0.35)}},
    5: {"weights": {"ev_ebitda":15,"fcf_yield":35,"volatility":25,"esgScore":25,"dividend_yield":0},
        "filters": {"ev_ebitda":(None,None),"volatility":(None,0.40)}}
}

# ESG base scores for regions and asset classes
ESG_BASE_SCORES = {
    "Europe": {
        "etf": 72,
        "bonds": 68,
        "stocks": 65
    },
    "North America": {
        "etf": 65,
        "bonds": 60,
        "stocks": 55
    },
    "Emerging Markets": {
        "etf": 55,
        "bonds": 50,
        "stocks": 45
    }
}

# Ticker-specific ESG scores for known ESG-focused securities
ESG_KNOWN_TICKERS = {
    # ESG-focused ETFs
    "IESG.L": 92,
    "SUSA": 88,
    "ESGV": 90,
    "ESGE": 85,
    "EEMX": 83,
    "IUSK.DE": 87,
    "IESE.AS": 89,
    "IDSE.AS": 84,
    
    # Green bonds
    "GRNB.L": 93,
    "BGRN": 91,
    
    # Well-known companies with strong ESG practices
    "ORSTED.CO": 95,  # Leader in renewable energy
    "MSFT": 82,
    "AAPL": 78,
    "SAP.DE": 83,
    "ASML.AS": 76,
    "NOVO-B.CO": 85,
    
    # Companies with lower ESG scores
    "XOM": 40,
    "SHEL.L": 42,
    "BP.L": 41
}

# Product information for known tickers
PRODUCT_INFO = {
    "EBND.DE":("iShares Core € Govt Bond UCITS ETF","Bond ETF"),
    "EUNA.DE":("iShares Euro Corporate Bond UCITS ETF","Bond ETF"),
    "IEUR":("iShares Core MSCI Europe ETF","ETF"),
    "SPY":("SPDR S&P 500 ETF Trust","ETF"),
    "IWM":("iShares Russell 2000 ETF","ETF"),
    "QQQ":("Invesco QQQ Trust","ETF"),
    "VTI":("Vanguard Total Stock Market ETF","ETF"),
    "AGG":("iShares Core U.S. Aggregate Bond ETF","Bond ETF"),
    "IEMG":("iShares Core MSCI Emerging Markets ETF","ETF"),
    "EEM":("iShares MSCI Emerging Markets ETF","ETF"),
    "VWO":("Vanguard FTSE Emerging Markets ETF","ETF"),
    "SHY":("iShares 1-3 Year Treasury Bond ETF","Bond ETF"),
    "BND":("Vanguard Total Bond Market ETF","Bond ETF"),
    "EMB":("iShares JP Morgan USD Emerging Markets Bond ETF","Bond ETF"),
    "VWOB":("Vanguard Emerging Markets Government Bond ETF","Bond ETF"),
    "EEMS":("iShares MSCI Emerging Markets Small-Cap ETF","ETF"),
}

# Questionnaire questions and options
QUESTIONNAIRE = [
    {"id":0, "text":"What is your primary investment objective?","options":["Wealth accumulation","Regular income","Capital preservation","Saving for a specific goal"]},
    {"id":1, "text":"Over what period do you plan to keep your money invested?","options":["<1 year","1-3 years","3-5 years","5-10 years",">10 years"]},
    {"id":2, "text":"How comfortable are you with market ups and downs?","options":["Very uncomfortable","Somewhat uncomfortable","Neutral","Somewhat comfortable","Very comfortable"]},
    {"id":3, "text":"If your portfolio lost 20% in a year, what would you do?","options":["Sell everything","Sell some","Do nothing","Buy more"]},
    {"id":4, "text":"What is the minimum annual return you expect?","options":["<2%","2-5%","5-8%","8-12%",">12%"]},
    {"id":5, "text":"How important is quick access to your money?","options":["Very important","Somewhat important","Not very important","Not important at all"]},
    {"id":6, "text":"Do you have any experience with investments?","options":["No, none at all","Yes, a little","Yes, regularly"]},
    {"id":7, "text":"What percentage of your savings will you invest?","options":["<10%","10-25%","25-50%","50-75%",">75%"]},
    {"id":8, "text":"Which best describes your risk vs. reward attitude?","options":["Protect capital","Balanced","Accept losses for gains","Seek maximum growth"]},
    {"id":9, "text":"How stable do you expect your income to be?","options":["Very stable","Somewhat stable","Uncertain","Likely to decrease"]},
    {"id":10,"text":"Do you anticipate any major expenses in the next three years?","options":["Yes","No"]},
    {"id":11,"text":"What percentage of your assets is in cash now?","options":["None","<10%","10-25%","25-50%",">50%"]},
    {"id":12,"text":"If an investment underperforms for six months, what would you do?","options":["Sell immediately","Re-evaluate","Hold through","Buy more"]},
    {"id":13,"text":"Are you interested in ESG-focused investments?","options":["Yes","No","Unsure"]},
    {"id":14,"text":"Would you consider investing with borrowed money to achieve higher returns?","options":["No, definitely not","Only if an expert recommends it","Yes, I can imagine doing that"]}
]

# =========================================================================
# 2. USER PROFILE FUNCTIONS
# =========================================================================

def map_answers_to_profile(a):
    """Creates a human-readable profile from questionnaire answers"""
    profile = {}
    for q in QUESTIONNAIRE:
        qid = q["id"]
        if qid in a:
            answer_index = a[qid]
            options = q["options"]
            if 0 <= answer_index < len(options):
                profile[qid] = options[answer_index]
    return profile

def derive_risk_level(a):
    """Calculate risk level using basic 5 questions (original method)"""
    required_keys = [1, 2, 4, 7, 8]
    if not all(k in a for k in required_keys):
        return 3  # Default to balanced if incomplete

    # Weighted calculation based on key questions
    w = {1: 0.20, 2: 0.30, 4: 0.20, 7: 0.15, 8: 0.15}
    s1, s2, s4, s7, s8 = a[1]/4, a[2]/4, a[4]/4, a[7]/4, a[8]/3
    comp = s1*w[1] + s2*w[2] + s4*w[4] + s7*w[7] + s8*w[8]

    if comp < 0.20: return 1
    if comp < 0.40: return 2
    if comp < 0.60: return 3
    if comp < 0.80: return 4
    return 5

def enhanced_derive_risk_level(answers):
    """Calculate risk level using more questionnaire answers for better accuracy"""
    # Start with base calculation from original 5 questions
    base_risk = derive_risk_level(answers)
    
    # Start with base risk level as a float to allow finer adjustments
    adjusted_risk = float(base_risk)
    
    # Reaction to losses (Q3) - Significant impact on true risk tolerance
    if 3 in answers:
        reaction = answers[3]
        if reaction == 0:  # "Sell everything"
            adjusted_risk -= 1.0  # Much lower risk tolerance
        elif reaction == 1:  # "Sell some"
            adjusted_risk -= 0.5  # Somewhat lower risk tolerance
        elif reaction == 3:  # "Buy more"
            adjusted_risk += 0.5  # Higher risk tolerance
    
    # Anticipated major expenses (Q10)
    if 10 in answers and answers[10] == 0:  # Yes to major expenses
        adjusted_risk -= 0.5  # Need more conservative approach
    
    # Underperformance reaction (Q12)
    if 12 in answers:
        reaction = answers[12]
        if reaction == 0:  # "Sell immediately"
            adjusted_risk -= 0.5  # Lower risk tolerance
        elif reaction == 3:  # "Buy more"
            adjusted_risk += 0.5  # Higher risk tolerance
    
    # Leverage comfort (Q14)
    if 14 in answers:
        leverage = answers[14]
        if leverage == 0:  # "No, definitely not"
            adjusted_risk -= 0.2  # More conservative
        elif leverage == 2:  # "Yes, I can imagine doing that"
            adjusted_risk += 0.5  # More aggressive
    
    # Clamp between 1-5 and round to nearest integer
    return max(1, min(5, round(adjusted_risk)))

def calculate_dynamic_allocation(answers):
    """Generate dynamic asset allocation based on questionnaire answers"""
    # Start with base allocation from risk level
    risk_level = derive_risk_level(answers)
    
    # Base allocations - every risk level has some exposure to each asset class
    base_allocations = {
        1: {"bonds": 0.80, "etf": 0.15, "stocks": 0.05},  # Mostly bonds
        2: {"bonds": 0.60, "etf": 0.30, "stocks": 0.10},  # Conservative
        3: {"bonds": 0.40, "etf": 0.40, "stocks": 0.20},  # True balance
        4: {"bonds": 0.20, "etf": 0.50, "stocks": 0.30},  # Growth tilt
        5: {"bonds": 0.10, "etf": 0.40, "stocks": 0.50}   # Aggressive but diversified
    }
    
    allocation = base_allocations[risk_level].copy()
    
    # Modify based on investment objective (Q0)
    if 0 in answers:
        objective = answers[0]
        if objective == 0:  # Wealth accumulation
            allocation["stocks"] += 0.05
            allocation["bonds"] -= 0.05
        elif objective == 1:  # Regular income
            # Increase bonds for income
            allocation["bonds"] += 0.05
            allocation["stocks"] -= 0.05
        elif objective == 2:  # Capital preservation
            allocation["bonds"] += 0.10
            allocation["stocks"] -= 0.10
            
    # Adjust for liquidity needs (Q5)
    if 5 in answers:
        liquidity = answers[5]
        if liquidity == 0:  # Very important
            allocation["bonds"] += 0.10
            allocation["stocks"] -= 0.10
        elif liquidity == 3:  # Not important at all
            allocation["stocks"] += 0.05
            allocation["bonds"] -= 0.05
    
    # Adjust for investment experience (Q6)
    if 6 in answers:
        experience = answers[6]
        if experience == 0:  # No experience
            # Reduce stocks for beginners
            allocation["stocks"] = max(0, allocation["stocks"] - 0.10)
            allocation["etf"] += 0.10
        elif experience == 2:  # Regular investor
            # Can handle more direct stocks
            allocation["stocks"] = min(0.60, allocation["stocks"] + 0.05)
            allocation["etf"] -= 0.05
    
    # Adjust for reaction to losses (Q3)
    if 3 in answers:
        reaction = answers[3]
        if reaction == 0:  # "Sell everything"
            allocation["bonds"] += 0.10
            allocation["stocks"] -= 0.10
        elif reaction == 3:  # "Buy more"
            allocation["stocks"] += 0.05
            allocation["bonds"] -= 0.05
    
    # Adjust for major expenses (Q10)
    if 10 in answers and answers[10] == 0:  # Yes to major expenses
        allocation["bonds"] += 0.10
        allocation["stocks"] -= 0.10
    
    # Ensure no negative allocations
    for asset in allocation:
        allocation[asset] = max(0, allocation[asset])
    
    # Normalize to ensure allocations sum to 1.0
    total = sum(allocation.values())
    if total > 0:  # Avoid division by zero
        for asset in allocation:
            allocation[asset] /= total
    
    return allocation

def get_allowed_allocations(a):
    """Get allowed allocations based on the complete user profile"""
    # Use dynamic allocation instead of fixed
    alloc = calculate_dynamic_allocation(a)
    
    # Special case for very short-term investors (< 1 year)
    if a.get(1) == 0:
        return {"bonds":1.0,"etf":0.0,"stocks":0.0}
    
    # Adjust for investment experience
    if a.get(6, 99) <= 0:  # No investment experience
        # Remove stocks entirely for complete beginners
        alloc["stocks"] = 0.0
        # Normalize the remaining allocation
        s = alloc["bonds"] + alloc["etf"]
        if s > 0:
            alloc["bonds"] /= s
            alloc["etf"] /= s
    elif a.get(6, 99) <= 1:  # Limited experience
        # Reduce stocks but don't eliminate
        alloc["stocks"] /= 2
        # Increase ETFs to compensate
        alloc["etf"] += alloc["stocks"]
        # Normalize
        s = sum(alloc.values())
        if s > 0:
            for asset in alloc:
                alloc[asset] /= s
    
    return alloc

def adjust_scoring_weights(answers, risk_level):
    """Adjust scoring weights based on questionnaire answers"""
    # Start with standard weights from risk profile
    weights = RISK_PROFILE[risk_level]["weights"].copy()
    
    # Modify based on investment objective (Q0)
    if 0 in answers:
        objective = answers[0]
        if objective == 0:  # Wealth accumulation
            # Favor growth metrics
            weights["ev_ebitda"] -= 5
            weights["fcf_yield"] += 5
        elif objective == 1:  # Regular income
            # Add dividend yield weight
            weights["dividend_yield"] = 15
            weights["ev_ebitda"] -= 5
            weights["fcf_yield"] -= 10
        elif objective == 2:  # Capital preservation
            # Favor stability
            weights["volatility"] += 10
            weights["ev_ebitda"] -= 5
            weights["fcf_yield"] -= 5
    
    # Adjust for ESG interest (Q13)
    if 13 in answers:
        if answers[13] == 0:  # Yes to ESG
            weights["esgScore"] = min(50, weights.get("esgScore", 0) + 10)
            # Reduce other metrics to keep total reasonable
            total_reduction = 10
            for metric in ["ev_ebitda", "fcf_yield", "volatility"]:
                weights[metric] = max(5, weights[metric] - (total_reduction // 3))
    
    # Normalize to ensure weights sum to 100
    total = sum(weights.values())
    for metric in weights:
        weights[metric] = round(weights[metric] * 100 / total)
    
    return weights

# =========================================================================
# 3. INVESTMENT RECOMMENDATION FUNCTIONS
# =========================================================================

def get_esg_score_for_ticker(ticker, region, asset_class):
    """Get region and class-specific ESG scores with realistic variation"""
    # Check if a predefined score exists for this ticker
    if ticker in ESG_KNOWN_TICKERS:
        base_score = ESG_KNOWN_TICKERS[ticker]
        # Add small variation for realism
        return base_score * random.uniform(0.95, 1.05)
    
    # Otherwise use region-specific base value
    base_score = ESG_BASE_SCORES.get(region, {}).get(asset_class, 50)
    
    # Consider ESG prefix in ticker name
    if any(esg_prefix in ticker for esg_prefix in ["ESG", "SRI", "SDG", "GREEN", "SUST"]):
        base_score += 15 * random.uniform(0.9, 1.1)
    
    # Random variation for realism, but more variation for unknown tickers
    variation = random.uniform(0.85, 1.15)
    
    # Limit score to 0-100
    return min(100, max(0, base_score * variation))

def fetch_batch_metrics(tickers: List[str]) -> List[Dict[str, Any]]:
    """Fetch financial metrics for a list of tickers"""
    results = []
    for t in tickers:
        try:
            tk = yf.Ticker(t)
            info = tk.info
            
            ev, ebitda = info.get("enterpriseValue"), info.get("ebitda")
            ev_ebitda = ev/ebitda if ev and ebitda else None
            
            fcf, mcap = info.get("freeCashflow"), info.get("marketCap")
            fcf_yield = fcf/mcap if fcf and mcap else None
            
            # Get dividend yield
            div_yield = info.get("dividendYield", None)
            if div_yield is not None:
                div_yield = div_yield * 100  # Convert to percentage
            
            try:
                hist = tk.history(period="3mo", interval="1d")["Close"].pct_change().dropna()
                vol = hist.std()*(252**0.5)
            except Exception as e:
                print(f"Error getting volatility for {t}: {str(e)}")
                vol = None
            
            # Get ESG score: First check if known ticker, else from API
            esg_score = ESG_KNOWN_TICKERS.get(t, info.get("esgScore"))
            
            results.append({
                "ticker": t,
                "ev_ebitda": ev_ebitda,
                "fcf_yield": fcf_yield,
                "volatility": vol,
                "esgScore": esg_score,
                "dividend_yield": div_yield
            })
        except Exception as e:
            print(f"Error fetching data for {t}: {str(e)}")
            # Still add the ticker but with missing metrics
            # This will be handled by the scoring function
            results.append({
                "ticker": t,
                "ev_ebitda": None,
                "fcf_yield": None,
                "volatility": None,
                "esgScore": get_esg_score_for_ticker(t, None, None),
                "dividend_yield": None
            })
        time.sleep(0.1)
    return results

def apply_filters(items, filters):
    """Apply filters to list of items based on metric thresholds"""
    def ok(it):
        for k,(mn,mx) in filters.items():
            v=it.get(k)
            if v is None: continue
            if (mn is not None and v<mn) or (mx is not None and v>mx): return False
        return True
    return [it for it in items if ok(it)]

def score_item(item, weights, region=None, asset_class=None):
    """Score an investment item based on risk profile weights and region/class defaults"""
    ev = item.get("ev_ebitda")
    fcf = item.get("fcf_yield")
    vol = item.get("volatility")
    esg = item.get("esgScore")
    div = item.get("dividend_yield")
    ticker = item.get("ticker")

    # Region and asset class specific default values for missing data
    if ev is None or ev <= 0:
        # Region-specific EV/EBITDA defaults
        if region == "Europe":
            ev = 18 * random.uniform(0.9, 1.1)
        elif region == "North America":
            ev = 20 * random.uniform(0.9, 1.1)
        elif region == "Emerging Markets":
            ev = 22 * random.uniform(0.9, 1.1)
        else:
            ev = 20 * random.uniform(0.9, 1.1)
    
    if fcf is None:
        # Asset class specific FCF yield defaults
        if asset_class == "bonds":
            fcf = 0.015 * random.uniform(0.9, 1.1)
        elif asset_class == "etf":
            fcf = 0.02 * random.uniform(0.9, 1.1)
        elif asset_class == "stocks":
            fcf = 0.03 * random.uniform(0.9, 1.1)
        else:
            fcf = 0.02 * random.uniform(0.9, 1.1)
    
    if vol is None:
        # Region-specific and asset class specific volatility standards
        base_vol = 0.3
        region_factor = 1.0
        asset_factor = 1.0
        
        if region == "Europe":
            region_factor = 0.9  # European markets tend to be less volatile
        elif region == "North America":
            region_factor = 1.0  # Baseline
        elif region == "Emerging Markets":
            region_factor = 1.2  # Emerging markets tend to be more volatile
        
        if asset_class == "bonds":
            asset_factor = 0.7  # Bonds less volatile
        elif asset_class == "etf":
            asset_factor = 1.0  # Baseline
        elif asset_class == "stocks":
            asset_factor = 1.3  # Individual stocks more volatile
        
        vol = base_vol * region_factor * asset_factor * random.uniform(0.9, 1.1)
    
    # Dividend yield defaults
    if div is None:
        if asset_class == "bonds":
            div = 3.0 * random.uniform(0.9, 1.1)  # Bonds typically have higher yields
        elif asset_class == "etf":
            div = 2.0 * random.uniform(0.9, 1.1)  # ETFs have moderate yields
        elif asset_class == "stocks":
            # Region-specific yield expectations
            if region == "Europe":
                div = 3.0 * random.uniform(0.9, 1.1)  # European stocks often have higher dividends
            elif region == "North America":
                div = 1.5 * random.uniform(0.9, 1.1)  # US stocks have moderate dividends
            elif region == "Emerging Markets":
                div = 2.5 * random.uniform(0.9, 1.1)  # Emerging markets vary widely
            else:
                div = 2.0 * random.uniform(0.9, 1.1)
        else:
            div = 2.0 * random.uniform(0.9, 1.1)
    
    # Improved ESG score calculation
    if esg is None:
        esg = get_esg_score_for_ticker(ticker, region, asset_class)

    # Scoring formulas
    score_ev = max(0, min(1, (20 - ev) / 15))
    score_fcf = max(0, min(1, fcf / 0.10))
    score_vol = max(0, min(1, (0.5 - vol) / 0.4))
    score_esg = max(0, min(1, esg / 100))
    score_div = max(0, min(1, div / 5.0))  # Score of 1 for 5% yield or higher

    # Regional score adjustments
    region_modifier = 1.0
    if region == "Europe":
        region_modifier = 1.0 + (random.uniform(-0.05, 0.05))
    elif region == "North America":
        region_modifier = 1.0 + (random.uniform(-0.05, 0.05))
    elif region == "Emerging Markets":
        region_modifier = 1.0 + (random.uniform(-0.05, 0.05))

    # Calculate total score with all available metrics
    total_score = (
        score_ev * weights.get("ev_ebitda", 0) +
        score_fcf * weights.get("fcf_yield", 0) +
        score_vol * weights.get("volatility", 0) +
        score_esg * weights.get("esgScore", 0) +
        score_div * weights.get("dividend_yield", 0)
    ) / 100 * region_modifier

    return total_score

def get_user_universe(region, asset_class, esg_only):
    """Get appropriate asset universe based on user preferences"""
    if region=="Any":
        full = sum((ASSET_UNIVERSE[r][asset_class] for r in ASSET_UNIVERSE),[])
    else:
        full = ASSET_UNIVERSE.get(region,{}).get(asset_class,[])
    return full[:5] if esg_only else full

def get_region_risk_etf(region, rl):
    """Get the primary ETF for a region and risk level"""
    if region=="Any":
        return {"profile":"Balanced","ticker":"EUNL.DE"}
    p,t=REGION_RISK_ETF[region][rl]
    return {"profile":p,"ticker":t}

def map_user_to_recommendations(region, asset_class, risk_level, esg_only, answers=None):
    """Generate recommendations based on user profile"""
    try:
        tks = get_user_universe(region, asset_class, esg_only)
        raw = fetch_batch_metrics(tks)
        
        # If answers provided, use custom weights
        if answers:
            custom_weights = adjust_scoring_weights(answers, risk_level)
            cfg = RISK_PROFILE[risk_level].copy()
            cfg["weights"] = custom_weights
        else:
            cfg = RISK_PROFILE[risk_level]
            
        flt = apply_filters(raw, cfg["filters"])
        
        for it in flt:
            it["score"] = score_item(it, cfg["weights"], region, asset_class)
        
        return sorted(flt, key=lambda x: x["score"], reverse=True)
    except Exception as e:
        print(f"Error in recommendations for {region}/{asset_class}: {str(e)}")
        # Return a default recommendation if there's an error
        default_ticker = REGION_RISK_ETF.get(region, {}).get(3, ("Balanced", "EUNL.DE"))[1]
        return [{
            "ticker": default_ticker,
            "ev_ebitda": None,
            "fcf_yield": None,
            "volatility": None,
            "esgScore": ESG_BASE_SCORES.get(region, {}).get(asset_class, 50),
            "dividend_yield": None,
            "score": 0.5
        }]

# =========================================================================
# 4. MAIN RECOMMENDATION FUNCTION
# =========================================================================

def generate_recommendation(ans):
    """Generate personalized investment recommendations"""
    try:
        profile = map_answers_to_profile(ans)
        esg_only = profile.get(13, "No") == "Yes"
        
        # Use enhanced risk level calculation
        rl = enhanced_derive_risk_level(ans)
        
        # Use dynamic allocation instead of fixed
        alloc = get_allowed_allocations(ans)

        combined = []

        for region in ["Europe", "North America", "Emerging Markets"]:
            region_products = []

            for cls, w in alloc.items():
                if w <= 0.05:  # Skip very small allocations, but keep more diversity
                    continue

                try:
                    # Pass answers to recommendation function for customized scoring
                    recs = map_user_to_recommendations(region, cls, rl, esg_only, ans)
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
                except Exception as e:
                    print(f"Error generating recommendations for {region}/{cls}: {str(e)}")
                    # Add a fallback recommendation if needed
                    if not region_products and cls == "etf":  # Only add fallback for ETFs
                        default_etf = REGION_RISK_ETF[region][rl][1]
                        region_products.append({
                            "ticker": default_etf,
                            "region": region,
                            "asset_class": cls,
                            "class_weight": w,
                            "score": 0.5,
                            "final_score": 0.5 * w,
                            "esgScore": ESG_BASE_SCORES.get(region, {}).get(cls, 50),
                            "dividend_yield": None
                        })

            # Make sure we have at least one recommendation per region
            if region_products:
                # Ensure diversity in asset types within each region
                # Group by asset class
                by_asset_class = {}
                for prod in region_products:
                    asset_class = prod["asset_class"]
                    if asset_class not in by_asset_class:
                        by_asset_class[asset_class] = []
                    by_asset_class[asset_class].append(prod)
                
                # Get top product from each asset class with allocation > 0
                top_region_recs = []
                for asset_class, products in by_asset_class.items():
                    if products and alloc.get(asset_class, 0) > 0:
                        top_in_class = sorted(products, key=lambda x: x["score"], reverse=True)[0]
                        top_region_recs.append(top_in_class)
                
                # If we still need more, add second-best products
                if len(top_region_recs) < 2 and region_products:
                    remaining = [p for p in region_products if p not in top_region_recs]
                    remaining = sorted(remaining, key=lambda x: x["final_score"], reverse=True)
                    top_region_recs.extend(remaining[:2-len(top_region_recs)])
                
                combined += top_region_recs
            else:
                # Add a default recommendation if we couldn't get any valid ones
                default_etf = REGION_RISK_ETF[region][3][1]  # Use balanced risk level as fallback
                combined.append({
                    "ticker": default_etf,
                    "region": region,
                    "asset_class": "etf",
                    "class_weight": 1.0,
                    "score": 0.5,
                    "final_score": 0.5,
                    "esgScore": ESG_BASE_SCORES.get(region, {}).get("etf", 50),
                    "dividend_yield": None
                })

        primary = get_region_risk_etf("Europe", rl)

        # Add risk level to profile for reference
        profile["risk_level"] = rl

        return {
            "investor_profile": profile,
            "risk_level": rl,
            "primary_etf": primary,
            "recommendations": combined
        }
    except Exception as e:
        print(f"Error in generate_recommendation: {str(e)}")
        # Return a default recommendation
        rl = 3  # Balanced as default
        return {
            "investor_profile": map_answers_to_profile(ans),
            "risk_level": rl,
            "primary_etf": {"profile": "Balanced", "ticker": "EUNL.DE"},
            "recommendations": [
                {
                    "ticker": "IEUR",
                    "region": "Europe",
                    "asset_class": "etf",
                    "class_weight": 0.4,
                    "score": 0.5,
                    "final_score": 0.5,
                    "esgScore": 65,
                    "dividend_yield": None
                },
                {
                    "ticker": "SPY",
                    "region": "North America",
                    "asset_class": "etf",
                    "class_weight": 0.4,
                    "score": 0.5,
                    "final_score": 0.5,
                    "esgScore": 60,
                    "dividend_yield": None
                },
                {
                    "ticker": "IEMG",
                    "region": "Emerging Markets",
                    "asset_class": "etf",
                    "class_weight": 0.2,
                    "score": 0.5,
                    "final_score": 0.5,
                    "esgScore": 55,
                    "dividend_yield": None
                }
            ]
        }

# Export main function with backward compatibility
generate_full_recommendation = generate_recommendation
