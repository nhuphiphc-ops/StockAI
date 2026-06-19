import requests
import json
import random
import time
from datetime import datetime, timedelta

class SsiClient:
    def __init__(self, consumer_id: str = "", consumer_secret: str = "", private_key_path: str = "", use_mock_fallback: bool = True):
        self.consumer_id = consumer_id
        self.consumer_secret = consumer_secret
        self.private_key_path = private_key_path
        self.use_mock_fallback = use_mock_fallback
        
        self.access_token = None
        self.token_expiry = 0
        self.base_url = "https://fc-data.ssi.com.vn/api/v2/Market"
        self.base_prices = {
            "FPT": 71.5, "SSI": 27.15, "VIC": 205.1, "VNM": 59.0, "HPG": 23.6, "PHC": 4.62,
            "MBB": 22.0, "TCB": 24.5, "VCB": 92.0, "ACB": 22.2, "CTD": 65.0, "HBC": 6.0,
            "VCG": 22.0, "STB": 29.0, "VPB": 18.0, "CTG": 32.0, "BID": 45.0, "VHM": 38.0,
            "VRE": 20.0, "DIG": 24.0, "DXG": 16.0, "NLG": 38.0, "VCI": 45.0, "HCM": 28.0,
            "VND": 20.0, "DGC": 115.0, "GVR": 33.0, "GAS": 78.0, "PVD": 28.0, "PVS": 38.0,
            "VN30F1M": 1964.00, "VNINDEX": 1824.53, "VN30": 1963.57, "HNXINDEX": 324.83, "UPCOMINDEX": 127.52
        }
        self.cache = {}

    def _normalize_symbol(self, symbol: str) -> str:
        s = symbol.upper().strip()
        if s in ["HNX-INDEX", "HNX_INDEX"]:
            return "HNXINDEX"
        if s in ["UPCOM-INDEX", "UPCOM_INDEX"]:
            return "UPCOMINDEX"
        return s

    def _get_cached(self, key: tuple):
        now = time.time()
        if key in self.cache:
            expiry, data = self.cache[key]
            if now < expiry:
                return data
        return None

    def _set_cached(self, key: tuple, data, duration: int):
        self.cache[key] = (time.time() + duration, data)

    def get_access_token(self) -> str:
        """
        Retrieves access token from SSI OAuth2 server.
        """
        # Return mock token if we're forcing mock
        if self.use_mock_fallback and (not self.consumer_id or self.consumer_id == "YOUR_CONSUMER_ID"):
            return "mock_ssi_access_token_123456"

        # Check if cached token is still valid
        if self.access_token and time.time() < self.token_expiry:
            return self.access_token

        try:
            url = f"{self.base_url}/AccessToken"
            payload = {
                "consumerId": self.consumer_id,
                "consumerSecret": self.consumer_secret
            }
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("data", {}).get("accessToken")
                expires_in = data.get("data", {}).get("expiresIn", 3600)
                self.token_expiry = time.time() + expires_in - 60  # Renew 1 minute early
                return self.access_token
            else:
                print(f"Warning: Failed to auth with SSI: {response.text}")
                if self.use_mock_fallback:
                    return "mock_ssi_access_token_fallback"
                raise Exception(f"SSI Auth Failed: {response.text}")
        except Exception as e:
            print(f"Error in SSI token retrieval: {e}")
            if self.use_mock_fallback:
                return "mock_ssi_access_token_fallback"
            raise e

    def get_historical_data(self, symbol: str, start_date: str = None, end_date: str = None, resolution: str = "1D") -> list:
        """
        Retrieves historical daily OHLC data.
        """
        symbol = self._normalize_symbol(symbol)
        cache_key = ("historical", symbol, start_date, end_date, resolution)
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        token = self.get_access_token()
        if token == "mock_ssi_access_token_fallback" or (self.use_mock_fallback and token.startswith("mock")):
            try:
                from vnstock import Quote
                q = Quote(symbol=symbol, source="kbs")
                if start_date and end_date:
                    df = q.history(start=start_date, end=end_date, interval="1d")
                else:
                    df = q.history(length="100", interval="1d")
                
                if df is not None and not df.empty:
                    formatted = []
                    for _, row in df.iterrows():
                        formatted.append({
                            "time": str(row.get("time", "")).split("T")[0].split(" ")[0],
                            "open": float(row.get("open", 0)),
                            "high": float(row.get("high", 0)),
                            "low": float(row.get("low", 0)),
                            "close": float(row.get("close", 0)),
                            "volume": int(row.get("volume", 0))
                        })
                    self._set_cached(cache_key, formatted, 300)
                    return formatted
            except BaseException as e:
                print(f"SSI mock mode fallback history query failed for {symbol}: {e}. Generating mock history...")
            
            mock_res = self._generate_mock_history(symbol, start_date, end_date)
            self._set_cached(cache_key, mock_res, 300)
            return mock_res

        try:
            # SSI DailyOHLC endpoint
            url = f"{self.base_url}/DailyOHLC"
            params = {
                "symbol": symbol,
                "fromDate": start_date or (datetime.now() - timedelta(days=90)).strftime("%d/%m/%Y"),
                "toDate": end_date or datetime.now().strftime("%d/%m/%Y"),
                "pageIndex": 1,
                "pageSize": 1000
            }
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=5)
            if response.status_code == 200:
                res_data = response.json()
                raw_list = res_data.get("data", [])
                
                # Format to uniform structure: {time, open, high, low, close, volume}
                formatted = []
                for item in raw_list:
                    formatted.append({
                        "time": item.get("TradingDate", ""),
                        "open": item.get("OpenPrice", 0),
                        "high": item.get("HighPrice", 0),
                        "low": item.get("LowPrice", 0),
                        "close": item.get("ClosePrice", 0),
                        "volume": item.get("TotalVolume", 0)
                    })
                self._set_cached(cache_key, formatted, 300)
                return formatted
            else:
                print(f"SSI OHLC request failed: {response.text}")
                if self.use_mock_fallback:
                    mock_res = self._generate_mock_history(symbol, start_date, end_date)
                    self._set_cached(cache_key, mock_res, 300)
                    return mock_res
                return []
        except BaseException as e:
            print(f"Error in SSI get_historical_data: {e}")
            if self.use_mock_fallback:
                mock_res = self._generate_mock_history(symbol, start_date, end_date)
                self._set_cached(cache_key, mock_res, 300)
                return mock_res
            return []

    def get_intraday(self, symbol: str) -> list:
        """
        Retrieves intraday transactions.
        """
        symbol = self._normalize_symbol(symbol)
        cache_key = ("intraday", symbol)
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        token = self.get_access_token()
        if token.startswith("mock"):
            try:
                from vnstock import Quote
                q = Quote(symbol=symbol, source="kbs")
                df = q.intraday()
                if df is not None and not df.empty:
                    formatted = []
                    for _, row in df.iterrows():
                        formatted.append({
                            "time": str(row.get("time", "")).split(" ")[-1],
                            "price": float(row.get("price", 0)),
                            "volume": int(row.get("volume", 0)),
                            "side": str(row.get("match_type", "B")).upper()
                        })
                    self._set_cached(cache_key, formatted, 30)
                    return formatted
            except BaseException as e:
                print(f"SSI mock mode fallback intraday query failed for {symbol}: {e}. Generating mock intraday...")
            
            mock_res = self._generate_mock_intraday(symbol)
            self._set_cached(cache_key, mock_res, 30)
            return mock_res

        try:
            url = f"{self.base_url}/Intraday"
            params = {"symbol": symbol, "pageIndex": 1, "pageSize": 100}
            headers = {"Authorization": f"Bearer {token}"}
            
            response = requests.get(url, params=params, headers=headers, timeout=5)
            if response.status_code == 200:
                raw_list = response.json().get("data", [])
                formatted = []
                for item in raw_list:
                    formatted.append({
                        "time": item.get("Time", ""),
                        "price": item.get("Price", 0),
                        "volume": item.get("Volume", 0),
                        "side": item.get("Side", "B")
                    })
                self._set_cached(cache_key, formatted, 30)
                return formatted
            else:
                if self.use_mock_fallback:
                    mock_res = self._generate_mock_intraday(symbol)
                    self._set_cached(cache_key, mock_res, 30)
                    return mock_res
                return []
        except BaseException as e:
            print(f"Error in SSI get_intraday: {e}")
            if self.use_mock_fallback:
                mock_res = self._generate_mock_intraday(symbol)
                self._set_cached(cache_key, mock_res, 30)
                return mock_res
            return []

    def get_price_depth(self, symbol: str) -> dict:
        """
        Retrieves best bid/ask queues.
        """
        symbol = self._normalize_symbol(symbol)
        cache_key = ("price_depth", symbol)
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        token = self.get_access_token()
        if token.startswith("mock"):
            try:
                from vnstock import Quote
                last_price = None
                change = 0.0
                change_pct = 0.0

                df_hist = None
                for src in ["kbs", "vci"]:
                    try:
                        q = Quote(symbol=symbol, source=src)
                        df_hist = q.history(length="5")
                        if df_hist is not None and not df_hist.empty:
                            break
                    except BaseException as e:
                        print(f"Index query via source {src} failed for {symbol}: {e}")

                if df_hist is not None and not df_hist.empty:
                    df_hist = df_hist.sort_values(by="time")
                    if len(df_hist) >= 1:
                        last_price = float(df_hist.iloc[-1]["close"])
                        if len(df_hist) >= 2:
                            prev_close = float(df_hist.iloc[-2]["close"])
                            change = last_price - prev_close
                            change_pct = (change / prev_close) * 100.0 if prev_close != 0 else 0.0

                if last_price is None or last_price == 0:
                    df_intra = q.intraday()
                    if df_intra is not None and not df_intra.empty:
                        if "price" in df_intra.columns:
                            last_price = float(df_intra.iloc[0]["price"])
                            if len(df_intra) >= 2:
                                prev_intra = float(df_intra.iloc[-1]["price"])
                                change = last_price - prev_intra
                                change_pct = (change / prev_intra) * 100.0 if prev_intra != 0 else 0.0

                if last_price is not None and last_price > 0:
                    import random
                    symbol_upper = symbol.upper()
                    if "VNINDEX" in symbol_upper or "VN30" in symbol_upper:
                        spread = 0.50
                        step = 0.50
                    else:
                        spread = 0.05
                        step = 0.05

                    bids = [
                        {"price": round(last_price - spread, 2), "volume": random.randint(1000, 15000) * 10},
                        {"price": round(last_price - spread - step, 2), "volume": random.randint(2000, 20000) * 10},
                        {"price": round(last_price - spread - (step * 2), 2), "volume": random.randint(3000, 30000) * 10}
                    ]
                    asks = [
                        {"price": round(last_price + spread, 2), "volume": random.randint(1000, 15000) * 10},
                        {"price": round(last_price + spread + step, 2), "volume": random.randint(2000, 20000) * 10},
                        {"price": round(last_price + spread + (step * 2), 2), "volume": random.randint(3000, 30000) * 10}
                    ]

                    # Also update self.base_prices cache so that any other mock generators (e.g. history fallback) use the updated price
                    self.base_prices[symbol_upper] = last_price

                    res = {
                        "symbol": symbol_upper,
                        "last_price": round(last_price, 2),
                        "change": round(change, 2),
                        "change_pct": round(change_pct, 2),
                        "bids": bids,
                        "asks": asks
                    }
                    self._set_cached(cache_key, res, 30)
                    return res
            except BaseException as e:
                print(f"SSI mock mode fallback price depth failed for {symbol}: {e}. Generating mock price depth...")
            
            mock_res = self._generate_mock_price_depth(symbol)
            self._set_cached(cache_key, mock_res, 30)
            return mock_res

        try:
            url = f"{self.base_url}/StockPrice"
            params = {"symbol": symbol}
            headers = {"Authorization": f"Bearer {token}"}
            
            response = requests.get(url, params=params, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json().get("data", {})
                bids = [
                    {"price": data.get("BidPrice1", 0), "volume": data.get("BidVol1", 0)},
                    {"price": data.get("BidPrice2", 0), "volume": data.get("BidVol2", 0)},
                    {"price": data.get("BidPrice3", 0), "volume": data.get("BidVol3", 0)}
                ]
                asks = [
                    {"price": data.get("AskPrice1", 0), "volume": data.get("AskVol1", 0)},
                    {"price": data.get("AskPrice2", 0), "volume": data.get("AskVol2", 0)},
                    {"price": data.get("AskPrice3", 0), "volume": data.get("AskVol3", 0)}
                ]
                res = {
                    "symbol": symbol,
                    "last_price": data.get("LastPrice", 0),
                    "change": data.get("PriceChange", 0),
                    "change_pct": data.get("PriceChangePercent", 0),
                    "bids": bids,
                    "asks": asks
                }
                self._set_cached(cache_key, res, 30)
                return res
            else:
                if self.use_mock_fallback:
                    mock_res = self._generate_mock_price_depth(symbol)
                    self._set_cached(cache_key, mock_res, 30)
                    return mock_res
                return {"bids": [], "asks": []}
        except BaseException as e:
            print(f"Error in SSI get_price_depth: {e}")
            if self.use_mock_fallback:
                mock_res = self._generate_mock_price_depth(symbol)
                self._set_cached(cache_key, mock_res, 30)
                return mock_res
            return {"bids": [], "asks": []}

    # --- MOCK GENERATORS ---
    def _generate_mock_history(self, symbol: str, start_date: str = None, end_date: str = None) -> list:
        days = 90
        start_dt = datetime.now() - timedelta(days=days)
        base_p = self.base_prices.get(symbol.upper(), 30.0)
        
        history = []
        curr_p = base_p
        
        for i in range(days):
            date_str = (start_dt + timedelta(days=i)).strftime("%Y-%m-%d")
            day_of_week = (start_dt + timedelta(days=i)).weekday()
            if day_of_week >= 5:
                continue
                
            change = random.uniform(-0.03, 0.035) * curr_p
            open_p = curr_p
            close_p = curr_p + change
            high_p = max(open_p, close_p) + random.uniform(0, 0.015) * curr_p
            low_p = min(open_p, close_p) - random.uniform(0, 0.015) * curr_p
            vol = int(random.uniform(500000, 5000000))
            
            history.append({
                "time": date_str,
                "open": round(open_p, 2),
                "high": round(high_p, 2),
                "low": round(low_p, 2),
                "close": round(close_p, 2),
                "volume": vol
            })
            curr_p = close_p
            
        return history

    def _generate_mock_intraday(self, symbol: str) -> list:
        base_p = self.base_prices.get(symbol.upper(), 30.0)
        trades = []
        now = datetime.now()
        
        for i in range(50):
            trade_time = (now - timedelta(minutes=i * 2)).strftime("%H:%M:%S")
            price = base_p + random.uniform(-0.01, 0.01) * base_p
            vol = random.randint(1, 500) * 100
            side = random.choice(["B", "S"])
            trades.append({
                "time": trade_time,
                "price": round(price, 2),
                "volume": vol,
                "side": side
            })
        return trades

    def _get_yahoo_finance_fallback(self, symbol: str) -> dict:
        symbol_upper = symbol.upper().strip()
        if symbol_upper == "VNINDEX":
            yahoo_sym = "^VNINDEX"
        elif symbol_upper == "VN30":
            yahoo_sym = "^VN30"
        elif symbol_upper == "VN30F1M":
            return None
        else:
            yahoo_sym = f"{symbol_upper}.VN"
            
        import requests
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_sym}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        try:
            r = requests.get(url, headers=headers, timeout=5)
            if r.status_code == 200:
                data = r.json()
                meta = data.get("chart", {}).get("result", [{}])[0].get("meta", {})
                raw_price = meta.get("regularMarketPrice")
                raw_prev_close = meta.get("previousClose")
                if raw_price:
                    last_price = raw_price
                    prev_close = raw_prev_close or last_price
                    
                    if last_price > 2000:
                        last_price = last_price / 1000.0
                    if prev_close > 2000:
                        prev_close = prev_close / 1000.0
                        
                    change = last_price - prev_close
                    change_pct = (change / prev_close) * 100.0 if prev_close != 0 else 0.0
                    
                    import random
                    if "VNINDEX" in symbol_upper or "VN30" in symbol_upper:
                        spread = 0.50
                        step = 0.50
                    else:
                        spread = 0.05
                        step = 0.05
                        
                    bids = [
                        {"price": round(last_price - spread, 2), "volume": random.randint(1000, 15000) * 10},
                        {"price": round(last_price - spread - step, 2), "volume": random.randint(2000, 20000) * 10},
                        {"price": round(last_price - spread - (step * 2), 2), "volume": random.randint(3000, 30000) * 10}
                    ]
                    asks = [
                        {"price": round(last_price + spread, 2), "volume": random.randint(1000, 15000) * 10},
                        {"price": round(last_price + spread + step, 2), "volume": random.randint(2000, 20000) * 10},
                        {"price": round(last_price + spread + (step * 2), 2), "volume": random.randint(3000, 30000) * 10}
                    ]
                    
                    return {
                        "symbol": symbol_upper,
                        "last_price": round(last_price, 2),
                        "change": round(change, 2),
                        "change_pct": round(change_pct, 2),
                        "bids": bids,
                        "asks": asks
                    }
        except Exception as e:
            print(f"SSI Yahoo Finance fallback failed for {symbol_upper}: {e}")
        return None

    def _generate_mock_price_depth(self, symbol: str) -> dict:
        # Try Yahoo Finance fallback first
        yahoo_res = self._get_yahoo_finance_fallback(symbol)
        if yahoo_res:
            return yahoo_res

        base_p = self.base_prices.get(symbol.upper(), 30.0)
        curr_price = base_p + random.uniform(-0.005, 0.005) * base_p
        spread = 0.05
        
        bids = [
            {"price": round(curr_price - spread, 2), "volume": random.randint(1000, 15000) * 10},
            {"price": round(curr_price - spread - 0.05, 2), "volume": random.randint(2000, 20000) * 10},
            {"price": round(curr_price - spread - 0.10, 2), "volume": random.randint(3000, 30000) * 10}
        ]
        asks = [
            {"price": round(curr_price + spread, 2), "volume": random.randint(1000, 15000) * 10},
            {"price": round(curr_price + spread + 0.05, 2), "volume": random.randint(2000, 20000) * 10},
            {"price": round(curr_price + spread + 0.10, 2), "volume": random.randint(3000, 30000) * 10}
        ]
        change = random.uniform(-2.5, 3.0)
        return {
            "symbol": symbol,
            "last_price": round(curr_price, 2),
            "change": round(change, 2),
            "change_pct": round(change / base_p * 100, 2),
            "bids": bids,
            "asks": asks
        }
