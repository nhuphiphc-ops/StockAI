import requests
import random
from datetime import datetime, timedelta

class FireAntClient:
    def __init__(self, auth_token: str = "", cookie: str = "", use_mock_fallback: bool = True):
        self.auth_token = auth_token
        self.cookie = cookie
        self.use_mock_fallback = use_mock_fallback
        self.base_url = "https://restv2.fireant.vn"

    def _get_headers(self) -> dict:
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        if self.cookie:
            headers["Cookie"] = self.cookie
        return headers

    def get_news(self, limit: int = 10) -> list:
        """
        Retrieves recent financial and stock market news.
        """
        if self.use_mock_fallback and (not self.auth_token or self.auth_token == "YOUR_BEARER_TOKEN"):
            return self._generate_mock_news(limit)

        try:
            url = f"{self.base_url}/news"
            params = {"limit": limit}
            headers = self._get_headers()
            
            response = requests.get(url, params=params, headers=headers, timeout=5)
            if response.status_code == 200:
                raw_news = response.json()
                formatted = []
                for item in raw_news:
                    formatted.append({
                        "id": item.get("id"),
                        "title": item.get("title", ""),
                        "summary": item.get("summary", ""),
                        "source": item.get("sourceName", "FireAnt"),
                        "publish_date": item.get("publishDate", datetime.now().isoformat()),
                        "url": f"https://fireant.vn/tin-tuc/{item.get('id')}" if item.get("id") else "https://fireant.vn"
                    })
                return formatted
            else:
                print(f"FireAnt news fetch failed: {response.text}")
                if self.use_mock_fallback:
                    return self._generate_mock_news(limit)
                return []
        except Exception as e:
            print(f"Error in FireAnt get_news: {e}")
            if self.use_mock_fallback:
                return self._generate_mock_news(limit)
            return []

    def get_corporate_events(self, symbol: str) -> list:
        """
        Retrieves corporate events (dividends, shareholder meetings).
        """
        if self.use_mock_fallback and (not self.auth_token or self.auth_token == "YOUR_BEARER_TOKEN"):
            return self._generate_mock_events(symbol)

        try:
            url = f"{self.base_url}/symbols/{symbol}/events"
            headers = self._get_headers()
            
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                raw_events = response.json()
                formatted = []
                for item in raw_events:
                    formatted.append({
                        "event_name": item.get("eventName", ""),
                        "ex_date": item.get("exDate", ""),
                        "record_date": item.get("recordDate", ""),
                        "payment_date": item.get("paymentDate", ""),
                        "description": item.get("description", "")
                    })
                return formatted
            else:
                print(f"FireAnt events fetch failed: {response.text}")
                if self.use_mock_fallback:
                    return self._generate_mock_events(symbol)
                return []
        except Exception as e:
            print(f"Error in FireAnt get_corporate_events: {e}")
            if self.use_mock_fallback:
                return self._generate_mock_events(symbol)
            return []

    def get_financial_indicators(self, symbol: str) -> dict:
        """
        Retrieves core financial indicators (P/E, P/B, EPS, ROA, ROE, etc.).
        """
        if self.use_mock_fallback and (not self.auth_token or self.auth_token == "YOUR_BEARER_TOKEN"):
            return self._generate_mock_indicators(symbol)

        try:
            url = f"{self.base_url}/symbols/{symbol}/financial-indicators"
            headers = self._get_headers()
            
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"FireAnt financials fetch failed: {response.text}")
                if self.use_mock_fallback:
                    return self._generate_mock_indicators(symbol)
                return {}
        except Exception as e:
            print(f"Error in FireAnt get_financial_indicators: {e}")
            if self.use_mock_fallback:
                return self._generate_mock_indicators(symbol)
            return {}

    # --- MOCK GENERATORS ---
    def _generate_mock_news(self, limit: int) -> list:
        all_news = [
            {
                "title": "Cổ phiếu ngành thép bứt phá mạnh mẽ sau công bố giá thép xây dựng tăng",
                "summary": "Nhu cầu phục hồi mạnh từ các dự án đầu tư công giúp các doanh nghiệp thép như HPG, HSG ghi nhận biên lợi nhuận gộp tích cực hơn.",
                "source": "Báo Đầu Tư",
                "publish_date": (datetime.now() - timedelta(hours=1)).isoformat(),
                "url": "https://baodautu.vn"
            },
            {
                "title": "VN-Index giằng co quanh vùng 1.250 điểm, dòng tiền luân chuyển thông minh",
                "summary": "Áp lực chốt lời tăng nhẹ ở nhóm ngân hàng nhưng nhóm bất động sản và khu công nghiệp đã nâng đỡ chỉ số thành công.",
                "source": "Vietstock",
                "publish_date": (datetime.now() - timedelta(hours=3)).isoformat(),
                "url": "https://vietstock.vn"
            },
            {
                "title": "FPT công bố kết quả kinh doanh quý 1 vượt kỳ vọng, mảng xuất khẩu phần mềm dẫn đầu",
                "summary": "Doanh thu dịch vụ CNTT tại thị trường nước ngoài đạt tăng trưởng ấn tượng 28%, động lực chính đến từ các hợp đồng quy mô lớn tại Nhật Bản và Mỹ.",
                "source": "CafeF",
                "publish_date": (datetime.now() - timedelta(hours=5)).isoformat(),
                "url": "https://cafef.vn"
            },
            {
                "title": "Khối ngoại quay lại mua ròng mạnh mã SSI và VNM trong phiên chiều",
                "summary": "Giá trị mua ròng khớp lệnh đạt hơn 150 tỷ đồng, báo hiệu xu hướng dòng vốn ngoại đang quay lại thị trường chứng khoán Việt Nam.",
                "source": "Kinh tế & Tiêu dùng",
                "publish_date": (datetime.now() - timedelta(hours=8)).isoformat(),
                "url": "https://vietnambiz.vn"
            },
            {
                "title": "Ngân hàng Nhà nước tiếp tục ổn định lãi suất điều hành hỗ trợ doanh nghiệp",
                "summary": "Dự kiến mặt bằng lãi suất cho vay sẽ đi ngang hoặc giảm nhẹ trong các quý tới nhằm hỗ trợ thúc đẩy tăng trưởng kinh tế cuối năm.",
                "source": "Thời báo Tài chính",
                "publish_date": (datetime.now() - timedelta(days=1)).isoformat(),
                "url": "https://thoibaotaichinhvietnam.vn"
            }
        ]
        return all_news[:limit]

    def _generate_mock_events(self, symbol: str) -> list:
        symbol = symbol.upper().strip()
        now = datetime.now()
        
        # Real/realistic events for main tickers
        if symbol == "FPT":
            return [
                {
                    "event_name": "Trả cổ tức đợt 2 năm 2025 bằng tiền mặt - FPT",
                    "ex_date": "2026-05-28",
                    "record_date": "2026-05-29",
                    "payment_date": "2026-06-10",
                    "description": "Tỷ lệ thực hiện: 10% (1.000 đồng/cổ phiếu)"
                },
                {
                    "event_name": "Đại hội đồng cổ đông thường niên năm 2026 - FPT",
                    "ex_date": "2026-03-05",
                    "record_date": "2026-03-06",
                    "payment_date": "—",
                    "description": "Họp vào ngày 09/04/2026 tại Hà Nội thông qua kế hoạch doanh thu và định hướng phát triển AI toàn cầu."
                }
            ]
        elif symbol == "SSI":
            return [
                {
                    "event_name": "Trả cổ tức năm 2025 bằng tiền mặt - SSI",
                    "ex_date": "2026-07-02",
                    "record_date": "2026-07-03",
                    "payment_date": "2026-07-24",
                    "description": "Tỷ lệ thực hiện: 10% (1.000 đồng/cổ phiếu). Phát hành cổ phiếu trả cổ tức tỷ lệ 20% thực hiện sau đó."
                },
                {
                    "event_name": "Đại hội đồng cổ đông thường niên năm 2026 - SSI",
                    "ex_date": "2026-03-23",
                    "record_date": "2026-03-24",
                    "payment_date": "—",
                    "description": "Họp vào ngày 23/04/2026 thông qua phương án tăng vốn điều lệ lên 30.000 tỷ đồng và chia cổ tức 30%."
                }
            ]
        elif symbol == "MBB":
            return [
                {
                    "event_name": "Trả cổ tức năm 2025 bằng tiền mặt - MBB",
                    "ex_date": "2026-07-16",
                    "record_date": "2026-07-17",
                    "payment_date": "2026-08-05",
                    "description": "Tỷ lệ thực hiện: 10% (1.000 đồng/cổ phiếu). Phát hành cổ phiếu trả cổ tức tỷ lệ 15% thực hiện đồng thời."
                },
                {
                    "event_name": "Đại hội đồng cổ đông thường niên năm 2026 - MBB",
                    "ex_date": "2026-03-20",
                    "record_date": "2026-03-23",
                    "payment_date": "—",
                    "description": "Họp vào ngày 25/04/2026 tại Hà Nội thông qua kế hoạch kinh doanh và phương án tăng vốn điều lệ."
                }
            ]
        elif symbol == "PHC":
            return [
                {
                    "event_name": "Đại hội đồng cổ đông thường niên năm 2026 - PHC",
                    "ex_date": "2026-03-18",
                    "record_date": "2026-03-19",
                    "payment_date": "—",
                    "description": "Họp vào ngày 20/04/2026 thông qua mục tiêu LNST đạt 40 tỷ đồng (tăng trưởng so với 2025)."
                },
                {
                    "event_name": "Trả cổ tức năm 2023 bằng tiền mặt - PHC",
                    "ex_date": "2024-09-12",
                    "record_date": "2024-09-15",
                    "payment_date": "2024-10-10",
                    "description": "Tỷ lệ thực hiện: 5% (500 đồng/cổ phiếu). Giai đoạn 2024-2025 tập trung giữ lại vốn phục vụ thi công."
                }
            ]
        else:
            # Deterministic generator for other tickers
            import hashlib
            h = int(hashlib.md5(symbol.encode('utf-8')).hexdigest(), 16)
            div_rate = 5 + (h % 11)  # 5% to 15%
            div_val = div_rate * 100
            
            ex_date_days = 10 + (h % 20)
            pay_date_days = ex_date_days + 15 + (h % 10)
            
            return [
                {
                    "event_name": f"Trả cổ tức bằng tiền mặt năm 2025 - {symbol}",
                    "ex_date": (now + timedelta(days=ex_date_days)).strftime("%Y-%m-%d"),
                    "record_date": (now + timedelta(days=ex_date_days + 1)).strftime("%Y-%m-%d"),
                    "payment_date": (now + timedelta(days=pay_date_days)).strftime("%Y-%m-%d"),
                    "description": f"Tỷ lệ thực hiện: {div_rate}% ({div_val:,.0f} đồng/cổ phiếu)"
                },
                {
                    "event_name": f"Đại hội đồng cổ đông thường niên năm 2026 - {symbol}",
                    "ex_date": (now - timedelta(days=20 + (h % 30))).strftime("%Y-%m-%d"),
                    "record_date": (now - timedelta(days=19 + (h % 30))).strftime("%Y-%m-%d"),
                    "payment_date": "—",
                    "description": f"Họp ĐHĐCĐ thường niên năm 2026 thông qua kết quả kinh doanh và kế hoạch phân phối lợi nhuận."
                }
            ]

    def _generate_mock_indicators(self, symbol: str) -> dict:
        stats = {
            "FPT": {"pe": 22.4, "pb": 5.2, "eps": 6050, "roa": 12.5, "roe": 25.8, "market_cap": 165000000000000},
            "SSI": {"pe": 15.1, "pb": 1.8, "eps": 2520, "roa": 4.2, "roe": 12.1, "market_cap": 57000000000000},
            "VIC": {"pe": 35.8, "pb": 1.2, "eps": 1150, "roa": 1.5, "roe": 4.5, "market_cap": 158000000000000},
            "VNM": {"pe": 16.5, "pb": 4.1, "eps": 4120, "roa": 15.2, "roe": 28.5, "market_cap": 142000000000000},
            "HPG": {"pe": 12.8, "pb": 1.5, "eps": 2180, "roa": 6.8, "roe": 13.2, "market_cap": 178000000000000},
            "PHC": {"pe": 11.2, "pb": 0.8, "eps": 820, "roa": 1.5, "roe": 6.2, "market_cap": 280000000000}
        }
        return stats.get(symbol.upper(), {"pe": 15.0, "pb": 1.5, "eps": 2000, "roa": 5.0, "roe": 12.0, "market_cap": 10000000000000})
