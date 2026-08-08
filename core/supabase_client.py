"""
Lưu nhật ký tín hiệu phái sinh M5 lên Supabase (PostgREST), thay cho localStorage.

Trước đây nhật ký chỉ nằm ở localStorage của trình duyệt: đổi máy hoặc xóa dữ liệu
trình duyệt là mất sạch, và không tích lũy được qua nhiều ngày để đối chiếu dài hạn.
Route /api/derivatives/history-log từng đọc static/derivatives_history.json, nhưng
filesystem trên Vercel chỉ đọc nên đường đó thực tế luôn rỗng trên production.

Dùng thẳng REST API của Supabase (PostgREST) qua `requests`, không dùng SDK `supabase`
chính thức - SDK kéo theo httpx/postgrest-py/gotrue/realtime, nặng không cần thiết cho
một hàm serverless chỉ cần hai thao tác insert/select đơn giản. Toàn bộ client khác
trong dự án (SSI, FRED, vnstock) đều gọi REST trực tiếp theo đúng cách này.

Dùng SUPABASE_KEY dạng service_role, không phải anon: mọi lượt ghi/đọc đều đi qua
backend FastAPI của chính dự án (chốt chặn phiên, kiểm tra hành động Long/Short đã
nằm ở main.py), trình duyệt không bao giờ gọi thẳng vào Supabase. service_role bỏ qua
RLS nên không cần bật policy công khai cho bảng - khóa đó tuyệt đối không được lộ ra
phía client.

Bảng cần tạo trước trong Supabase (SQL Editor):

    create table if not exists derivatives_signals (
        id bigint generated always as identity primary key,
        trade_date date not null,
        trade_time time not null,
        trend text not null,
        action text not null,
        entry text not null,
        sl text not null,
        tp text not null,
        created_at timestamptz not null default now()
    );
    create index if not exists idx_derivatives_signals_date on derivatives_signals(trade_date);
"""
import os
import requests

TABLE = "derivatives_signals"


def _config():
    url = (os.getenv("SUPABASE_URL") or "").strip().rstrip("/")
    key = (os.getenv("SUPABASE_KEY") or "").strip()
    return url, key


def _headers(key):
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def is_configured():
    url, key = _config()
    return bool(url and key)


def insert_signal(trade_date, trade_time, trend, action, entry, sl, tp):
    """
    Ghi một tín hiệu Long/Short thật vào Supabase. Không bao giờ ném lỗi ra ngoài -
    persistence hỏng không được phép làm hỏng luôn cả kết quả phân tích đang trả về
    cho người dùng. Trả True/False để nơi gọi biết mà log, không hơn.
    """
    url, key = _config()
    if not url or not key:
        print("Chưa cấu hình SUPABASE_URL/SUPABASE_KEY, bỏ qua ghi nhật ký tín hiệu.")
        return False
    try:
        r = requests.post(
            f"{url}/rest/v1/{TABLE}",
            headers=_headers(key),
            json={
                "trade_date": trade_date,
                "trade_time": trade_time,
                "trend": trend,
                "action": action,
                "entry": entry,
                "sl": sl,
                "tp": tp,
            },
            timeout=8,
        )
        if r.status_code not in (200, 201):
            print(f"Ghi nhật ký Supabase thất bại: HTTP {r.status_code} {r.text[:200]}")
            return False
        return True
    except Exception as e:
        print(f"Ghi nhật ký Supabase lỗi: {e}")
        return False


def get_signals(trade_date):
    """
    Lấy toàn bộ tín hiệu của một ngày, sắp theo giờ. Trả về (danh sách, cảnh báo).

    Không bao giờ ném lỗi: Supabase hỏng thì trả [] kèm cảnh báo rõ ràng, để giao diện
    hiện cảnh báo thay vì âm thầm coi như "chưa có lệnh nào" - hai tình huống đó khác
    nhau và người dùng cần phân biệt được.
    """
    url, key = _config()
    if not url or not key:
        return [], ("Chưa cấu hình SUPABASE_URL/SUPABASE_KEY nên không đọc được nhật ký "
                    "tín hiệu đã lưu.")
    try:
        r = requests.get(
            f"{url}/rest/v1/{TABLE}",
            headers=_headers(key),
            params={
                "trade_date": f"eq.{trade_date}",
                "order": "trade_time.asc",
                "select": "trade_date,trade_time,trend,action,entry,sl,tp",
            },
            timeout=8,
        )
        if r.status_code != 200:
            return [], f"Không đọc được nhật ký tín hiệu: HTTP {r.status_code}."
        rows = r.json()
        return [
            {
                "date": row["trade_date"],
                "time": str(row["trade_time"])[:8],
                "trend": row.get("trend", ""),
                "action": row["action"],
                "entry": row["entry"],
                "sl": row["sl"],
                "tp": row["tp"],
            }
            for row in rows
        ], None
    except Exception as e:
        return [], f"Không đọc được nhật ký tín hiệu: {e}"
