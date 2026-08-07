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
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime

FRED_BASE = "https://api.stlouisfed.org/fred/release/dates"
FRED_OBS = "https://api.stlouisfed.org/fred/series/observations"

# FRED trả lời trong khoảng 200-400ms khi bình thường. Đặt hạn chờ ngắn để lúc nó chặn
# tốc độ (giới hạn 120 lượt/phút) thì lịch hỏng nhanh và hiện cảnh báo, thay vì treo cả
# chục giây rồi vẫn hỏng - hàm serverless không có ngần ấy thời gian.
FRED_TIMEOUT = 6

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

# --------------------------------------------------------------------------------------
# SỐ LIỆU THỰC TẾ KÈM THEO MỖI BÁO CÁO
#
# Trước đây phần "chi tiết" của mỗi thẻ là số gõ tay trong HTML. Đối chiếu lại với FRED
# thì lệch: thẻ CPI tháng 7 ghi 3.0% YoY và lõi 3.3%, số thật của kỳ tháng 6/2026 là
# 3.46% và 2.57%. Gõ tay số liệu cho tháng mới sẽ lặp lại đúng lỗi đó, nên số liệu ở đây
# luôn kéo trực tiếp từ FRED tại thời điểm hiển thị.
#
# Lưu ý: đây là KỲ GẦN NHẤT ĐÃ CÔNG BỐ, không phải dự báo cho kỳ sắp tới. Với một thẻ
# "sắp diễn ra" thì nó chính là mốc tham chiếu để so sánh khi số mới ra. Không có nguồn
# dự báo (consensus) miễn phí đáng tin nên tuyệt đối không điền số dự báo tự nghĩ.
#
# units theo quy ước FRED: lin = giá trị gốc, pc1 = %ăn theo cùng kỳ năm trước,
# pch = % so với kỳ liền trước, chg = chênh lệch tuyệt đối so với kỳ liền trước.
# --------------------------------------------------------------------------------------
RELEASE_SERIES = {
    50: [  # Employment Situation
        {"id": "PAYEMS", "units": "chg", "freq": "m", "label": "Non-farm Payrolls",
         "suffix": "K", "digits": 0, "signed": True},
        {"id": "UNRATE", "units": "lin", "freq": "m", "label": "Thất nghiệp",
         "suffix": "%", "digits": 1},
        {"id": "CES0500000003", "units": "pc1", "freq": "m", "label": "Thu nhập giờ YoY",
         "suffix": "%", "digits": 1},
    ],
    10: [  # CPI
        {"id": "CPIAUCSL", "units": "pc1", "freq": "m", "label": "CPI YoY",
         "suffix": "%", "digits": 2},
        {"id": "CPILFESL", "units": "pc1", "freq": "m", "label": "CPI lõi YoY",
         "suffix": "%", "digits": 2},
    ],
    46: [  # PPI
        {"id": "PPIFIS", "units": "pc1", "freq": "m", "label": "PPI YoY",
         "suffix": "%", "digits": 2},
        {"id": "PPIFIS", "units": "pch", "freq": "m", "label": "PPI MoM",
         "suffix": "%", "digits": 2, "signed": True},
    ],
    54: [  # Personal Income & Outlays (PCE)
        {"id": "PCEPI", "units": "pc1", "freq": "m", "label": "PCE YoY",
         "suffix": "%", "digits": 2},
        {"id": "PCEPILFE", "units": "pc1", "freq": "m", "label": "PCE lõi YoY",
         "suffix": "%", "digits": 2},
    ],
}

# Bối cảnh chung của thị trường, hiện một dải phía trên lịch. Ba biến này quyết định
# phần lớn tác động từ Mỹ sang Việt Nam: trần lãi suất Fed, lợi suất 10 năm (chi phí vốn
# toàn cầu), và sức mạnh đồng USD (áp lực lên tỷ giá USD/VND và dòng vốn ngoại).
CONTEXT_SERIES = [
    {"id": "DFEDTARU", "units": "lin", "freq": "d", "label": "Trần lãi suất Fed",
     "suffix": "%", "digits": 2},
    {"id": "DGS10", "units": "lin", "freq": "d", "label": "Lợi suất TPCP Mỹ 10 năm",
     "suffix": "%", "digits": 2},
    {"id": "DTWEXBGS", "units": "lin", "freq": "d", "label": "Chỉ số USD (broad)",
     "suffix": "", "digits": 2},
]

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


def load_release_commentary():
    """
    Bình luận mặc định theo LOẠI báo cáo, không gắn với một ngày cụ thể.

    Bình luận viết cho riêng ngày 12/08 thì sang tháng 9 thẻ CPI lại trống trơn - đúng
    kiểu bế tắc của bản HTML cứng cũ. Cơ chế truyền dẫn từ số liệu Mỹ sang thị trường
    Việt Nam thì tháng nào cũng như nhau, nên viết một lần ở đây và dùng cho mọi kỳ.
    Bản ghi theo ngày trong 'events' vẫn đè lên phần này khi cần nói chuyện cụ thể.
    """
    path = _data_file()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception:
        return {}
    raw = payload.get("binh_luan_mac_dinh", {})
    return {k: v for k, v in raw.items() if isinstance(v, dict)}


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
    with urllib.request.urlopen(req, timeout=FRED_TIMEOUT) as r:
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

    def _one(entry):
        """Trả về (release_id, payload, thông báo lỗi). Không ném lỗi ra khỏi thread."""
        release_id, meta = entry
        try:
            return release_id, _fred_request(release_id, start, end, api_key), None
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = json.loads(e.read().decode("utf-8")).get("error_message", "")
            except Exception:
                pass
            return release_id, None, f"{meta['title']}: HTTP {e.code} {body}".strip()
        except Exception as e:
            return release_id, None, f"{meta['title']}: {e}"

    # Gọi song song: bốn lượt nối đuôi nhau đủ chậm để cộng dồn thành vài giây trên
    # một hàm serverless vốn đã phải chờ thêm phần số liệu phía dưới.
    with ThreadPoolExecutor(max_workers=4) as pool:
        fetched = list(pool.map(_one, FRED_RELEASES.items()))

    events = []
    failed = []
    for release_id, payload, error in fetched:
        meta = FRED_RELEASES[release_id]
        if error:
            failed.append(error)
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


def _spec_key(spec):
    return f"{spec['id']}|{spec['units']}"


def _format_period(day, freq):
    """Ngày quan sát của FRED luôn là đầu kỳ. Với chuỗi theo tháng thì hiện 'T6/2026'."""
    try:
        d = datetime.strptime(day, "%Y-%m-%d").date()
    except ValueError:
        return day
    return f"T{d.month}/{d.year}" if freq == "m" else d.strftime("%d/%m/%Y")


def _format_value(raw, spec):
    """Trả về None khi FRED báo thiếu quan sát ('.'), để chỗ đó bỏ trống thay vì hiện 0."""
    if raw in (None, "", "."):
        return None
    try:
        v = float(raw)
    except (TypeError, ValueError):
        return None
    digits = spec.get("digits", 2)
    text = f"{v:+,.{digits}f}" if spec.get("signed") else f"{v:,.{digits}f}"
    return text + spec.get("suffix", "")


def _fetch_observation(spec, api_key, as_of=None):
    """
    Lấy đúng một quan sát mới nhất của một chuỗi. Lỗi thì trả None, không ném ra ngoài.

    as_of ('YYYY-MM-DD') dùng tham số realtime của FRED để hỏi "vào ngày đó thị trường
    nhìn thấy con số nào". Nhờ vậy thẻ đã công bố hiện đúng số của buổi công bố hôm ấy,
    thay vì số của kỳ mới nhất tính tới hôm nay - hai thứ hoàn toàn khác nhau.
    """
    query = {
        "series_id": spec["id"],
        "api_key": api_key,
        "file_type": "json",
        "units": spec["units"],
        "sort_order": "desc",
        "limit": 1,
    }
    if as_of:
        query["realtime_start"] = as_of
        query["realtime_end"] = as_of
    params = urllib.parse.urlencode(query)
    req = urllib.request.Request(f"{FRED_OBS}?{params}",
                                 headers={"User-Agent": "AI-Terminal/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=FRED_TIMEOUT) as r:
            payload = json.loads(r.read().decode("utf-8"))
    except Exception:
        return None

    for item in payload.get("observations", []):
        value = _format_value(item.get("value"), spec)
        if value is None:
            continue
        return {
            "label": spec["label"],
            "value": value,
            "period": _format_period(item.get("date", ""), spec.get("freq", "m")),
            "series_id": spec["id"],
        }
    return None


def fetch_fred_observations():
    """
    Lấy số liệu thực tế mới nhất của mọi chuỗi cần dùng.

    Trả về (dict theo khóa 'series|units', cảnh báo hoặc None). Chuỗi nào hỏng thì thiếu
    chuỗi đó, phần còn lại vẫn hiển thị - lịch không bao giờ chết vì một chuỗi lỗi.
    """
    api_key = _clean_api_key(os.getenv("FRED_API_KEY"))
    if not api_key or not FRED_KEY_RE.match(api_key):
        return {}, None  # fetch_fred_events đã cảnh báo về key rồi, không lặp lại

    with _cache_lock:
        hit = _cache.get("observations")
        if hit and time.time() - hit["at"] < _CACHE_TTL:
            return dict(hit["data"]), hit["warning"]

    specs = [s for group in RELEASE_SERIES.values() for s in group] + CONTEXT_SERIES
    seen, unique = set(), []
    for spec in specs:
        key = _spec_key(spec)
        if key not in seen:
            seen.add(key)
            unique.append(spec)

    # Tuần tự thì khoảng chục lượt gọi nối đuôi nhau, đủ chậm để người dùng thấy giật.
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda s: (_spec_key(s), _fetch_observation(s, api_key)), unique))

    data = {k: v for k, v in results if v}
    missing = [k.split("|")[0] for k, v in results if not v]
    warning = None
    if missing:
        warning = ("Không lấy được số liệu thực tế của: " + ", ".join(sorted(set(missing)))
                   + ". Thẻ tương ứng sẽ để trống phần số liệu.")
    if not missing:
        with _cache_lock:
            _cache["observations"] = {"at": time.time(), "data": dict(data), "warning": warning}
    return data, warning


def fetch_release_vintages(pairs):
    """
    Số liệu đúng như thị trường nhìn thấy tại ngày công bố, cho nhiều thẻ cùng lúc.

    pairs: danh sách (release_id, 'YYYY-MM-DD'). Trả về dict theo cặp đó.

    Gom hết vào một đợt song song thay vì gọi lần lượt từng thẻ: một tháng nhiều thẻ đã
    qua thì kiểu gọi nối đuôi mất vài giây, quá lâu cho một hàm serverless.
    Thẻ nào hỏng thì mất phần số liệu của riêng nó, không bao giờ mượn số của kỳ khác.
    """
    api_key = _clean_api_key(os.getenv("FRED_API_KEY"))
    if not api_key or not FRED_KEY_RE.match(api_key):
        return {}

    out, jobs = {}, []
    for release_id, as_of in set(pairs):
        cache_key = f"vintage|{release_id}|{as_of}"
        with _cache_lock:
            hit = _cache.get(cache_key)
        if hit and time.time() - hit["at"] < _CACHE_TTL:
            out[(release_id, as_of)] = list(hit["data"])
            continue
        for spec in RELEASE_SERIES.get(release_id, []):
            jobs.append((release_id, as_of, spec))

    if jobs:
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(
                lambda j: (j[0], j[1], _fetch_observation(j[2], api_key, j[1])), jobs))
        wanted = {}
        for release_id, as_of, _ in jobs:
            wanted[(release_id, as_of)] = wanted.get((release_id, as_of), 0) + 1
        for key in wanted:
            out.setdefault(key, [])
        for release_id, as_of, found in results:
            if found:
                out[(release_id, as_of)].append(found)

        # Giữ đúng thứ tự khai báo trong RELEASE_SERIES, thread pool trả về không theo thứ tự
        for key in wanted:
            order = [s["label"] for s in RELEASE_SERIES.get(key[0], [])]
            out[key].sort(key=lambda m: order.index(m["label"]) if m["label"] in order else 99)

        # Chỉ cache khi lấy đủ mọi chuỗi của thẻ đó. Bản dữ liệu quá khứ thì không đổi nữa,
        # nhưng một lần FRED timeout mà vẫn ghim vào cache thì thẻ mất số liệu suốt 6 tiếng
        # dù mạng đã tốt trở lại - lỗi tạm thời hóa thành lỗi dai dẳng.
        with _cache_lock:
            for key, count in wanted.items():
                if len(out[key]) == count:
                    _cache[f"vintage|{key[0]}|{key[1]}"] = {
                        "at": time.time(), "data": list(out[key])}
    return out


def _release_id_for(event):
    """Dò ngược từ tiêu đề về release ID để biết thẻ này gắn với bộ chuỗi số liệu nào."""
    if event.get("category") != "us_data":
        return None
    title = event.get("title", "")
    for release_id, meta in FRED_RELEASES.items():
        if meta["title"] in title or title in meta["title"]:
            return release_id
    return None


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

    observations, obs_warn = fetch_fred_observations()
    if obs_warn:
        warnings.append(obs_warn)

    commentary = load_release_commentary()

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
        ev["_release_id"] = _release_id_for(ev)

    vintages = fetch_release_vintages([(ev["_release_id"], ev["date"]) for ev in events
                                       if ev["_release_id"] and ev["status"] == "past"])

    for ev in events:
        release_id = ev.pop("_release_id")
        specs = RELEASE_SERIES.get(release_id, [])

        # Chỉ lấp vào chỗ đang trống: bình luận viết riêng cho ngày đó luôn được ưu tiên
        fallback = commentary.get(ev["title"], {})
        for field in ("detail", "vn_impact", "recommendation"):
            if not ev.get(field) and fallback.get(field):
                ev[field] = fallback[field]

        # Thẻ đã qua: số của chính buổi công bố hôm đó. Thẻ hôm nay/sắp tới: kỳ gần nhất
        # đã công bố, làm mốc so sánh khi số mới ra. 'latest_kind' để giao diện ghi rõ
        # đang xem loại nào, tránh đọc nhầm số kỳ trước thành số kỳ này.
        if release_id and ev["status"] == "past":
            ev["latest"] = vintages.get((release_id, ev["date"]), [])
            ev["latest_kind"] = "released"
        else:
            ev["latest"] = [observations[_spec_key(s)] for s in specs
                            if _spec_key(s) in observations]
            ev["latest_kind"] = "reference"

    return {
        "month": f"{anchor.month}/{anchor.year}",
        "month_key": anchor.strftime("%Y-%m"),
        "today": today_s,
        "is_current_month": (anchor.year, anchor.month) == (today.year, today.month),
        "events": events,
        "market_context": [observations[_spec_key(s)] for s in CONTEXT_SERIES
                           if _spec_key(s) in observations],
        "counts": {
            "total": len(events),
            "from_fred": sum(1 for e in events if e["source"].startswith("fred")),
            "manual": sum(1 for e in events if e["source"] == "manual"),
        },
        "warnings": warnings,
    }
