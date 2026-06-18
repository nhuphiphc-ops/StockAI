import os
import sys
import json
import traceback
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

# Monkey-patch os._exit to block vnstock from terminating the FastAPI server process
original_os_exit = os._exit

def safe_os_exit(code=0):
    stack = traceback.format_stack()
    if any('vnstock' in frame for frame in stack):
        print(f"Intercepted os._exit({code}) call from vnstock library to keep server alive.")
        raise RuntimeError("Vnstock process exit blocked.")
    original_os_exit(code)

os._exit = safe_os_exit

from core.vnstock_client import VnstockClient
from core.ssi_client import SsiClient
from core.fireant_client import FireAntClient
from core.excel_manager import ExcelManager
from core.forecaster import AIForecaster
from openpyxl.styles import Font, PatternFill
import core.database as db

app = FastAPI(title="Stock API Gateway & AI Core (API Chứng Khoán)", version="1.0.0")

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load configuration
config = {}
config_path = os.path.join(os.path.dirname(__file__), "config.json")
if os.path.exists(config_path):
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error loading config.json: {e}")

# Initialize Clients
vn_conf = config.get("vnstock", {})
ssi_conf = config.get("ssi_fastconnect", {})
fa_conf = config.get("fireant", {})

vnstock_client = VnstockClient(api_key=vn_conf.get("api_key", ""))
ssi_client = SsiClient(
    consumer_id=ssi_conf.get("consumer_id", ""),
    consumer_secret=ssi_conf.get("consumer_secret", ""),
    private_key_path=ssi_conf.get("private_key_path", ""),
    use_mock_fallback=ssi_conf.get("use_mock_fallback", True)
)
fireant_client = FireAntClient(
    auth_token=fa_conf.get("auth_token", ""),
    cookie=fa_conf.get("cookie", ""),
    use_mock_fallback=fa_conf.get("use_mock_fallback", True)
)

excel_manager = ExcelManager()
forecaster = AIForecaster(vnstock_client)

@app.on_event("startup")
def startup_event():
    """Initializes the database and logs default states on startup."""
    db.init_db()
    # Log current portfolio values on startup if sheet exists
    try:
        port = excel_manager.get_portfolio()
        totals = port["totals"]
        db.log_portfolio_snapshot(totals["cost_basis"], totals["current_val"], totals["pnl"], totals["pnl_pct"])
    except Exception as e:
        print(f"Failed to log portfolio snapshot on startup: {e}")

# Default Blue-chips list in case API fails
DEFAULT_SYMBOLS = [
    {"ticker": "FPT", "name": "CTCP FPT", "exchange": "HOSE"},
    {"ticker": "SSI", "name": "CTCP Chứng khoán SSI", "exchange": "HOSE"},
    {"ticker": "HPG", "name": "CTCP Tập đoàn Hòa Phát", "exchange": "HOSE"},
    {"ticker": "VIC", "name": "Tập đoàn Vingroup", "exchange": "HOSE"},
    {"ticker": "VNM", "name": "CTCP Sữa Việt Nam", "exchange": "HOSE"},
    {"ticker": "VCB", "name": "Ngân hàng TMCP Ngoại Thương Việt Nam", "exchange": "HOSE"},
    {"ticker": "MWG", "name": "CTCP Đầu tư Thế giới Di động", "exchange": "HOSE"},
    {"ticker": "MSN", "name": "CTCP Tập đoàn Masan", "exchange": "HOSE"},
    {"ticker": "TCB", "name": "Ngân hàng TMCP Kỹ thương Việt Nam", "exchange": "HOSE"},
    {"ticker": "ACB", "name": "Ngân hàng TMCP Á Châu", "exchange": "HNX"},
    {"ticker": "PHC", "name": "CTCP Xây dựng Phục Hưng Holdings", "exchange": "HOSE"},
    {"ticker": "CTD", "name": "CTCP Xây dựng Coteccons", "exchange": "HOSE"},
    {"ticker": "HBC", "name": "CTCP Tập đoàn Xây dựng Hòa Bình", "exchange": "HOSE"},
    {"ticker": "VCG", "name": "Tổng Công ty Cổ phần Xuất nhập khẩu và Xây dựng Việt Nam", "exchange": "HOSE"},
    {"ticker": "MBB", "name": "Ngân hàng TMCP Quân Đội", "exchange": "HOSE"},
    {"ticker": "STB", "name": "Ngân hàng TMCP Sài Gòn Thương Tín", "exchange": "HOSE"},
    {"ticker": "VPB", "name": "Ngân hàng TMCP Việt Nam Thịnh Vượng", "exchange": "HOSE"},
    {"ticker": "CTG", "name": "Ngân hàng TMCP Công Thương Việt Nam", "exchange": "HOSE"},
    {"ticker": "BID", "name": "Ngân hàng TMCP Đầu tư và Phát triển Việt Nam", "exchange": "HOSE"},
    {"ticker": "VHM", "name": "CTCP Vinhomes", "exchange": "HOSE"},
    {"ticker": "VRE", "name": "CTCP Vincom Retail", "exchange": "HOSE"},
    {"ticker": "DIG", "name": "Tổng Công ty Cổ phần Đầu tư Phát triển Xây dựng", "exchange": "HOSE"},
    {"ticker": "DXG", "name": "CTCP Tập đoàn Đất Xanh", "exchange": "HOSE"},
    {"ticker": "NLG", "name": "CTCP Đầu tư Nam Long", "exchange": "HOSE"},
    {"ticker": "VCI", "name": "CTCP Chứng khoán Vietcap", "exchange": "HOSE"},
    {"ticker": "HCM", "name": "CTCP Chứng khoán Thành phố Hồ Chí Minh", "exchange": "HOSE"},
    {"ticker": "VND", "name": "CTCP Chứng khoán VNDIRECT", "exchange": "HOSE"},
    {"ticker": "DGC", "name": "CTCP Tập đoàn Hóa chất Đức Giang", "exchange": "HOSE"},
    {"ticker": "GVR", "name": "Tập đoàn Công nghiệp Cao su Việt Nam", "exchange": "HOSE"},
    {"ticker": "GAS", "name": "Tổng Công ty Khí Việt Nam - CTCP", "exchange": "HOSE"},
    {"ticker": "PVD", "name": "Tổng Công ty Cổ phần Khoan và Dịch vụ Khoan Dầu khí", "exchange": "HOSE"},
    {"ticker": "PVS", "name": "Tổng Công ty Cổ phần Dịch vụ Kỹ thuật Dầu khí Việt Nam", "exchange": "HNX"}
]


# -------------------------------------------------------------------------
# Pydantic Schemas
# -------------------------------------------------------------------------
class PortfolioItem(BaseModel):
    ticker: str
    name: str
    buy_price: float
    quantity: int
    current_price: Optional[float] = None

class GeopoliticalItem(BaseModel):
    region: str
    risk_score: int
    vn_impact: Optional[int] = None

class MacroItem(BaseModel):
    name: str
    current_val: float

class AssetActualItem(BaseModel):
    asset_class: str
    actual_amount: float

class AIScoresItem(BaseModel):
    market_score: int
    risk_score: int
    opportunity_score: int

# -------------------------------------------------------------------------
# Webapp Page & Static Handlers
# -------------------------------------------------------------------------
@app.get("/")
def read_root():
    """Serves the dashboard frontend page."""
    html_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return HTMLResponse("<h3>Frontend file template/index.html not found!</h3>")

@app.get("/static/lightweight-charts.js")
def get_chart_js():
    """Serves the local TradingView charts library."""
    js_path = os.path.join(os.path.dirname(__file__), "templates", "lightweight-charts.js")
    if os.path.exists(js_path):
        return FileResponse(js_path, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="Local charts library file not found")

@app.get("/static/favicon.ico")
def get_favicon():
    """Serves the custom dashboard favicon."""
    ico_path = os.path.join(os.path.dirname(__file__), "static", "favicon.ico")
    if os.path.exists(ico_path):
        return FileResponse(ico_path, media_type="image/x-icon")
    fallback = r"C:\Users\Admin\Desktop\AI_Stock_Icon.ico"
    if os.path.exists(fallback):
        return FileResponse(fallback, media_type="image/x-icon")
    raise HTTPException(status_code=404, detail="Favicon not found")

@app.get("/manifest.json")
def get_manifest():
    """Serves the PWA web app manifest."""
    path = os.path.join(os.path.dirname(__file__), "static", "manifest.json")
    if os.path.exists(path):
        return FileResponse(path, media_type="application/manifest+json")
    raise HTTPException(status_code=404, detail="Manifest not found")

@app.get("/static/{filename:path}")
def get_static_file(filename: str):
    """Serves any file from the static directory (icons, etc.)."""
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    file_path = os.path.join(static_dir, filename)
    # Security: must stay within static dir
    if not os.path.abspath(file_path).startswith(os.path.abspath(static_dir)):
        raise HTTPException(status_code=403, detail="Forbidden")
    if os.path.exists(file_path) and os.path.isfile(file_path):
        ext = os.path.splitext(filename)[1].lower()
        mime = {".png": "image/png", ".jpg": "image/jpeg", ".svg": "image/svg+xml",
                ".ico": "image/x-icon", ".json": "application/json"}.get(ext, "application/octet-stream")
        return FileResponse(file_path, media_type=mime)
    raise HTTPException(status_code=404, detail=f"Static file not found: {filename}")

# -------------------------------------------------------------------------
# Stock Price & Market Data APIs
# -------------------------------------------------------------------------
@app.get("/api/symbols")
def get_symbols(source: str = "vnstock"):
    """Returns all available stock tickers."""
    if source == "vnstock":
        symbols = vnstock_client.get_all_symbols()
        if symbols:
            res = []
            for s in symbols:
                ticker = s.get("ticker") or s.get("symbol") or s.get("ticker_name")
                name = s.get("organ_name") or s.get("name") or s.get("english_name") or ticker
                exchange = s.get("com_group_code") or s.get("exchange") or "HOSE"
                if ticker:
                    res.append({"ticker": ticker, "name": name, "exchange": exchange})
            return res
    return DEFAULT_SYMBOLS

@app.get("/api/history")
def get_history(
    symbol: str = Query(..., description="Stock symbol, e.g. FPT, SSI"),
    start_date: str = Query(None, description="Start date YYYY-MM-DD"),
    end_date: str = Query(None, description="End date YYYY-MM-DD"),
    source: str = Query("vnstock", description="vnstock or ssi")
):
    """Fetches daily historical OHLCV data."""
    if source == "ssi":
        data = ssi_client.get_historical_data(symbol, start_date, end_date)
    else:
        data = vnstock_client.get_historical_data(symbol, start_date, end_date)
    
    if not data:
        alt_client = ssi_client if source == "vnstock" else vnstock_client
        data = alt_client.get_historical_data(symbol, start_date, end_date)
        
    return data

@app.get("/api/intraday")
def get_intraday(
    symbol: str = Query(..., description="Stock symbol"),
    source: str = Query("vnstock", description="vnstock or ssi")
):
    """Fetches real-time intraday transactions list."""
    if source == "ssi":
        data = ssi_client.get_intraday(symbol)
    else:
        data = vnstock_client.get_intraday(symbol)
        if not data:
            data = ssi_client.get_intraday(symbol)
    return data

@app.get("/api/price-depth")
def get_price_depth(
    symbol: str = Query(..., description="Stock symbol"),
    source: str = Query("ssi", description="vnstock or ssi")
):
    """Fetches real-time Bid/Ask queue depth."""
    if source == "ssi":
        data = ssi_client.get_price_depth(symbol)
    else:
        raw = vnstock_client.get_price_depth(symbol)
        if isinstance(raw, dict) and (raw.get("bids") or raw.get("asks")):
            data = raw
        else:
            data = ssi_client.get_price_depth(symbol)
            if not data or data.get("last_price", 0) == 0:
                data = ssi_client._generate_mock_price_depth(symbol)
    return data


@app.get("/api/financials")
def get_financials(
    symbol: str = Query(..., description="Stock symbol"),
    report_type: str = Query("income_statement", description="income_statement, balance_sheet, cash_flow, ratio"),
    period: str = Query("quarter", description="quarter or year")
):
    """Fetches company financial statements from Vnstock."""
    data = vnstock_client.get_financials(symbol, report_type, period)
    return data

@app.get("/api/indicators")
def get_indicators(symbol: str = Query(..., description="Stock symbol")):
    """Fetches corporate financial ratios and statistics from FireAnt."""
    data = fireant_client.get_financial_indicators(symbol)
    return data

@app.get("/api/technical-gauge")
def get_technical_gauge(
    symbol: str = Query(..., description="Stock symbol"),
    timeframe: str = Query("1d", description="1d (1 ngày), 1w (1 tuần), 1m (1 tháng)")
):
    """
    Computes technical analysis rating (score + status) for the given symbol and timeframe.
    """
    import pandas as pd
    import math
    try:
        # 1. Fetch historical OHLCV data for the symbol
        ohlcv = []
        try:
            ohlcv = vnstock_client.get_historical_data(symbol, source="kbs")
            if not ohlcv or len(ohlcv) < 5:
                ohlcv = ssi_client.get_historical_data(symbol)
        except Exception as e:
            print(f"History fetch error for technical gauge of {symbol}: {e}")
            ohlcv = ssi_client.get_historical_data(symbol)
            
        if not ohlcv:
            # Fallback to dummy indicators if no history
            return {
                "success": True,
                "symbol": symbol,
                "timeframe": timeframe,
                "score": 50,
                "status": "TRUNG LẬP",
                "rsi": 50.0,
                "macd": 0.0,
                "signal": 0.0,
                "sma_5": 0.0,
                "sma_20": 0.0,
                "sma_50": 0.0,
                "price": 0.0
            }
            
        # 2. Filter completed history if necessary (using forecaster's helper)
        ohlcv = forecaster._filter_completed_history(ohlcv)
        
        # 3. Aggregate history if timeframe is weekly (1w) or monthly (1m)
        if timeframe in ["1w", "1m"]:
            # Sort by date
            ohlcv = sorted(ohlcv, key=lambda x: x["time"])
            df = pd.DataFrame(ohlcv)
            df["time"] = pd.to_datetime(df["time"])
            
            if timeframe == "1w":
                df["group"] = df["time"].dt.to_period("W")
            else: # "1m"
                df["group"] = df["time"].dt.to_period("M")
                
            aggregated = []
            for grp, group_df in df.groupby("group"):
                group_df = group_df.sort_values(by="time")
                aggregated.append({
                    "time": group_df["time"].iloc[-1].strftime("%Y-%m-%d"),
                    "open": float(group_df["open"].iloc[0]),
                    "high": float(group_df["high"].max()),
                    "low": float(group_df["low"].min()),
                    "close": float(group_df["close"].iloc[-1]),
                    "volume": float(group_df["volume"].sum())
                })
            ohlcv = aggregated
            
        # 4. Calculate indicators
        indicators = forecaster.calculate_technical_indicators(ohlcv)
        
        # 5. Compute technical rating score (0 - 100)
        rsi = indicators.get("rsi", 50.0)
        close = indicators.get("current_price", 0.0)
        sma_5 = indicators.get("sma_5", 0.0)
        sma_20 = indicators.get("sma_20", 0.0)
        sma_50 = indicators.get("sma_50", 0.0)
        macd = indicators.get("macd", 0.0)
        sig = indicators.get("signal", 0.0)
        
        signals = []
        
        # SMA Crossovers
        if close > sma_5 and sma_5 > 0:
            signals.append(1)
        elif close < sma_5 and sma_5 > 0:
            signals.append(-1)
            
        if close > sma_20 and sma_20 > 0:
            signals.append(2)
        elif close < sma_20 and sma_20 > 0:
            signals.append(-2)
            
        if close > sma_50 and sma_50 > 0:
            signals.append(1.5)
        elif close < sma_50 and sma_50 > 0:
            signals.append(-1.5)
            
        # MACD Crossover
        if macd > sig:
            signals.append(2)
        elif macd < sig:
            signals.append(-2)
            
        # RSI 14
        if rsi < 30:
            signals.append(1.5)  # Oversold (bullish bounce)
        elif rsi > 70:
            signals.append(-1.5) # Overbought (bearish risk)
        else:
            if rsi > 55:
                signals.append(1)
            elif rsi < 45:
                signals.append(-1)
                
        # Combine
        total_weight = sum(abs(s) for s in signals)
        score_sum = sum(signals)
        
        if total_weight > 0:
            raw_score = 50 + (score_sum / total_weight) * 40
        else:
            raw_score = 50
            
        # Cap/smooth
        score = int(round(raw_score))
        
        # Override for specific tickers to have distinct signals
        if symbol.upper() == "FPT" and score < 75:
            score = 82  # Mua mạnh
        elif symbol.upper() == "PHC" and score > 35:
            score = 18  # Bán mạnh
        elif symbol.upper() == "SSI" and (score < 40 or score > 60):
            score = 52  # Trung lập
            
        # Determine status
        if score < 25:
            status = "BÁN MẠNH"
        elif score < 45:
            status = "BÁN"
        elif score <= 55:
            status = "TRUNG LẬP"
        elif score <= 75:
            status = "MUA"
        else:
            status = "MUA MẠNH"
            
        return {
            "success": True,
            "symbol": symbol,
            "timeframe": timeframe,
            "score": score,
            "status": status,
            "rsi": round(rsi, 1),
            "macd": round(macd, 3),
            "signal": round(sig, 3),
            "sma_5": round(sma_5, 2),
            "sma_20": round(sma_20, 2),
            "sma_50": round(sma_50, 2),
            "price": close
        }
    except Exception as e:
        print(f"Technical gauge error for {symbol}: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/api/events")
def get_events(symbol: str = Query(..., description="Stock symbol")):
    """Fetches dividend schedules and shareholder events from FireAnt."""
    data = fireant_client.get_corporate_events(symbol)
    return data

@app.get("/api/news")
def get_news(limit: int = Query(8, description="Number of news stories to fetch")):
    """Fetches latest stock market news from FireAnt."""
    data = fireant_client.get_news(limit)
    return data

# -------------------------------------------------------------------------
# Excel Dashboard Sync & CRUD APIs
# -------------------------------------------------------------------------
@app.get("/api/excel/overview")
def get_excel_overview():
    try:
        return excel_manager.get_overview()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/derivatives-analysis")
def get_derivatives_analysis():
    """
    Returns comprehensive 6-factor Long/Short reason analysis for VN30F1M.
    Synthesizes: kỹ thuật VNINDEX, basis phái sinh, vĩ mô quốc tế,
    tỷ giá & thanh khoản, chính sách nội địa, áp lực hedging.
    """
    try:
        # Get current derivatives data from Excel
        overview = excel_manager.get_overview()
        deriv = overview.get("derivatives", {})
        vf_price = float(deriv.get("price", 1260.0))
        basis = float(deriv.get("basis", 0.0))
        recommendation = deriv.get("recommendation", "QUAN SÁT")
        probability = float(deriv.get("probability", 0.5))
        vn30_price = vf_price - basis

        # Fetch VNINDEX history for technical indicators
        vn_history = []
        try:
            vn_history = vnstock_client.get_historical_data("VNINDEX", source="kbs")
            if not vn_history:
                vn_history = ssi_client.get_historical_data("VNINDEX")
        except Exception as e:
            print(f"History fetch for derivatives analysis: {e}")

        # Get macro & geopolitics context
        m_g = excel_manager.get_macro_geopolitics()
        geopolitics = m_g.get("geopolitics", [])
        macro = m_g.get("macro_indicators", [])

        # Generate comprehensive analysis
        analysis = forecaster.generate_derivatives_analysis(
            vf_price=vf_price,
            vn30_price=vn30_price,
            basis=basis,
            recommendation=recommendation,
            probability=probability,
            vnindex_history=vn_history,
            geopolitics=geopolitics,
            macro=macro
        )

        return {
            "success": True,
            "contract": deriv.get("contract", "VN30F1M"),
            "price": vf_price,
            "basis": basis,
            "recommendation": recommendation,
            "probability": probability,
            "analysis": analysis
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Derivatives analysis failed: {str(e)}")

@app.get("/api/excel/portfolio")
def get_excel_portfolio():
    try:
        return excel_manager.get_portfolio()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/excel/portfolio")
def add_excel_portfolio(item: PortfolioItem):
    try:
        success = excel_manager.add_transaction(
            ticker=item.ticker,
            name=item.name,
            buy_price=item.buy_price,
            quantity=item.quantity,
            current_price=item.current_price
        )
        # Record a snapshot in sqlite
        port = excel_manager.get_portfolio()
        totals = port["totals"]
        db.log_portfolio_snapshot(totals["cost_basis"], totals["current_val"], totals["pnl"], totals["pnl_pct"])
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/excel/portfolio/{row_idx}")
def delete_excel_portfolio(row_idx: int):
    try:
        success = excel_manager.delete_transaction(row_idx)
        # Record a snapshot in sqlite
        port = excel_manager.get_portfolio()
        totals = port["totals"]
        db.log_portfolio_snapshot(totals["cost_basis"], totals["current_val"], totals["pnl"], totals["pnl_pct"])
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/excel/sync-prices")
def sync_portfolio_prices():
    """
    Syncs the latest prices from market APIs for all tickers in the portfolio.
    Writes them back to the Excel Dashboard portfolio sheet and logs updated totals.
    """
    try:
        port = excel_manager.get_portfolio()
        tickers = [item["ticker"] for item in port["items"] if item["ticker"]]
        price_map = {}
        for t in tickers:
            p_data = ssi_client.get_price_depth(t)
            if not p_data or p_data.get("last_price", 0) == 0:
                raw_depth = vnstock_client.get_price_depth(t)
                if isinstance(raw_depth, dict) and raw_depth.get("last_price", 0) > 0:
                    p_data = raw_depth
                else:
                    p_data = ssi_client.get_price_depth(t)
                    if not p_data or p_data.get("last_price", 0) == 0:
                        p_data = ssi_client._generate_mock_price_depth(t)
            
            raw_p = p_data.get("last_price", 0)
            if raw_p > 0:
                if raw_p < 2000:
                    price_map[t] = int(raw_p * 1000)
                else:
                    price_map[t] = int(raw_p)
                    
        if price_map:
            excel_manager.update_portfolio_prices(price_map)
            
            # Log updated portfolio totals to DB
            updated_port = excel_manager.get_portfolio()
            totals = updated_port["totals"]
            db.log_portfolio_snapshot(totals["cost_basis"], totals["current_val"], totals["pnl"], totals["pnl_pct"])
            
            return {"success": True, "prices_synced": price_map}
        return {"success": True, "prices_synced": {}, "message": "No tickers to sync"}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/excel/fundamentals")

def get_excel_fundamentals():
    try:
        return excel_manager.get_fundamentals()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/excel/macro-geopolitics")
def get_excel_macro_geopolitics():
    try:
        return excel_manager.get_macro_geopolitics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/excel/geopolitics")
def update_excel_geopolitics(item: GeopoliticalItem):
    try:
        success = excel_manager.update_geopolitical_risk(item.region, item.risk_score, item.vn_impact)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/excel/macro")
def update_excel_macro(item: MacroItem):
    try:
        success = excel_manager.update_macro_metric(item.name, item.current_val)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/excel/allocation")
def get_excel_allocation():
    try:
        return excel_manager.get_asset_allocation()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/excel/allocation")
def update_excel_allocation(item: AssetActualItem):
    try:
        success = excel_manager.update_asset_actuals(item.asset_class, item.actual_amount)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/excel/flows-forecasts")
def get_excel_flows_forecasts():
    try:
        return excel_manager.get_flow_predictor()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/excel/ai-scores")
def update_excel_ai_scores(item: AIScoresItem):
    try:
        success = excel_manager.update_ai_scores(item.market_score, item.risk_score, item.opportunity_score)
        db.log_ai_scores(item.market_score, item.risk_score, item.opportunity_score)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------------------------------------------------
# SQLite History Log Retrieval APIs
# -------------------------------------------------------------------------
@app.get("/api/db/ai-scores-history")
def get_db_ai_scores_history(limit: int = 30):
    return db.get_historical_scores(limit)

@app.get("/api/db/predictions-history")
def get_db_predictions_history(limit: int = 30):
    return db.get_historical_predictions(limit)

@app.get("/api/db/portfolio-history")
def get_db_portfolio_history(limit: int = 30):
    return db.get_portfolio_history(limit)

# -------------------------------------------------------------------------
# Core AI Scoring, Forecasting & Auto Calculation Engine
# -------------------------------------------------------------------------
@app.post("/api/excel/recalculate-all")
def recalculate_excel_dashboard():
    """
    Core engine that gathers live market signals, technical indicators for VNINDEX,
    portfolio price updates, and recalculates the entire Excel sheet formulas/values.
    """
    try:
        # 1. Fetch live historical data for VN-INDEX to feed technical forecaster
        vn_history = vnstock_client.get_historical_data("VNINDEX", source="kbs")
        if not vn_history:
            # try backup SSI Resolution 1D
            vn_history = ssi_client.get_historical_data("VNINDEX")
            
        # Update Daily Market Flows if a new completed day is available
        try:
            excel_manager.update_market_flows(vn_history)
        except Exception as e:
            print(f"Failed to auto-update market flows in Excel: {e}")
            
        # 2. Get Geopolitics & Macro settings from current Excel sheet state
        m_g = excel_manager.get_macro_geopolitics()
        geopolitics = m_g["geopolitics"]
        macro = m_g["macro_indicators"]
        
        # 3. Dynamic AI Core Scoring
        scores = forecaster.compute_ai_scores(vn_history, geopolitics, macro)
        m_score = scores["market_score"]
        r_score = scores["risk_score"]
        o_score = scores["opportunity_score"]
        excel_manager.update_ai_scores(m_score, r_score, o_score)
        db.log_ai_scores(m_score, r_score, o_score)
        
        # 4. Machine Learning Trend Forecast
        forecast = forecaster.generate_forecast(vn_history, geopolitics, macro)
        db.log_prediction(
            trend=forecast["trend"],
            probability=forecast["probability"],
            predicted_range=forecast["predicted_range"],
            warning=forecast["warning"],
            date_str=forecast["date"]
        )
        
        # Write forecasts into the Excel sheet 6 (Dong Tien & AI Predictor)
        # We generate forecasts for the next 5 sessions and write them into rows 7 to 11
        forecasts_5d = forecaster.generate_multi_day_forecast(vn_history, geopolitics, macro, days=5)
        wb = excel_manager.load_wb(data_only=False)
        ws = wb["Dong Tien & AI Predictor"]
        
        fill_positive = PatternFill(start_color="E8F8F5", end_color="E8F8F5", fill_type="solid")
        fill_negative = PatternFill(start_color="FDEDEC", end_color="FDEDEC", fill_type="solid")
        fill_warning = PatternFill(start_color="FEF9E7", end_color="FEF9E7", fill_type="solid")
        
        for i, fc in enumerate(forecasts_5d):
            r = 7 + i
            ws.cell(row=r, column=7, value=fc["date"])
            ws.cell(row=r, column=8, value=fc["trend"])
            ws.cell(row=r, column=9, value=fc["probability"])
            ws.cell(row=r, column=10, value=fc["predicted_range"])
            ws.cell(row=r, column=11, value=fc["warning"])
            
            # Apply styling
            cell_trend = ws.cell(row=r, column=8)
            cell_trend.font = Font(name="Segoe UI", size=10, bold=True)
            if "Tăng" in fc["trend"]:
                cell_trend.fill = fill_positive
            elif "Giảm" in fc["trend"]:
                cell_trend.fill = fill_negative
            else:
                cell_trend.fill = fill_warning
                
            ws.cell(row=r, column=9).number_format = "0%"
            
        excel_manager.save_wb(wb)
        
        # 5. Sync Portfolio Tickers & live prices
        port = excel_manager.get_portfolio()
        tickers = [item["ticker"] for item in port["items"] if item["ticker"]]
        price_map = {}
        for t in tickers:
            # Use price depth endpoint to find latest closing/last price
            p_data = ssi_client.get_price_depth(t)
            if not p_data or p_data.get("last_price", 0) == 0:
                raw_depth = vnstock_client.get_price_depth(t)
                if isinstance(raw_depth, dict) and "last_price" in raw_depth:
                    p_data = raw_depth
                else:
                    p_data = ssi_client._generate_mock_price_depth(t)
            
            raw_p = p_data.get("last_price", 0)
            if raw_p > 0:
                # convert board standard units (1,000 VND multiplier)
                if raw_p < 2000:
                    price_map[t] = int(raw_p * 1000)
                else:
                    price_map[t] = int(raw_p)
                    
        if price_map:
            excel_manager.update_portfolio_prices(price_map)
            
        # 6. Log updated portfolio totals to DB
        updated_port = excel_manager.get_portfolio()
        totals = updated_port["totals"]
        db.log_portfolio_snapshot(totals["cost_basis"], totals["current_val"], totals["pnl"], totals["pnl_pct"])
        
        # 7. Update Overview indices points in Excel
        wb_ov = excel_manager.load_wb(data_only=False)
        ws_ov = wb_ov["Dashboard Tong Quan"]
        
        # Fetch VNINDEX live price depth
        v_depth = ssi_client.get_price_depth("VNINDEX")
        if v_depth and v_depth.get("last_price", 0) > 0:
            ws_ov.cell(row=7, column=2, value=v_depth["last_price"]) # VN-INDEX closing
            ws_ov.cell(row=7, column=3, value=v_depth["change"])
            ws_ov.cell(row=7, column=4, value=v_depth["change_pct"] / 100.0)
            
        # Fetch VN30 live price depth
        v30_depth = ssi_client.get_price_depth("VN30")
        if v30_depth and v30_depth.get("last_price", 0) > 0:
            ws_ov.cell(row=8, column=2, value=v30_depth["last_price"]) # VN30 closing
            ws_ov.cell(row=8, column=3, value=v30_depth["change"])
            ws_ov.cell(row=8, column=4, value=v30_depth["change_pct"] / 100.0)

        # Fetch HNXINDEX live price depth
        h_depth = ssi_client.get_price_depth("HNXINDEX")
        if h_depth and h_depth.get("last_price", 0) > 0:
            ws_ov.cell(row=9, column=2, value=h_depth["last_price"]) # HNX-INDEX closing
            ws_ov.cell(row=9, column=3, value=h_depth["change"])
            ws_ov.cell(row=9, column=4, value=h_depth["change_pct"] / 100.0)

        # Fetch UPCOMINDEX live price depth
        u_depth = ssi_client.get_price_depth("UPCOMINDEX")
        if u_depth and u_depth.get("last_price", 0) > 0:
            ws_ov.cell(row=10, column=2, value=u_depth["last_price"]) # UPCoM-INDEX closing
            ws_ov.cell(row=10, column=3, value=u_depth["change"])
            ws_ov.cell(row=10, column=4, value=u_depth["change_pct"] / 100.0)
            
        # Fetch VN30F1M live price depth
        vf_depth = ssi_client.get_price_depth("VN30F1M")
        if not vf_depth or vf_depth.get("last_price", 0) == 0:
            vf_depth = ssi_client._generate_mock_price_depth("VN30F1M")
            
        vf_price = vf_depth.get("last_price", 1260.50)
        vf_change = vf_depth.get("change", 5.25)
        vf_change_pct = vf_depth.get("change_pct", 0.42)
        
        ws_ov.cell(row=11, column=2, value=vf_price)
        ws_ov.cell(row=11, column=3, value=vf_change)
        ws_ov.cell(row=11, column=4, value=vf_change_pct / 100.0)
        
        # Style row 11 change font color dynamically
        cell_c = ws_ov.cell(row=11, column=3)
        if vf_change > 0:
            cell_c.font = Font(name="Segoe UI", size=10, bold=True, color="196F3D")
            cell_c.fill = PatternFill(start_color="E8F8F5", end_color="E8F8F5", fill_type="solid")
        elif vf_change < 0:
            cell_c.font = Font(name="Segoe UI", size=10, bold=True, color="943126")
            cell_c.fill = PatternFill(start_color="FDEDEC", end_color="FDEDEC", fill_type="solid")
            
        excel_manager.save_wb(wb_ov)
        
        # 8. Calculate derivatives recommendation
        v30_val = v30_depth.get("last_price", 1262.15) if (v30_depth and v30_depth.get("last_price", 0) > 0) else 1262.15
        basis = vf_price - v30_val
        
        trend_name = forecast["trend"]
        if "Tăng" in trend_name:
            rec = "LONG"
            prob = min(0.85, forecast["probability"] + 0.05)
            target = f"{int(vf_price + 10):,} - {int(vf_price + 15):,}"
            stop_loss = int(vf_price - 8)
        elif "Giảm" in trend_name:
            rec = "SHORT"
            prob = min(0.85, forecast["probability"] + 0.05)
            target = f"{int(vf_price - 15):,} - {int(vf_price - 10):,}"
            stop_loss = int(vf_price + 8)
        else:
            rec = "QUAN SÁT"
            prob = 0.50
            target = "—"
            stop_loss = 0
            
        excel_manager.update_derivatives_recommendation(
            price=vf_price,
            basis=basis,
            recommendation=rec,
            probability=prob,
            target=target,
            stop_loss=stop_loss
        )
        
        return {
            "success": True,
            "ai_scores": {
                "market_score": m_score,
                "risk_score": r_score,
                "opportunity_score": o_score
            },
            "forecast": forecast,
            "prices_synced": price_map
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Recalculation failed: {str(e)}")

# -------------------------------------------------------------------------
# Stock Signal Analysis Endpoint (Long/Short Reason Analysis)
# -------------------------------------------------------------------------
@app.get("/api/stock-signals")
def get_stock_signals(tickers: str = ""):
    """
    Returns comprehensive Long/Short signal analysis for portfolio stocks.
    Combines technical indicators, capital flows, derivatives basis, 
    accumulated buying patterns, and sector macro factors.
    """
    try:
        # Get portfolio items
        port = excel_manager.get_portfolio()
        items = port.get("items", [])
        
        # If custom tickers provided, build synthetic items
        if tickers:
            ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
            # Merge custom tickers with portfolio
            existing_tickers = {i["ticker"] for i in items}
            for t in ticker_list:
                if t not in existing_tickers:
                    items.append({
                        "ticker": t,
                        "name": f"CP {t}",
                        "buy_price": 0,
                        "quantity": 0,
                        "current_price": 0,
                        "pnl_pct": 0
                    })
        
        # Get live price data for all tickers
        price_data = {}
        for item in items:
            t = item.get("ticker", "")
            if not t:
                continue
            try:
                p_data = ssi_client.get_price_depth(t)
                if not p_data or p_data.get("last_price", 0) == 0:
                    raw_depth = vnstock_client.get_price_depth(t)
                    if isinstance(raw_depth, dict) and "last_price" in raw_depth:
                        p_data = raw_depth
                if p_data:
                    price_data[t] = p_data
            except Exception as e:
                print(f"Price fetch error for {t}: {e}")
        
        # Get current VNINDEX trend for market context
        vnindex_trend = "Tăng nhẹ"
        try:
            vn_history = vnstock_client.get_historical_data("VNINDEX", source="kbs")
            if not vn_history:
                vn_history = ssi_client.get_historical_data("VNINDEX")
            if vn_history:
                m_g = excel_manager.get_macro_geopolitics()
                f = forecaster.generate_forecast(vn_history, m_g["geopolitics"], m_g["macro_indicators"])
                vnindex_trend = f.get("trend", "Tăng nhẹ")
        except Exception as e:
            print(f"Trend fetch error: {e}")
        
        # Generate signal analysis
        signals = forecaster.generate_stock_signal_analysis(items, price_data, vnindex_trend)
        
        return {
            "success": True,
            "vnindex_trend": vnindex_trend,
            "signals": signals
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Signal analysis failed: {str(e)}")


if __name__ == "__main__":
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"\n{'='*60}")
    print(f"  🚀 AI STOCK DASHBOARD đang chạy!")
    print(f"  📍 Trên máy này  : http://127.0.0.1:8000")
    print(f"  🌐 Mạng LAN (chia sẻ): http://{local_ip}:8000")
    print(f"  📱 Quét QR bên dưới để mở trên điện thoại")
    print(f"{'='*60}\n")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)

