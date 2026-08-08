# StockAI — AI Terminal phân tích chứng khoán Việt Nam

Dashboard FastAPI + HTML tĩnh, deploy trên Vercel.
Repo: `github.com/nhuphiphc-ops/StockAI` · Live: `stock-ai-six-iota.vercel.app`

## Chạy dự án

```bash
uvicorn main:app --reload
```

`launch_dashboard.bat` cũng khởi chạy được. Không có test suite.

## Kiến trúc — 5 điểm dễ vấp

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

**4. Hàm serverless trên Vercel chạy theo UTC, không phải giờ Việt Nam.**
`datetime.now()` ở đó trả về giờ sớm hơn Việt Nam 7 tiếng. Dùng
`vn_now()` trong `main.py` (ghim `timezone(timedelta(hours=7))`) cho **mọi** logic
phụ thuộc giờ: xét phiên giao dịch, đóng dấu thời gian bản ghi, cắt theo ngày.

Đã trả giá cho chuyện này: chốt chặn phiên phái sinh viết bằng `datetime.now()` khi
lên production sẽ coi **15:45–21:45 giờ Việt Nam là trong phiên** và chặn đúng
8:45–14:45 — đảo ngược hoàn toàn. Máy cá nhân đặt múi giờ VN nên chạy `uvicorn` ở
nhà thấy đúng hết; bản deploy cũng qua được lượt kiểm tra đầu vì hôm đó là thứ Bảy,
chốt chặn cuối tuần chạy trước nên che mất lỗi giờ.

**Không có gì trong giao diện phơi ra "máy chủ đang nghĩ mấy giờ"**, nên cả lớp lỗi
này im lặng. Nghi ngờ lệch giờ thì đối chiếu:

```bash
curl -s https://stock-ai-six-iota.vercel.app/api/macro-events | python -c "import sys,json;print(json.load(sys.stdin)['today'])"
```

**5. `/static/...` trên Vercel KHÔNG chạy qua Python.**
`vercel.json` route `/static/(.*)` thẳng vào build `@vercel/static`, nên mọi route
FastAPI khai cùng đường dẫn đó chỉ có tác dụng ở local. Từng có một route riêng phục
vụ `/static/lightweight-charts.js` đọc từ `templates/`, khiến hai môi trường nạp hai
file khác nhau: local ra bản v5.2.0, production 404. Biểu đồ nến vì thế chưa bao giờ
chạy trên site thật.

File tĩnh phải nằm **thật** trong `static/`. Đừng thêm route FastAPI cho đường dẫn
`/static/`; handler chung `get_static_file()` đã đọc đúng thư mục Vercel phục vụ.

## Biểu đồ nến

`static/lightweight-charts.js` là TradingView Lightweight Charts **4.2.3**, vendor
sẵn trong repo. Phải giữ nhánh **v4**: code trong `initChart()` gọi
`addCandlestickSeries()` và `param.seriesData.get()`, **cả hai đã bị gỡ ở v5**. Nâng
lên v5 mà không sửa code thì các guard `typeof … === 'function'` sẽ lặng lẽ bỏ qua —
biểu đồ vẽ trục nhưng không có nến, và console không báo gì cả.

Biểu đồ nằm ở tab **Bảng Giá Live** (`<div id="tvChart">`), không phải tab Phái Sinh.

## Phái sinh M5

- `derivatives_session_state()` — phiên VN30F1M trên HNX: T2–T6, ATO 8:45, khớp liên
  tục 9:00–11:30, nghỉ trưa, 13:00–14:30, ATC tới 14:45. Ngoài phiên thì
  `/api/derivatives/intraday-forecast` trả `NGOÀI PHIÊN GIAO DỊCH` và **không ghi
  nhật ký**. Trước khi có hàm này, chỉ cần mở trang là cứ 15 giây log dài thêm một
  dòng — kể cả thứ Bảy, Chủ nhật, 7 giờ tối.
- **Chỉ chặn được cuối tuần, không chặn ngày lễ** — dự án không có lịch nghỉ HNX.
- Nhật ký nằm ở `localStorage` của trình duyệt, không phải trên server. Route
  `/api/derivatives/history-log` đọc `static/derivatives_history.json`, mà filesystem
  trên Vercel chỉ đọc nên đường đó thực tế luôn rỗng.
- Từ khóa nhận hướng trong `price_action` phải đủ dài để không nuốt nghĩa nhau. Bản
  cũ để `"long"`, `"short"` trần, mà chính câu mô tả trung lập tự sinh là *"hai phe
  Long/Short đang giằng co"* — khớp cả hai phía rồi rơi vào nhánh Short. `"tăng"`
  cũng khớp trong *"từ chối tăng"*.
- Con số ở hàng ROI **không phải lãi/lỗ đã thực hiện**: nó cộng khoảng cách
  Entry→TP1 của mọi tín hiệu, tức giả định lệnh nào cũng chạm TP1 và không lệnh nào
  chạm SL. Hệ thống chưa đối chiếu giá sau tín hiệu nên chưa biết kết quả thật.

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
- `binh_luan_mac_dinh` trong cùng file đó áp cho **mọi kỳ** của một loại báo cáo,
  không gắn với ngày. Nhờ vậy tháng 9, 10, 11… tự có phân tích. Viết bình luận
  cho riêng một ngày thì sang tháng sau thẻ lại trống — đúng kiểu bế tắc cũ.

**Số liệu trong thẻ không được gõ tay.** `RELEASE_SERIES` khai chuỗi FRED cho từng
báo cáo, số kéo về lúc hiển thị:

- Thẻ **sắp diễn ra / hôm nay** → kỳ gần nhất đã công bố, làm mốc so sánh.
- Thẻ **đã công bố** → tham số `realtime_start/end` của FRED cho đúng con số thị
  trường nhìn thấy hôm đó, không phải số kỳ mới nhất tính tới hôm nay.
- `market_context` (trần lãi suất Fed, lợi suất 10 năm, chỉ số USD) hiện thành
  dải phía trên lịch.

Lý do phải làm vậy: đám số gõ tay của tháng 7 đã sai so với FRED — thẻ CPI ghi
3.0% YoY và lõi 3.3%, số thật kỳ T6/2026 là 3.46% và 2.57%; thất nghiệp ghi 4.1%,
`UNRATE` là 4.2%. Không ai đối chiếu vì nó chỉ là chữ trong HTML.

Mọi lượt gọi FRED đều chạy song song và cache 6 tiếng. Bỏ song song thì một tháng
nhiều thẻ đã qua mất ~6,5s, quá lâu cho hàm serverless.

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

- FOMC không có trong FRED, phải nhập tay.
- Bốn loại báo cáo FRED đã có bình luận tác động VN qua `binh_luan_mac_dinh`, nhưng
  trường `recommendation` để trống — phần khuyến nghị đầu tư cụ thể do người dùng viết.
- Chưa theo dõi kết quả thật của tín hiệu phái sinh (so giá sau tín hiệu với SL/TP)
  nên hàng ROI vẫn là kịch bản giả định, chưa phải lãi/lỗ thật.
- Ngày lễ chưa được lọc khỏi phiên giao dịch, chỉ mới lọc cuối tuần.
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
