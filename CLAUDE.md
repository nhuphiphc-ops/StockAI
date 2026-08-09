# StockAI — AI Terminal phân tích chứng khoán Việt Nam

Dashboard FastAPI + HTML tĩnh, deploy trên Vercel.
Repo: `github.com/nhuphiphc-ops/StockAI` · Live: `stock-ai-six-iota.vercel.app`

## Chạy dự án

```bash
uvicorn main:app --reload
```

`launch_dashboard.bat` cũng khởi chạy được. Không có test suite.

## Kiến trúc — 6 điểm dễ vấp

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

**6. `vnstock` ghi vào `Path.home()`, mà home trên Vercel chỉ đọc.**
Gói `vnai` mà `vnstock` phụ thuộc (đo lường sử dụng/license) ghi cache vào
`Path.home()/".vnstock"`. Trên Vercel, `Path.home()` trỏ vào `/home/sbx_user...` —
chỉ `/tmp` ghi được. Ghi thất bại làm hỏng **luôn cả lệnh gọi đang chạy**, không
riêng phần ghi: `get_historical_data()` bắt exception rồi in ra "Vnstock Rate
Limit", nhưng lỗi thật nằm ở `[Errno 30] Read-only file system`, không liên quan
gì đến giới hạn tốc độ — dòng log đó đánh lừa người đọc đi sai hướng.

`main.py` đã tự dò việc này ở đầu file, trước khi bất cứ chỗ nào import
`vnstock`: nếu `~` không ghi được thì ghim cả `HOME` lẫn `USERPROFILE` sang
`tempfile.gettempdir()`. Cần cả hai biến vì `os.path.expanduser` trên POSIX
(Vercel) chỉ nhìn `HOME`, còn trên Windows lại ưu tiên `USERPROFILE` và bỏ qua
`HOME` — thiếu một trong hai thì bản sửa vô tác dụng trên đúng nền tảng đó. Đặt
sau dòng `import core.vnstock_client` là vô ích, vì `vnai` đã cache đường dẫn cũ
ngay lúc import.

## Biểu đồ nến

`static/lightweight-charts.js` là TradingView Lightweight Charts **4.2.3**, vendor
sẵn trong repo. Phải giữ nhánh **v4**: code trong `initChart()` gọi
`addCandlestickSeries()` và `param.seriesData.get()`, **cả hai đã bị gỡ ở v5**. Nâng
lên v5 mà không sửa code thì các guard `typeof … === 'function'` sẽ lặng lẽ bỏ qua —
biểu đồ vẽ trục nhưng không có nến, và console không báo gì cả.

Biểu đồ nằm ở tab **Bảng Giá Live** (`<div id="tvChart">`), không phải tab Phái Sinh.

Từ commit đầu tiên của repo, `.chart-box` mang `display: none !important` **vô điều
kiện** — không route JS hay rule CSS nào từng bật lại nó. `initChart()` vẫn chạy,
canvas vẫn được tạo, `candleSeries` vẫn có dữ liệu thật, nên mọi phép kiểm tra chỉ
nhìn vào state JS (như `candleSeries.data().length`) sẽ báo "OK" nhầm — phải nhìn
`getComputedStyle(...).display` hoặc chụp ảnh thật mới lộ ra. Nay đã đổi thành
`display: flex` và thêm `autoSize: true` vào `createChart()` để thư viện tự đặt
`ResizeObserver` theo dõi container (đổi tab, resize cửa sổ, xoay máy đều tự đo lại) —
`.chart-box` từng luôn 0×0 nên container không có kích thước thật để thư viện đo lúc
khởi tạo.

`.live-board-layout` (khung 3 cột của tab Bảng Giá Live: `290px 1fr 320px`) cũng
không có media query nào che cho tới giờ. Hai cột biên cố định đã 610px, nên dưới
ngưỡng đó cột giữa (`1fr`) — chứa băng giá, biểu đồ, sổ lệnh — co về 0px và biến mất,
không tràn ra ngoài để còn dễ nhận ra. Media query dưới 900px xếp dọc ba khối, kèm
đổi `height: 100%` sang `auto` cho `.sidebar-panel`/`.center-layout` vì các khối đó
dựa vào chiều cao dòng lưới cố định trên desktop.

## Phái sinh M5

- `derivatives_session_state()` — phiên VN30F1M trên HNX: T2–T6, ATO 8:45, khớp liên
  tục 9:00–11:30, nghỉ trưa, 13:00–14:30, ATC tới 14:45. Ngoài phiên thì
  `/api/derivatives/intraday-forecast` trả `NGOÀI PHIÊN GIAO DỊCH` và **không ghi
  nhật ký**. Trước khi có hàm này, chỉ cần mở trang là cứ 15 giây log dài thêm một
  dòng — kể cả thứ Bảy, Chủ nhật, 7 giờ tối.
- Lọc cả cuối tuần và nghỉ lễ. Lịch nghỉ lấy từ `vnstock.core.utils.market_events`
  (module nội bộ, vendor sẵn trong `vnstock` — không tự nhập tay ngày nào), gồm cả
  nhãn `Compensation` (nghỉ bù khi lễ rơi cuối tuần), không riêng `Holiday`. Đây là
  lịch nghỉ CHUNG của cả nước, không phải luồng chính thức riêng của HNX cho hợp đồng
  tương lai — trùng khớp hầu hết trường hợp nhưng không phủ được các thông báo đóng
  cửa đặc biệt ngoài lịch nghỉ lễ nhà nước, nếu HNX có công bố riêng. Đường import là
  module nội bộ, có thể đổi khi nâng phiên bản `vnstock`; lỗi thì lặng lẽ quay về chỉ
  lọc cuối tuần (`_load_vn_holidays()` trả `{}`), không làm chết cả hàm.
- Nhật ký lưu trên **Supabase** (`core/supabase_client.py`), không phải localStorage
  hay file JSON. Trước đây nằm ở localStorage: đổi máy hoặc xóa dữ liệu trình duyệt là
  mất sạch, không tích lũy qua nhiều ngày. Trước nữa còn có bản ghi
  `static/derivatives_history.json`, nhưng filesystem trên Vercel chỉ đọc nên đường đó
  thực tế luôn rỗng trên production.
  - Gọi thẳng REST API của Supabase (PostgREST) qua `requests`, không dùng SDK
    `supabase` chính thức — SDK kéo theo httpx/postgrest-py/gotrue/realtime, nặng
    không cần thiết cho hai thao tác insert/select đơn giản. Đúng phong cách các
    client khác trong dự án (SSI, FRED, vnstock đều gọi REST trực tiếp).
  - Dùng `SUPABASE_KEY` dạng **service_role**, không phải anon: mọi lượt ghi/đọc đều
    đi qua backend, trình duyệt không bao giờ gọi thẳng vào Supabase. service_role bỏ
    qua RLS nên không cần bật policy công khai cho bảng — khóa đó tuyệt đối không được
    lộ ra phía client.
  - Schema bảng `derivatives_signals` và các bước tạo project nằm trong
    `.env.example`. Thiếu `SUPABASE_URL`/`SUPABASE_KEY` (hoặc project đã bị Supabase
    tự tạm dừng do không hoạt động) thì nhật ký vẫn tính tín hiệu bình thường nhưng
    không lưu được gì — giao diện hiện cảnh báo màu vàng ở cả bảng lẫn hàng tổng kết,
    không âm thầm coi như "chưa có lệnh nào".
  - `POST /api/derivatives/evaluate-log` không còn nhận `signals` từ client nữa —
    server tự đọc đúng nhật ký của ngày đó từ Supabase. Trước đây client tính "hôm
    nay" bằng `new Date()` theo múi giờ **trình duyệt**, có thể lệch với "hôm nay"
    theo giờ Việt Nam (`vn_now()`) mà server dùng; nay chỉ còn một nơi quyết định
    ngày, không còn hai nguồn có thể lệch nhau.
- Từ khóa nhận hướng trong `price_action` phải đủ dài để không nuốt nghĩa nhau. Bản
  cũ để `"long"`, `"short"` trần, mà chính câu mô tả trung lập tự sinh là *"hai phe
  Long/Short đang giằng co"* — khớp cả hai phía rồi rơi vào nhánh Short. `"tăng"`
  cũng khớp trong *"từ chối tăng"*.
- `POST /api/derivatives/evaluate-log` chấm kết quả thật: dò **nến 1 phút của
  VN30F1M** sau thời điểm phát tín hiệu xem chạm SL hay TP1 trước. Hàng ROI chỉ cộng
  lệnh **đã chốt**; đang mở / hết phiên chưa chạm / không xác định / thiếu dữ liệu đều
  đếm riêng và ghi rõ. Trước đây nó cộng khoảng cách Entry→TP1 của mọi tín hiệu, tức
  ngầm giả định lệnh nào cũng thắng.
- Nguồn nến: `vnstock_client.get_historical_data("VN30F1M", d, d, "1m", "VCI")` —
  241 nến mỗi phiên, 09:00–14:45. **Phải dùng đường này**, đừng dùng
  `ssi_client.get_intraday()`: thiếu credential SSI thì nó tự sinh giá ngẫu nhiên
  (`_generate_mock_intraday`), mà tính lãi lỗ từ giá bịa còn tệ hơn con số cũ.
  `get_historical_data` trả `[]` khi hỏng, giao diện khi đó để trống kèm cảnh báo.
- Một nến 1 phút quét qua **cả** SL lẫn TP thì không biết mức nào tới trước → để
  `khong_xac_dinh`, không đoán. Giá vào lệnh lấy trung điểm dải Entry và giá thoát lấy
  đúng mức SL/TP (chưa tính trượt giá) — hai giả định này hiện ngay trong `assumptions`
  của API.

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
- Project Supabase tham chiếu trong `.env` cũ đã **chết** (DNS không phân giải được -
  domain không tồn tại, khả năng bị Supabase tự tạm dừng do không hoạt động). Cần tạo
  project mới rồi cập nhật `SUPABASE_URL`/`SUPABASE_KEY` cả local lẫn Vercel (xem
  `.env.example` để biết schema và các bước) thì nhật ký M5 mới thật sự lưu được.
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
