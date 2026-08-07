"""
Lịch sự kiện vĩ mô ảnh hưởng tới thị trường Việt Nam.

Trước đây khối lịch này là HTML viết cứng trong templates/index.html: ngày tháng gõ tay,
tiêu đề ghi thẳng "(THÁNG 7/2026)", nhãn "ĐANG DIỄN RA" cũng là chữ cứng. Không có mã nào
chuyển sang tháng mới, nên sang tháng 8 nó vẫn hiển thị nguyên tháng 7.

Module này thay bằng hai nguồn ghép lại:

  1. FRED (Fed St. Louis) - tự động lấy NGÀY CÔNG BỐ của các báo cáo vĩ mô Mỹ.
     Miễn phí, là nguồn gốc, cần một API key đăng ký miễn phí tại
     https://fredaccount.stlouisfed.org/apikey rồi đặt vào biến môi trường FRED_API_KEY.

  2. data/macro_events.json - phần người dùng tự biên tập: sự kiện địa chính trị, giá
     hàng hóa, họp FOMC, và quan trọng nhất là bình luận tác động tới Việt Nam.
     FRED chỉ cho biết "ngày nào công bố cái gì", không hề có phân tích tác động.

Nguyên tắc an toàn: không bao giờ im lặng hiển thị dữ liệu tháng cũ. Nếu FRED lỗi hoặc
thiếu key, API vẫn trả về đúng tháng đang xem kèm cảnh báo rõ ràng để giao diện hiện lên.
"""
import json
import os
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from calendar import monthrange
from datetime import date, datetime

FRED_BASE = "https://api.stlouisfed.org/fred/release/dates"

# FRED chỉ chấp nhận key đúng 32 ký tự chữ thường + số
FRED_KEY_RE = re.compile(r"^[a-z0-9]{32}$")


def _clean_api_key(raw):
    """
    Gột sạch giá trị biến môi trường trước khi dùng.

    Biến môi trường rất hay bị dính rác tùy cách thiết lập: xuống dòng CR/LF, BOM
    (\\ufeff), dấu nháy bao quanh, khoảng trắng. str.strip() không xóa BOM nên phải
    xử lý riêng, nếu không key trông đúng mà FRED vẫn từ chối.
    """
    if not raw:
        return ""
    return raw.strip().strip("﻿\r\n\t '\"").strip()

# Release ID tra trực tiếp từ danh mục releases của FRED, không phải phỏng đoán.
FRED_RELEASES = {
    50: {"title": "Báo cáo Việc làm Mỹ", "category": "us_data",
         "summary": "Employment Situation - Non-farm Payrolls và tỷ lệ thất nghiệp, "
                    "thước đo sức khỏe thị trường lao động Mỹ."},
    10: {"title": "Chỉ số Lạm phát CPI Mỹ", "category": "us_data",
         "summary": "Consumer Price Index - lạm phát tiêu dùng, tác động trực tiếp tới "
                    "kỳ vọng lãi suất Fed và áp lực tỷ giá USD/VND."},
    46: {"title": "Chỉ số Giá sản xuất PPI Mỹ", "category": "us_data",
         "summary": "Producer Price Index - lạm phát từ phía sản xuất, chỉ báo sớm của CPI."},
    54: {"title": "Chỉ số Lạm phát PCE Mỹ", "category": "us_data",
         "summary": "Personal Income and Outlays - thước đo lạm phát ưa thích của Fed."},
}

VALID_CATEGORIES = {"us_data", "fomc", "geopolitics", "commodity", "vn_data"}

_CACHE_TTL = 6 * 60 * 60  # 6 tiếng: lịch công bố hiếm khi đổi trong ngày
_cache = {}
_cache_lock = threading.Lock()


def _data_file():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, "data", "macro_events.json")


def load_manual_events():
    """Đọc kho sự kiện người dùng tự biên tập. Trả về (danh sách, lỗi nếu có)."""
    path = _data_file()
    if not os.path.exists(path):
        return [], f"Không tìm thấy {os.path.relpath(path)}."
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception as e:
        return [], f"Không đọc được macro_events.json: {e}"

    events = []
    for raw in payload.get("events", []):
        if not raw.get("date") or not raw.get("title"):
            continue  # bỏ qua bản ghi thiếu trường bắt buộc thay vì làm hỏng cả lịch
        try:
            datetime.strptime(raw["date"], "%Y-%m-%d")
        except ValueError:
            continue
        category = raw.get("category", "us_data")
        events.append({
            "date": raw["date"],
            "title": raw["title"],
            "category": category if category in VALID_CATEGORIES else "us_data",
            "summary": raw.get("summary", ""),
            "detail": raw.get("detail", ""),
            "vn_impact": raw.get("vn_impact", ""),
            "recommendation": raw.get("recommendation", ""),
            "source": "manual",
        })
    return events, None


def _fred_request(release_id, start, end, api_key):
    params = urllib.parse.urlencode({
        "release_id": release_id,
        "api_key": api_key,
        "file_type": "json",
        "realtime_start": start,
        "realtime_end": end,
        "include_release_dates_with_no_data": "true",
        "sort_order": "asc",
    })
    req = urllib.request.Request(f"{FRED_BASE}?{params}",
                                 headers={"User-Agent": "AI-Terminal/1.0"})
    with urllib.request.urlopen(req, timeout=12) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_fred_events(start, end):
    """
    Lấy ngày công bố các báo cáo vĩ mô Mỹ trong khoảng [start, end] (chuỗi YYYY-MM-DD).
    Trả về (danh sách sự kiện, cảnh báo hoặc None). Không bao giờ ném lỗi ra ngoài.
    """
    api_key = _clean_api_key(os.getenv("FRED_API_KEY"))
    if not api_key:
        return [], ("Chưa cấu hình FRED_API_KEY nên không tự lấy được lịch công bố "
                    "CPI/PPI/PCE/Việc làm Mỹ. Đăng ký key miễn phí tại "
                    "fredaccount.stlouisfed.org/apikey.")
    if not FRED_KEY_RE.match(api_key):
        # Bắt lỗi ngay thay vì để FRED trả về 4 lần HTTP 400 giống hệt nhau.
        # Thường gặp khi biến môi trường bị dính ký tự xuống dòng, dấu nháy hoặc BOM
        # do cách nạp giá trị (ví dụ pipe qua PowerShell trên Windows).
        return [], (f"FRED_API_KEY không đúng định dạng: cần đúng 32 ký tự chữ thường và số, "
                    f"đang nhận {len(api_key)} ký tự. Kiểm tra lại giá trị biến môi trường "
                    f"(có thể bị dính ký tự thừa khi thiết lập).")

    cache_key = (start, end)
    with _cache_lock:
        hit = _cache.get(cache_key)
        if hit and time.time() - hit["at"] < _CACHE_TTL:
            return list(hit["events"]), hit["warning"]

    events = []
    failed = []
    for release_id, meta in FRED_RELEASES.items():
        try:
            payload = _fred_request(release_id, start, end, api_key)
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = json.loads(e.read().decode("utf-8")).get("error_message", "")
            except Exception:
                pass
            failed.append(f"{meta['title']}: HTTP {e.code} {body}".strip())
            continue
        except Exception as e:
            failed.append(f"{meta['title']}: {e}")
            continue

        for item in payload.get("release_dates", []):
            d = item.get("date")
            if not d or d < start or d > end:
                continue
            events.append({
                "date": d,
                "title": meta["title"],
                "category": meta["category"],
                "summary": meta["summary"],
                "detail": "",
                "vn_impact": "",
                "recommendation": "",
                "source": "fred",
            })

    warning = None
    if failed:
        warning = "Một số lịch không lấy được từ FRED: " + "; ".join(failed)
    # Chỉ cache khi mọi release đều thành công, tránh ghim lại một lần lỗi tạm thời
    if not failed:
        with _cache_lock:
            _cache[cache_key] = {"at": time.time(), "events": list(events), "warning": warning}
    return events, warning


def _merge(manual, auto):
    """
    Gộp hai nguồn. Bản ghi thủ công trùng (ngày, nhóm) sẽ đè lên bản FRED, vì nó mang
    thêm phần bình luận tác động tới Việt Nam mà FRED không có.
    """
    by_key = {}
    for ev in auto:
        by_key[(ev["date"], ev["category"], ev["title"])] = ev

    for ev in manual:
        exact = (ev["date"], ev["category"], ev["title"])
        if exact in by_key:
            by_key[exact] = {**by_key[exact], **{k: v for k, v in ev.items() if v},
                             "source": "fred+manual"}
            continue
        # Cùng ngày, cùng nhóm dữ liệu Mỹ nhưng tiêu đề lệch nhau -> vẫn coi là một
        same_slot = next(
            (k for k in by_key
             if k[0] == ev["date"] and k[1] == ev["category"] == "us_data"
             and (k[2] in ev["title"] or ev["title"] in k[2])),
            None
        )
        if same_slot:
            by_key[same_slot] = {**by_key[same_slot], **{k: v for k, v in ev.items() if v},
                                 "source": "fred+manual"}
        else:
            by_key[exact] = ev

    return sorted(by_key.values(), key=lambda e: (e["date"], e["title"]))


def get_macro_events(month=None, today=None):
    """
    Trả về lịch sự kiện của một tháng.

    month : 'YYYY-MM'. Bỏ trống thì lấy tháng hiện tại - đây chính là chỗ trước kia
            bị viết cứng thành tháng 7/2026.
    today : ghi đè ngày hôm nay, phục vụ kiểm thử.
    """
    today = today or date.today()
    if month:
        try:
            anchor = datetime.strptime(month, "%Y-%m").date()
        except ValueError:
            raise ValueError("Tham số month phải có dạng YYYY-MM.")
    else:
        anchor = today.replace(day=1)

    start = anchor.replace(day=1)
    end = anchor.replace(day=monthrange(anchor.year, anchor.month)[1])
    start_s, end_s = start.isoformat(), end.isoformat()

    warnings = []
    manual, manual_err = load_manual_events()
    if manual_err:
        warnings.append(manual_err)
    manual_in_month = [e for e in manual if start_s <= e["date"] <= end_s]

    auto, auto_warn = fetch_fred_events(start_s, end_s)
    if auto_warn:
        warnings.append(auto_warn)

    events = _merge(manual_in_month, auto)

    # Trạng thái tính theo ngày thật, không còn nhãn "ĐANG DIỄN RA" viết cứng
    today_s = today.isoformat()
    for ev in events:
        if ev["date"] < today_s:
            ev["status"] = "past"
        elif ev["date"] == today_s:
            ev["status"] = "today"
        else:
            ev["status"] = "upcoming"
        ev["date_display"] = datetime.strptime(ev["date"], "%Y-%m-%d").strftime("%d/%m/%Y")

    return {
        "month": f"{anchor.month}/{anchor.year}",
        "month_key": anchor.strftime("%Y-%m"),
        "today": today_s,
        "is_current_month": (anchor.year, anchor.month) == (today.year, today.month),
        "events": events,
        "counts": {
            "total": len(events),
            "from_fred": sum(1 for e in events if e["source"].startswith("fred")),
            "manual": sum(1 for e in events if e["source"] == "manual"),
        },
        "warnings": warnings,
    }
