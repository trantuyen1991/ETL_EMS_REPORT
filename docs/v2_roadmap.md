# 1. Những gì đã chốt cho V2

## Cấu trúc report

Report V2 sẽ đi theo 8 section chính:

1. Executive Summary
2. Energy Overview
3. Area Breakdown

   * Diode
   * Ico
   * Sakari
4. Utility Usage
5. Production & KPI
6. Comparison vs Previous Period
7. Daily Summary Tables
8. Raw Detail Exports

---

## Kỳ báo cáo

Hỗ trợ 4 loại:

* Daily
* Weekly
* Monthly
* Custom date range

Bạn muốn để option này ở `.env`.
Tức là V2 có thể đi theo hướng:

* `.env` = default mode
* CLI = override khi chạy thực tế

---

## Quy tắc xử lý `energy_kpi`

### Khi 1 row phủ nhiều ngày

Chốt **Option B**:

* chỉ hiển thị ở đúng kỳ tổng
* không chia đều xuống từng ngày

Quyết định này rất đúng về nghiệp vụ.

Và mình đồng ý hoàn toàn với đề xuất UX của bạn: trong report nên có một chỗ nói rõ rằng dữ liệu KPI hiện có không tối ưu cho đúng kỳ đang xem, đồng thời gợi ý:

“Nhập KPI theo ngày hoặc theo đúng chu kỳ của report là tốt nhất.”

Cách đúng hơn
Giai đoạn hiện tại

Giữ rule:

row Day có giá trị 0 hoặc production = 0
→ vẫn là covered day hợp lệ
không có row nào
→ uncovered day, chưa kết luận là lỗi hay nghỉ
Giai đoạn sau

Khi bạn có:

lịch nghỉ
shift calendar
production calendar

thì mới refine tiếp:

uncovered day nhưng nằm trong non-working calendar
→ classify là non_working_day
uncovered day nhưng là working day
→ classify là missing_kpi_input
Cách này sạch hơn rất nhiều.

Đề xuất UX/report mà mình thấy rất hợp

Bạn vừa đề xuất một message rất đúng hướng.
Mình gợi ý bản tiếng Anh phù hợp hơn để dùng trong report sau này:

Short note

KPI data is not fully aligned with the current report period.

Expanded note

Some uncovered days may be non-working days or may have been entered using a different KPI time frame. For best accuracy, enter KPI daily or for the exact report period.

Câu này rất dùng được trong:

detail report
note dưới section Production & KPI
tooltip/info box
2. Ở bước render sau này

Trong bảng summary KPI theo ngày, nếu ngày nào không có KPI row trong DB thì vẫn nên tạo row đại diện cho ngày đó, rồi:

để trống
hoặc đổi màu
hoặc có note/message

Mình thấy đây là cách hiển thị tốt nhất, vì:

người dùng nhìn ra được toàn bộ chu kỳ report
biết ngày nào có dữ liệu, ngày nào không
không nhầm giữa “không có row” và “giá trị = 0”

Và nó rất khớp với rule vừa chốt:

có row và giá trị 0 → vẫn là dữ liệu hợp lệ
---

## KPI logic

### Nguồn đáng tin

* `prod`: do user nhập trong `energy_kpi`
* `energy`: có thể lấy từ view meter
* `kpi = energy / prod`

Bạn nói `Total_energy` trong `energy_kpi` cũng cùng source và không sợ sai.
Mình đề xuất chốt luôn như sau để tránh mơ hồ:

## Quy tắc ưu tiên dữ liệu

* **Production**: lấy từ `energy_kpi`
* **Energy**: ưu tiên tự tính từ views energy
* **KPI**: luôn tính lại từ `energy / prod`

Cách này giúp:

* report luôn nhất quán
* tránh phụ thuộc vào giá trị nhập tay / lưu thừa trong `energy_kpi`
* sau này dễ audit hơn

---

## KPI theo khu vực

Bắt buộc có trong V2:

* Total plant KPI
* Diode KPI
* Ico KPI
* Sakari KPI

---

## Utility section

Chốt:

* Summary cards / summary table ở đầu section
* Nếu range nhiều ngày thì có thêm daily utility table phía dưới

---

## Comparison

Chuẩn bị data càng chi tiết càng tốt.
Mình đồng ý hoàn toàn. Nghĩa là V2 nên chuẩn bị comparison cho:

* Total Energy
* Total Production
* Total KPI
* Energy per area
* Production per area
* KPI per area
* Utility totals

UI có thể chưa dùng hết ngay, nhưng data layer nên chuẩn bị trước.

---

## Raw export

Export theo từng dataset, không gộp 1 file:

* energy_all_raw.csv
* energy_diode_raw.csv
* energy_ico_raw.csv
* energy_sakari_raw.csv
* utility_raw.csv
* kpi_raw.csv

---

## Output files

### Ưu tiên 1

* **PDF**: file chính, gọn, đẹp, chứa thông tin quan trọng

### File phụ

* **CSV**: theo từng dataset để kiểm tra

### HTML

* **2 file HTML**

  * `report_pdf.html`: HTML tối ưu để convert PDF
  * `report_detail.html`: HTML mở trực tiếp bằng browser, chứa toàn bộ report_pdf.html có thêm bảng detail scroll ngang/dọc

Ý tưởng này rất hay. Đây là một quyết định kiến trúc tốt cho V2.

---

# 2. Ý kiến về ECharts CDN

Mình thấy hướng dùng **ECharts CDN cho file HTML detail** là hợp lý, nhưng nên tách rõ 2 case:

## Case A — HTML detail mở trực tiếp bằng browser

Dùng CDN là ổn:

* nhẹ repo
* không phải kẹp `echarts.min.js`
* dễ update

## Case B — HTML dùng để export PDF

Dùng thư viện echart.min.js trong "src/templates/assets/vendor/echarts" cho file HTML xuất PDF.

Vì khi export PDF headless:

* nếu máy mất mạng
* hoặc CDN bị chặn
* hoặc Chromium load JS không kịp

thì chart có thể không render ổn định.

---

# 3. Kiến trúc V2 mình đề xuất

V2 nên chia thành 4 tầng rõ ràng:

## A. Source Layer

Phụ trách đọc dữ liệu từ từng source:

* `all_energy`
* `diode_energy`
* `ico_energy`
* `sakari_energy`
* `utility_usage`
* `energy_kpi`

## B. Aggregation Layer

Phụ trách:

* tính summary
* area totals
* utility totals
* production/kpi
* comparison
* daily tables

## C. Rendering Layer

Phụ trách:

* `report_pdf.html`
* `report_detail.html`

## D. Export Layer

Phụ trách:

* PDF
* CSV
* HTML outputs

---

# 4. Các module nên có ở V2

## Giữ lại từ V1

* `mysql_client.py`
* `queries.py`
* `template_service.py`
* `csv_export_service.py`
* `pdf_service.py`
* `logger.py`

## Refactor / mở rộng

* `aggregation_service.py`
* `chart_service.py`
* `file_naming_service.py`
* `report_service.py`

## Nên thêm mới

### `src/services/period_service.py`

Phụ trách:

* resolve daily / weekly / monthly / custom range
* previous period range

### `src/services/energy_service.py`

Phụ trách:

* load + aggregate `all_energy`, `diode_energy`, `ico_energy`, `sakari_energy`

### `src/services/utility_service.py`

Phụ trách:

* load + aggregate `utility_usage`

### `src/services/kpi_service.py`

Phụ trách:

* resolve `energy_kpi`
* chọn row latest theo `dt_lastupdate`
* xử lý đúng kỳ tổng
* build production/kpi dataset

### `src/services/report_builder_service.py`

Phụ trách:

* assemble toàn bộ report context V2

Mình nghĩ `report_service.py` hiện tại có thể chính là nơi này nếu bạn muốn reuse tên cũ.

---

# 5. Report context V2 nên có gì

Mình đề xuất output cuối cùng của data layer sẽ có cấu trúc kiểu này:

```python
{
    "meta": {...},
    "period": {...},
    "summary": {...},

    "energy": {
        "plant": {...},
        "areas": {
            "diode": {...},
            "ico": {...},
            "sakari": {...},
        },
        "daily_rows": [...],
    },

    "utility": {
        "summary": {...},
        "daily_rows": [...],
    },

    "production_kpi": {
        "plant": {...},
        "areas": {
            "diode": {...},
            "ico": {...},
            "sakari": {...},
        },
        "daily_rows": [...],
        "period_rows": [...],
    },

    "comparison": {
        "energy": {...},
        "production": {...},
        "kpi": {...},
        "areas": {...},
        "utility": {...},
    },

    "raw_exports": {
        "all_energy": [...],
        "diode_energy": [...],
        "ico_energy": [...],
        "sakari_energy": [...],
        "utility_usage": [...],
        "energy_kpi": [...],
    }
}
```

Với cấu trúc này:

* PDF dùng phần summary
* HTML detail dùng thêm raw / detailed table
* CSV export lấy từ `raw_exports`

---

# 6. Thiết kế section V2 chi tiết

## 1. Executive Summary

Hiển thị:

* Report period
* Total plant energy
* Total production
* Total KPI
* Total active meters
* Key trend vs previous period

## 2. Energy Overview

Hiển thị:

* Total plant energy
* Daily trend
* Top meters overall
* Comparison vs previous period

## 3. Area Breakdown

Mỗi khu vực:

* Area energy total
* % contribution to plant total
* Top meters in area
* Area comparison vs previous period

## 4. Utility Usage

### Summary

* Domestic water
* Ico chilled water
* Diode chilled water
* Ico air
* Diode air
* Steam
* Sakari water

### Nếu range nhiều ngày

* daily utility table
* utility trend chart

## 5. Production & KPI

### Toàn nhà máy

* Total production
* Total energy
* Total KPI

### Theo khu vực

* Diode production / energy / kpi
* Ico production / energy / kpi
* Sakari production / energy / kpi

## 6. Comparison vs Previous Period

So sánh:

* plant energy
* plant production
* plant kpi
* area energy / production / kpi
* utility totals

## 7. Daily Summary Tables

* plant daily summary
* utility daily summary
* nếu cần: area daily summary

## 8. Raw Detail Exports

Không hiển thị hết vào PDF, chỉ note link/tên file export.

---

# 7. Roadmap V2 theo phase

## Phase 1 — Data foundation

Mục tiêu: mở rộng source layer

### Việc cần làm

* refactor `queries.py` để hỗ trợ multi-source generic hơn
* add source configs cho:

  * `all_energy`
  * `diode_energy`
  * `ico_energy`
  * `sakari_energy`
  * `utility_usage`
  * `energy_kpi`
* viết `period_service.py`
* viết `kpi_service.py` với rule latest row by `dt_lastupdate`
* viết `utility_service.py`

### Deliverable

* lấy đúng raw data cho mọi source
* resolve đúng kỳ báo cáo
* lấy đúng previous period

---

## Phase 2 — Aggregation & business logic

Mục tiêu: build report context V2

### Việc cần làm

* plant energy summary
* area energy summary
* utility summary
* production & KPI summary
* comparison datasets
* daily summary tables

### Deliverable

* 1 `report_context_v2` thống nhất

---

## Phase 3 — Rendering V2

Mục tiêu: có 2 template HTML

### Việc cần làm

* `report_pdf.html`
* `report_detail.html`
* layout 8 sections
* detail html có table scroll
* detail html dùng ECharts CDN

### Deliverable

* 2 HTML output riêng biệt

---

## Phase 4 — Exports

Mục tiêu: xuất đủ file

### Việc cần làm

* PDF từ `report_pdf.html`
* CSV theo từng dataset
* HTML detail output
* file naming chuẩn theo kỳ báo cáo

### Deliverable

* full output bundle cho V2

---

## Phase 5 — Runtime / UX

Mục tiêu: dễ chạy thực tế

### Việc cần làm

* config default period type
* CLI override
* logging job summary
* validation / error handling tốt hơn

### Deliverable

* chạy được như tool thực tế

---

# 8. Mình đề xuất thứ tự implement tối ưu

Để tránh build UI quá sớm, mình khuyên đi thứ tự này:

## Bước 1

`period_service.py`

## Bước 2

`queries.py` refactor cho multi-source

## Bước 3

`utility_service.py`

## Bước 4

`kpi_service.py`

## Bước 5

`aggregation_service.py` refactor thành V2

## Bước 6

`report_service.py` / `report_builder_service.py`

## Bước 7

`report_pdf.html`

## Bước 8

`report_detail.html`

## Bước 9

`csv_export_service.py` mở rộng multi-file export

## Bước 10

`file_naming_service.py` hoàn thiện

---

# 9. Các rủi ro cần lưu ý sớm

## 1. `energy_kpi` nhiều row cùng kỳ

Đã chốt rule:

* chọn row `dt_lastupdate` mới nhất

Rất tốt, cần implement chặt.

## 2. KPI row phủ nhiều ngày

Đã chốt:

* chỉ dùng cho đúng kỳ tổng
* không ép chia về daily

Cần đảm bảo UI daily không hiểu nhầm.

## 3. `all_energy` vs area sums

Mình đề xuất chốt source of truth như sau:

* Plant total energy: lấy từ `all_energy`
* Area energy totals: lấy từ từng area view
* có thể thêm validation log nếu tổng area lệch plant

Cách này vừa theo dữ liệu thật của bạn, vừa có lớp kiểm tra.

## 4. Utility null values

Coi null = 0 như V1.

## 5. PDF vs interactive HTML

Phải tách ngay từ đầu, bạn đã chốt đúng hướng.

---

# 10. Chốt thiết kế về config

Bạn muốn period type trong `.env`, mình đồng ý cho V2 phase đầu.
Mình đề xuất thêm các biến kiểu:

```env
REPORT_PERIOD_TYPE=daily
REPORT_START_DATE=
REPORT_END_DATE=
REPORT_OUTPUT_MODE=all
```

Trong đó:

* `daily`, `weekly`, `monthly`, `custom`
* `REPORT_OUTPUT_MODE=all/pdf/html/csv`

Sau này CLI có thể override.

---

# 11. Đề xuất chốt phạm vi V2.0

Để V2 không bị quá lớn, mình khuyên **V2.0** chỉ chốt các mục sau:

* multi-source energy
* utility section
* production & KPI section
* comparison datasets đầy đủ
* 2 HTML templates
* PDF + CSV multi-file
* logging & file naming hoàn chỉnh

## Chưa cần ở V2.0

* XLSX
* Windows exe packaging final
* scheduler
* anomaly detection

Những cái đó nên để **V2.1 / V2.2**

---


