# StockAI — AI Terminal phân tích chứng khoán Việt Nam

Dashboard FastAPI + HTML tĩnh, deploy trên Vercel.
Repo: `github.com/nhuphiphc-ops/StockAI` · Live: `stock-ai-six-iota.vercel.app`

## Chạy dự án

```bash
uvicorn main:app --reload
```

`launch_dashboard.bat` cũng khởi chạy được. Không có test suite.

## Kiến trúc — 3 điểm dễ vấp

**1. `templates/index.html` được phục vụ dạng TĨNH, không qua Jinja.**
`vercel.json` route `/(.*)` trỏ thẳng vào file. Trong template không có một cú pháp
`{{ }}` nào và cũng không được thêm — sẽ hiện nguyên văn ra trình duyệt. Mọi thứ
động phải render bằng JavaScript phía client, gọi vào `/api/...`.

**2. Toàn bộ JS nằm trong 3 thẻ `<script>` inline, thẻ giữa nặng ~152 KB.**
Một lỗi cú pháp ở bất kỳ đâu trong thẻ đó sẽ giết cả dashboard: không giá live,
không biểu đồ, không phái sinh. Đã từng xảy ra — một đoạn đuôi thừa trùng lặp của
`loadBuildersTab` để lại `} catch (e) {` mồ côi, và không ai phát hiện vì Vercel
đang chạy bản commit cũ còn nguyên vẹn.

**Trước khi deploy bất kỳ thay đổi nào vào `index.html`, kiểm tra cú pháp:**

```bash
python - <<'PY'
import io, re, subprocess, tempfile, os
src = io.open("templates/index.html", encoding="utf-8").read()
for i, s in enumerate(re.findall(r"<script(?![^>]*\ssrc=)[^>]*>(.*?)</script>", src, re.S)):
    p = os.path.join(tempfile.mkdtemp(), "s.js"); io.open(p, "w", encoding="utf-8").write(s)
    r = subprocess.run(["node", "--check", p], capture_output=True, text=True)
    print(f"script #{i} ({len(s)} chars):", "OK" if r.returncode == 0 else r.stderr.strip()[:200])
PY
```

**3. File dữ liệu đọc lúc chạy phải khai báo trong `vercel.json`.**
Build Python chỉ đóng gói những gì được liệt kê ở `config.includeFiles`. Hiện có
`data/**`. Thêm file dữ liệu mới thì phải bổ sung vào đây, nếu không nó tồn tại ở
local nhưng biến mất trên Vercel.

## Lịch sự kiện vĩ mô

Trước đây là HTML viết cứng, tên tháng gõ thẳng vào tiêu đề nên không bao giờ
sang tháng mới. Nay:

- `core/macro_calendar.py` — ghép 2 nguồn, tính trạng thái từ ngày thật.
- `GET /api/macro-events?month=YYYY-MM` — bỏ trống là tháng hiện tại.
- **FRED** (Fed St. Louis) tự cấp ngày công bố. Release ID: CPI `10`, PPI `46`,
  Employment Situation `50`, Personal Income & Outlays (PCE) `54`.
- `data/macro_events.json` — phần người dùng biên tập: địa chính trị, giá hàng
  hóa, họp FOMC, và **bình luận tác động tới Việt Nam**. FRED chỉ cho biết ngày
  nào công bố cái gì, không hề có phân tích. Bản ghi trùng `date` + `category`
  sẽ gộp đè lên thẻ FRED.

Cần `FRED_API_KEY` (32 ký tự chữ thường + số, miễn phí tại
`fredaccount.stlouisfed.org/apikey`). Thiếu key thì lịch vẫn hiện đúng tháng hiện
tại kèm cảnh báo — **không bao giờ âm thầm hiển thị tháng cũ**, vì chính kiểu im
lặng đó khiến lỗi ban đầu tồn tại rất lâu mà không ai biết.

Đặt biến trên Vercel bằng Git Bash, đừng dùng PowerShell:

```bash
printf '%s' 'KEY' | vercel env add FRED_API_KEY production
```

PowerShell chèn ký tự thừa vào giá trị và FRED sẽ từ chối. Code có gột `\r`, `\n`,
BOM, dấu nháy rồi, nhưng nạp sạch ngay từ đầu vẫn hơn.

## Việc còn dang dở

- Các thẻ lấy từ FRED chưa có phân tích tác động tới VN — chỉ có mô tả chung về
  loại báo cáo. Bổ sung qua `data/macro_events.json`.
- FOMC không có trong FRED, phải nhập tay.
- `data.db` và `__pycache__/*.pyc` **đang bị git theo dõi**. `.gitignore` không gỡ
  được, cần `git rm --cached`.
- `ssi_client.py` ở thư mục gốc và `core/ssi_client.py` là hai bản khác nhau;
  `excel_manager.py` cũng vậy. Chưa rõ bản nào đang thực sự được dùng.

## Quy tắc

- **Không bịa số liệu tài chính.** Đây là dashboard đầu tư, con số bịa ra có thể
  dẫn tới quyết định tiền thật. Thiếu dữ liệu thì để trống kèm cảnh báo rõ ràng.
- `.env` chứa khóa Supabase và FRED, đã được `.gitignore` chặn. Không bao giờ
  commit. Mẫu ở `.env.example`.
- Repo công khai.
