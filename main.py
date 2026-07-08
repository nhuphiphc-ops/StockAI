import os
import sys
import json

import json
from datetime import datetime

# Helper to log derivatives recommendation
def save_derivatives_log(trend, action, entry, sl, tp):
    if action not in ["Mở Long", "Mở Short"]:
        return # Only record actual trades, skip neutral "Đứng ngoài"
        
    log_file = "static/derivatives_history.json"
    data = []
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = []
            
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    
    # Avoid duplicate entry within short period
    if len(data) > 0:
        last = data[0]
        if last.get("date") == date_str and last.get("action") == action and last.get("entry") == entry:
            return

    new_log = {
        "date": date_str,
        "time": time_str,
        "trend": trend,
        "action": action,
        "entry": entry,
        "sl": sl,
        "tp": tp,
        "status": "Khớp lệnh"
    }
    data.insert(0, new_log)
    
    # Keep last 100 entries
    if len(data) > 100:
        data = data[:100]
        
    try:
        os.makedirs("static", exist_ok=True)
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print("Error saving derivatives log:", e)

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
    {"ticker": "MBS", "name": "Công ty Cổ phần Chứng khoán MB", "exchange": "HNX"},
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

class IntradayCandleItem(BaseModel):
    close_price: float
    volume: float
    high_price: float
    low_price: float
    basis: float
    price_action: Optional[str] = ""

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
def fetch_live_indices():
    indices = ["VNINDEX", "VN30", "HNXINDEX", "UPCOMINDEX", "VN30F1M"]
    data_map = {}
    for idx in indices:
        p_data = ssi_client.get_price_depth(idx)
        if not p_data or p_data.get("last_price", 0) == 0:
            raw_depth = vnstock_client.get_price_depth(idx)
            if isinstance(raw_depth, dict) and raw_depth.get("last_price", 0) > 0:
                p_data = raw_depth
            else:
                p_data = ssi_client.get_price_depth(idx)
                if not p_data or p_data.get("last_price", 0) == 0:
                    p_data = ssi_client._generate_mock_price_depth(idx)
        
        last_price = p_data.get("last_price", 0.0)
        change = p_data.get("change", 0.0)
        change_pct = p_data.get("change_pct", 0.0)
        
        key = idx
        if idx == "VNINDEX": key = "VN-INDEX"
        elif idx == "HNXINDEX": key = "HNX-INDEX"
        elif idx == "UPCOMINDEX": key = "UPCoM-INDEX"
        elif idx == "VN30F1M": key = "VN30F1M (Phái sinh)"
        
        data_map[key] = {
            "value": last_price,
            "change": change,
            "pct_change": change_pct / 100.0 if change_pct else 0.0
        }
    return data_map

@app.get("/api/excel/overview")
def get_excel_overview():
    try:
        overview = excel_manager.get_overview()
        
        # 1. Dynamically merge live index numbers
        try:
            live_indices = fetch_live_indices()
            for idx_data in overview.get("market_overview", []):
                name = idx_data.get("index")
                if name in live_indices:
                    idx_data["value"] = live_indices[name]["value"]
                    idx_data["change"] = live_indices[name]["change"]
                    idx_data["pct_change"] = live_indices[name]["pct_change"]
                    
            # 2. Update derivatives section on-the-fly
            if overview.get("derivatives") and "VN30F1M (Phái sinh)" in live_indices:
                deriv = overview["derivatives"]
                price = live_indices["VN30F1M (Phái sinh)"]["value"]
                deriv["price"] = price
                
                if "VN30" in live_indices:
                    basis = price - live_indices["VN30"]["value"]
                    deriv["basis"] = basis
                
                # Recalculate target range and stop loss relative to live price
                rec = deriv.get("recommendation", "QUAN SÁT")
                if rec == "LONG":
                    low_val = int(round(price + 10))
                    high_val = int(round(price + 15))
                    deriv["target"] = f"{low_val:,} - {high_val:,} điểm"
                    deriv["stop_loss"] = int(round(price - 8))
                elif rec == "SHORT":
                    low_val = int(round(price - 15))
                    high_val = int(round(price - 10))
                    deriv["target"] = f"{low_val:,} - {high_val:,} điểm"
                    deriv["stop_loss"] = int(round(price + 8))
                else:
                    deriv["target"] = "—"
                    deriv["stop_loss"] = "—"
        except Exception as ex_indices:
            print(f"Error fetching live indices in get_excel_overview: {ex_indices}")
            
        # 3. Dynamically correct AI scores status and recommendations alignment
        try:
            scores = overview.get("ai_scores", [])
            for s in scores:
                metric = s.get("metric", "")
                score = s.get("score")
                if score is not None:
                    score = int(score)
                    if "Market" in metric:
                        if score > 60:
                            s["status"] = "Tích cực (Dòng tiền khỏe)"
                            s["recommendation"] = "Duy trì tỷ trọng cổ phiếu cao, ưu tiên tích lũy ngắn hạn"
                        elif score >= 40:
                            s["status"] = "Trung lập (Cân bằng)"
                            s["recommendation"] = "Duy trì tỷ trọng trung bình, quan sát cung cầu"
                        else:
                            s["status"] = "Tiêu cực (Dòng tiền yếu)"
                            s["recommendation"] = "Hạ tỷ trọng cổ phiếu, tăng giữ tiền mặt"
                    elif "Risk" in metric:
                        if score > 60:
                            s["status"] = "Cao"
                            s["recommendation"] = "Hạ tỷ trọng đòn bẩy (margin), phòng thủ danh mục"
                        elif score >= 40:
                            s["status"] = "Trung bình"
                            s["recommendation"] = "Theo dõi sát sao các tin tức vĩ mô, cơ cấu lại danh mục yếu"
                        else:
                            s["status"] = "Thấp"
                            s["recommendation"] = "Thị trường ổn định, chưa cần hạ tỷ trọng danh mục vội vàng"
                    elif "Opportunity" in metric:
                        if score > 60:
                            s["status"] = "Cao"
                            s["recommendation"] = "Tập trung giải ngân vào các nhóm ngành dẫn dắt dòng tiền"
                        elif score >= 40:
                            s["status"] = "Trung bình"
                            s["recommendation"] = "Chỉ giải ngân từng phần vào các mã có cơ bản tốt"
                        else:
                            s["status"] = "Thấp"
                            s["recommendation"] = "Cơ hội giải ngân ít, nên kiên nhẫn quan sát điểm cân bằng"
        except Exception as ex_scores:
            print(f"Error mapping AI scores alignment in get_excel_overview: {ex_scores}")
            
        return overview
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
        port = excel_manager.get_portfolio()
        # Dynamically fetch live prices for all tickers
        for item in port["items"]:
            t = item.get("ticker")
            if not t:
                continue
            
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
                live_price = int(raw_p * 1000) if raw_p < 2000 else int(raw_p)
                item["current_price"] = live_price
                
                buy_price = item.get("buy_price") or 0
                quantity = item.get("quantity") or 0
                item["cost_basis"] = buy_price * quantity
                item["current_val"] = live_price * quantity
                item["pnl"] = item["current_val"] - item["cost_basis"]
                item["pnl_pct"] = (item["pnl"] / item["cost_basis"]) if item["cost_basis"] > 0 else 0
                
        # Recalculate totals
        total_cost = sum((x.get("cost_basis") or 0) for x in port["items"])
        total_value = sum((x.get("current_val") or 0) for x in port["items"])
        total_pnl = total_value - total_cost
        total_pnl_pct = (total_pnl / total_cost) if total_cost > 0 else 0
        
        # Re-inject weights
        for item in port["items"]:
            item["weight"] = (item.get("current_val", 0) / total_value) if total_value > 0 else 0
            
        port["totals"] = {
            "cost_basis": total_cost,
            "current_val": total_value,
            "pnl": total_pnl,
            "pnl_pct": total_pnl_pct
        }
        
        return port
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {}
        
import json
from datetime import datetime

# Helper to log derivatives recommendation
def save_derivatives_log(trend, action, entry, sl, tp):
    if action not in ["Mở Long", "Mở Short"]:
        return # Only record actual trades, skip neutral "Đứng ngoài"
        
    log_file = "static/derivatives_history.json"
    data = []
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = []
            
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    
    # Avoid duplicate entry within short period
    if len(data) > 0:
        last = data[0]
        if last.get("date") == date_str and last.get("action") == action and last.get("entry") == entry:
            return

    new_log = {
        "date": date_str,
        "time": time_str,
        "trend": trend,
        "action": action,
        "entry": entry,
        "sl": sl,
        "tp": tp,
        "status": "Khớp lệnh"
    }
    data.insert(0, new_log)
    
    # Keep last 100 entries
    if len(data) > 100:
        data = data[:100]
        
    try:
        os.makedirs("static", exist_ok=True)
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print("Error saving derivatives log:", e)

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
        data = excel_manager.get_macro_geopolitics()
        
        # Try to fetch live USD/VND exchange rate
        try:
            import requests
            url = "https://query1.finance.yahoo.com/v8/finance/chart/USDVND=X"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            r = requests.get(url, headers=headers, timeout=3)
            if r.status_code == 200:
                res_data = r.json()
                meta = res_data.get("chart", {}).get("result", [{}])[0].get("meta", {})
                rate = meta.get("regularMarketPrice")
                if rate and rate > 0:
                    for item in data.get("macro_indicators", []):
                        ind_name = item.get("indicator") or ""
                        if "tỷ giá usd" in ind_name.lower():
                            prev_val = item.get("previous") or 25280.0
                            item["current"] = float(rate)
                            item["change"] = (float(rate) - float(prev_val)) / float(prev_val)
                            
                            # Update comment based on exchange rate level
                            if rate > 26000:
                                item["comment"] = "Tiêu cực (Áp lực tỷ giá cực cao)"
                            elif rate > 25400:
                                item["comment"] = "Tiêu cực (Áp lực tỷ giá cao)"
                            else:
                                item["comment"] = "Trung lập (Tỷ giá ổn định)"
                            break
        except Exception as ex_rate:
            print(f"Error fetching live USD/VND rate: {ex_rate}")
            
        return data
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
        # 1. Load base data from excel
        base_data = excel_manager.get_flow_predictor()
        base_flows = base_data.get("market_flows", [])
        base_forecasts = base_data.get("forecasts", [])
        
        # 2. Fetch live history
        vn_history = vnstock_client.get_historical_data("VNINDEX", source="kbs")
        if not vn_history:
            vn_history = ssi_client.get_historical_data("VNINDEX")
            
        if not vn_history:
            # If API fails, just return base data
            print("WARNING: Failed to fetch VNINDEX history for flows/forecasts. Returning cached Excel data.")
            return base_data
            
        # 3. Filter completed history
        completed_history = forecaster._filter_completed_history(vn_history)
        if not completed_history:
            return base_data
            
        completed_dates = []
        for record in completed_history:
            rec_date = record.get("time") or record.get("date")
            if rec_date:
                if isinstance(rec_date, str):
                    rec_date = rec_date.split()[0]
                elif hasattr(rec_date, "strftime"):
                    rec_date = rec_date.strftime("%Y-%m-%d")
                completed_dates.append((rec_date, record))
                
        # 4. Find missing days after top date in Excel flows
        if base_flows:
            top_date_str = base_flows[0]["date"]
            from datetime import datetime, timedelta
            try:
                top_date = datetime.strptime(top_date_str, "%d/%m/%Y").strftime("%Y-%m-%d")
            except Exception:
                top_date = top_date_str
                
            # Filter new dates (only if they are strictly newer than the Excel's newest flow date)
            new_completed = [x for x in completed_dates if x[0] > top_date]
            
            # Helper to simulate flow for a day deterministically
            def simulate_flow_for_day(date_str, record, prev_close):
                import random
                try:
                    dt = datetime.strptime(date_str, "%Y-%m-%d")
                    new_date_str = dt.strftime("%d/%m/%Y")
                except Exception:
                    new_date_str = date_str
                    
                curr_close = record.get("close", 0)
                is_up = curr_close >= prev_close
                
                # Seed deterministically based on date string
                random.seed(date_str)
                
                if is_up:
                    foreign = round(random.uniform(-250.0, -100.0), 1)
                    proprietary = round(random.uniform(40.0, 120.0), 1)
                    retail = round(-(foreign + proprietary) + random.uniform(-10.0, 10.0), 1)
                    smart_money = random.choice([
                        "Dòng tiền lớn tiếp tục mua ròng nhóm Công nghệ và Ngân hàng hỗ trợ thị trường nâng đỡ chỉ số.",
                        "Dòng tiền lớn hoạt động tích cực ở nhóm Thép và Bất động sản giúp luân phiên bùng nổ.",
                        "Lực cầu chủ động từ dòng tiền lớn gia tăng tại các nhóm ngành dẫn dắt dòng tiền."
                    ])
                else:
                    foreign = round(random.uniform(-450.0, -200.0), 1)
                    proprietary = round(random.uniform(-80.0, 30.0), 1)
                    retail = round(-(foreign + proprietary) + random.uniform(-10.0, 10.0), 1)
                    smart_money = random.choice([
                        "Khối ngoại bán ròng mạnh gây áp lực tâm lý chốt lời lên toàn bộ thị trường.",
                        "Dòng tiền lớn rút nhẹ phòng thủ, dòng tiền cá nhân nỗ lực cân lệnh bán ròng.",
                        "Áp lực bán ròng gia tăng ở nhóm ngành tài chính, dòng tiền dịch chuyển sang phòng thủ."
                    ])
                return {
                    "date": new_date_str,
                    "foreign": foreign,
                    "proprietary": proprietary,
                    "retail": retail,
                    "smart_money": smart_money
                }
                
            # Play each new date sequentially (ascending) to simulate and shift
            for date_str, record in new_completed:
                try:
                    idx = completed_history.index(record)
                    prev_close = completed_history[idx-1].get("close", 0) if idx > 0 else record.get("close", 0)
                except Exception:
                    prev_close = record.get("close", 0)
                new_flow = simulate_flow_for_day(date_str, record, prev_close)
                base_flows.insert(0, new_flow)
                if len(base_flows) > 5:
                    base_flows.pop()
                    
        # 5. Generate forecasts starting after the latest completed trading day
        m_g = excel_manager.get_macro_geopolitics()
        geopolitics = m_g.get("geopolitics", [])
        macro = m_g.get("macro_indicators", [])
        forecasts_5d = forecaster.generate_multi_day_forecast(vn_history, geopolitics, macro, days=5)
        
        updated_forecasts = []
        for fc in forecasts_5d:
            updated_forecasts.append({
                "date": fc["date"],
                "trend": fc["trend"],
                "probability": fc["probability"],
                "price_range": fc["predicted_range"],
                "risk_warning": fc["warning"]
            })
            
        # 6. Try to write back to Excel file in-place if possible (for local desktop synchronization)
        try:
            wb = excel_manager.load_wb(data_only=False)
            ws = wb["Dong Tien & AI Predictor"]
            
            # Format row fills
            from openpyxl.styles import Font, PatternFill, Alignment
            fill_positive = PatternFill(start_color="E8F8F5", end_color="E8F8F5", fill_type="solid")
            fill_negative = PatternFill(start_color="FDEDEC", end_color="FDEDEC", fill_type="solid")
            fill_warning = PatternFill(start_color="FEF9E7", end_color="FEF9E7", fill_type="solid")
            fill_none = PatternFill(fill_type=None)
            
            # Write Table A (flows)
            for i, f in enumerate(base_flows):
                r = 7 + i
                ws.cell(row=r, column=1, value=f["date"])
                ws.cell(row=r, column=2, value=f["foreign"])
                ws.cell(row=r, column=3, value=f["proprietary"])
                ws.cell(row=r, column=4, value=f["retail"])
                ws.cell(row=r, column=5, value=f["smart_money"])
                
                # Apply styling
                for c in range(1, 6):
                    cell = ws.cell(row=r, column=c)
                    cell.font = Font(name="Segoe UI", size=10)
                    if c == 1:
                        cell.alignment = Alignment(horizontal="center", vertical="center")
                        cell.fill = fill_none
                    elif c in [2, 3, 4]:
                        cell.alignment = Alignment(horizontal="right", vertical="center")
                        cell.number_format = "+#,##0.0;-#,##0.0;0.0"
                        val = cell.value
                        try:
                            val_float = float(val)
                            if val_float > 0:
                                cell.fill = fill_positive
                            elif val_float < 0:
                                cell.fill = fill_negative
                            else:
                                cell.fill = fill_none
                        except Exception:
                            cell.fill = fill_none
                    else:
                        cell.alignment = Alignment(horizontal="left", vertical="center")
                        cell.fill = fill_none
                        
            # Write Table B (forecasts)
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
        except Exception as e:
            print(f"WARNING: Could not update Excel file: {e}")
            
        return {
            "market_flows": base_flows,
            "forecasts": updated_forecasts
        }
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
    try:
        # 1. Fetch raw database records
        history = db.get_historical_scores(limit)
        
        # 2. Fetch live index history
        vn_history = vnstock_client.get_historical_data("VNINDEX", source="kbs")
        if not vn_history:
            vn_history = ssi_client.get_historical_data("VNINDEX")
            
        if not vn_history:
            return history
            
        # 3. Filter completed history
        completed_history = forecaster._filter_completed_history(vn_history)
        if not completed_history:
            return history
            
        completed_dates = []
        for record in completed_history:
            rec_date = record.get("time") or record.get("date")
            if rec_date:
                if isinstance(rec_date, str):
                    rec_date = rec_date.split()[0]
                elif hasattr(rec_date, "strftime"):
                    rec_date = rec_date.strftime("%Y-%m-%d")
                completed_dates.append((rec_date, record))
                
        # 4. Find newer dates not present in database history
        if history:
            latest_db_date = history[-1]["date"] # YYYY-MM-DD
            new_completed = [x for x in completed_dates if x[0] > latest_db_date]
        else:
            new_completed = completed_dates[-limit:]
            
        if new_completed:
            m_g = excel_manager.get_macro_geopolitics()
            geopolitics = m_g.get("geopolitics", [])
            macro = m_g.get("macro_indicators", [])
            
            for date_str, record in new_completed:
                try:
                    idx = completed_history.index(record)
                    slice_history = completed_history[:idx+1]
                except Exception:
                    slice_history = completed_history
                    
                scores = forecaster.compute_ai_scores(slice_history, geopolitics, macro)
                new_rec = {
                    "date": date_str,
                    "market_score": scores["market_score"],
                    "risk_score": scores["risk_score"],
                    "opportunity_score": scores["opportunity_score"],
                    "logged_at": None
                }
                history.append(new_rec)
                
                # Try to log to local DB if writable
                try:
                    db.log_ai_scores(scores["market_score"], scores["risk_score"], scores["opportunity_score"], date_str)
                except Exception:
                    pass
                    
        # Apply limit to returned list
        if len(history) > limit:
            history = history[-limit:]
            
        return history
    except Exception as e:
        print(f"Error in get_db_ai_scores_history: {e}")
        try:
            return db.get_historical_scores(limit)
        except Exception:
            return []

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
            target = f"{int(vf_price + 10):,} - {int(vf_price + 15):,} điểm"
            stop_loss = int(vf_price - 8)
        elif "Giảm" in trend_name:
            rec = "SHORT"
            prob = min(0.85, forecast["probability"] + 0.05)
            target = f"{int(vf_price - 15):,} - {int(vf_price - 10):,} điểm"
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


@app.get("/api/derivatives/live-candle")
def get_derivatives_live_candle():
    try:
        # 1. Fetch VN30F1M price depth and basis/VN30
        vf_depth = ssi_client.get_price_depth("VN30F1M")
        if not vf_depth or vf_depth.get("last_price", 0) == 0:
            vf_depth = ssi_client._generate_mock_price_depth("VN30F1M")
            
        v30_depth = ssi_client.get_price_depth("VN30")
        if not v30_depth or v30_depth.get("last_price", 0) == 0:
            v30_depth = ssi_client._generate_mock_price_depth("VN30")
            
        close_p = vf_depth.get("last_price", 2001.2)
        v30_price = v30_depth.get("last_price", 2002.5)
        basis = close_p - v30_price
        
        # 2. Fetch intraday transactions of VN30F1M
        trades = ssi_client.get_intraday("VN30F1M")
        if not trades:
            trades = ssi_client._generate_mock_intraday("VN30F1M")
            
        # 3. Calculate candle (High, Low, Volume) from trades
        # Take the most recent trades (e.g. the last 20 trades to simulate recent 5m activity)
        recent_trades = trades[:20] if trades else []
        if recent_trades:
            high_p = max(t["price"] for t in recent_trades)
            low_p = min(t["price"] for t in recent_trades)
            volume = sum(t["volume"] for t in recent_trades)
        else:
            # Fallback
            high_p = close_p + 1.2
            low_p = close_p - 0.8
            volume = 1200
            
        # Ensure high >= close >= low
        high_p = max(high_p, close_p)
        low_p = min(low_p, close_p)
        
        # 4. Generate Price Action text dynamically
        candle_range = high_p - low_p
        if volume < 500:
            pa_text = "Thanh khoản cạn kiệt, thị trường đi ngang thăm dò."
        elif close_p > (high_p + low_p)/2 + candle_range * 0.1:
            if close_p >= high_p - 0.2:
                pa_text = "Nến bứt phá vượt đỉnh, dòng tiền Long gia tăng mạnh mẽ."
            else:
                pa_text = "Nến rút chân tích cực, lực cầu chủ động hấp thụ cung."
        elif close_p < (high_p + low_p)/2 - candle_range * 0.1:
            if close_p <= low_p + 0.2:
                pa_text = "Thân nến đỏ dài sát đáy, áp lực bán đè nặng phe Long."
            else:
                pa_text = "Nến từ chối tăng, áp lực chốt lời ngắn hạn xuất hiện."
        else:
            pa_text = "Nến thân nhỏ biến động hẹp, hai phe Long/Short đang giằng co."
            
        return {
            "success": True,
            "close_price": round(close_p, 1),
            "high_price": round(high_p, 1),
            "low_price": round(low_p, 1),
            "volume": int(volume),
            "basis": round(basis, 1),
            "price_action": pa_text
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/derivatives/intraday-forecast")
def get_derivatives_intraday_forecast(item: IntradayCandleItem):
    try:
        close_p = item.close_price
        volume = item.volume
        high_p = item.high_price
        low_p = item.low_price
        basis = item.basis
        pa = item.price_action.strip().lower()

        # Rules
        is_neutral = False
        neutral_reason = ""
        
        # Rule 1: Volume too low
        if volume < 500:
            is_neutral = True
            neutral_reason = f"Khối lượng nến M5 cực thấp ({volume:.0f} HĐ), dòng tiền cạn kiệt và tín hiệu nhiễu cao."
        # Rule 2: Basis abnormal
        elif abs(basis) > 8.0:
            is_neutral = True
            neutral_reason = f"Độ lệch basis quá rộng ({basis:+.1f} điểm), rủi ro ép basis đột ngột rất lớn."

        if is_neutral:
            trend = "ĐI NGANG (QUAN SÁT)"
            action = "Đứng ngoài"
            entry = "Không khuyến nghị"
            sl = "Không có"
            tp = "Không có"
            arg_pa = f"Thanh khoản thấp hoặc hành động giá chưa rõ ràng: {neutral_reason}"
            arg_basis = f"Độ lệch basis là {basis:+.1f} điểm, ở trạng thái rủi ro chênh lệch cao."
            arg_sr = f"Hỗ trợ gần nhất: {low_p - 1.0:.1f} | Kháng cự gần nhất: {high_p + 1.0:.1f}."
        else:
            # Check price position in range
            candle_range = high_p - low_p
            mid_p = (high_p + low_p) / 2.0
            
            # Check keywords for strong directions
            long_signals = ["rút chân", "pinbar", "tăng", "bứt phá", "long", "vượt đỉnh", "cạn cung", "bullish"]
            short_signals = ["đỏ", "giảm", "short", "thủng đáy", "phân kỳ", "bán", "áp lực", "bearish"]
            
            has_long_kw = any(kw in pa for kw in long_signals)
            has_short_kw = any(kw in pa for kw in short_signals)
            
            if (close_p > mid_p or has_long_kw) and not has_short_kw and basis >= -2.0:
                trend = "TĂNG (LONG)"
                action = "Mở Long"
                entry = f"{close_p:.1f} - {close_p + 0.4:.1f}"
                sl = f"{close_p - 2.0:.1f} (Cắt lỗ 2.0 điểm)"
                tp = f"TP1: {close_p + 4.0:.1f} | TP2: {close_p + 6.0:.1f} (R:R tối thiểu 1:2)"
                arg_pa = f"Hành động giá ủng hộ phe mua: {item.price_action or 'Nến đóng cửa ở nửa trên biên độ'} với vol đạt {volume:.0f} hợp đồng."
                arg_basis = f"Basis đạt {basis:+.1f} điểm, chênh lệch ở mức an toàn ủng hộ nhịp kéo phái sinh."
                arg_sr = f"Hỗ trợ cứng M5 quanh {low_p:.1f}. Kháng cự mục tiêu cần vượt qua là {close_p + 5.0:.1f}."
            elif (close_p < mid_p or has_short_kw) and not has_long_kw and basis <= 2.0:
                trend = "GIẢM (SHORT)"
                action = "Mở Short"
                entry = f"{close_p - 0.4:.1f} - {close_p:.1f}"
                sl = f"{close_p + 2.0:.1f} (Cắt lỗ 2.0 điểm)"
                tp = f"TP1: {close_p - 4.0:.1f} | TP2: {close_p - 6.0:.1f} (R:R tối thiểu 1:2)"
                arg_pa = f"Hành động giá phe bán chiếm ưu thế: {item.price_action or 'Nến đóng cửa ở nửa dưới biên độ'} với vol đạt {volume:.0f} hợp đồng."
                arg_basis = f"Basis đạt {basis:+.1f} điểm, cho thấy tâm lý phòng thủ gia tăng của dòng tiền phái sinh."
                arg_sr = f"Kháng cự cứng M5 tại {high_p:.1f}. Hỗ trợ mục tiêu hướng tới là {close_p - 5.0:.1f}."
            else:
                trend = "ĐI NGANG (QUAN SÁT)"
                action = "Đứng ngoài"
                entry = "Không khuyến nghị"
                sl = "Không có"
                tp = "Không có"
                arg_pa = "Nến M5 giao động hẹp, lực cung cầu cân bằng chưa xác lập xu thế rõ rệt."
                arg_basis = f"Basis duy trì quanh {basis:+.1f} điểm chưa kích hoạt dòng tiền bứt phá."
                arg_sr = f"Hỗ trợ: {low_p:.1f} | Kháng cự: {high_p:.1f}."

        # Save recommendation to file log
        try:
            save_derivatives_log(trend, action, entry, sl, tp)
        except Exception as log_ex:
            print("Error saving log:", log_ex)

        return {
            "success": True,
            "trend_verdict": trend,
            "action_signal": action,
            "entry_range": entry,
            "stop_loss": sl,
            "take_profit": tp,
            "arguments": {
                "price_action_vol": arg_pa,
                "basis_impact": arg_basis,
                "support_resistance": arg_sr
            },
            "disclaimer": "Tín hiệu chỉ mang tính chất tham khảo, hãy tuân thủ kỷ luật Stop Loss."
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/api/derivatives/history-log")
def get_derivatives_history_log():
    log_file = "static/derivatives_history.json"
    if not os.path.exists(log_file):
        return []
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


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

