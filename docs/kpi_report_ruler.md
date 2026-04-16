Mình thấy hướng bạn vừa nêu **hợp lý hơn nhiều** so với 2 cực đoan:

* cực đoan A: chỉ exact match, thiếu là bỏ hẳn
* cực đoan B: chia đều mọi week/month xuống daily

Mình đề xuất chốt theo kiểu **coverage-first, no prorating**:

## Nguyên tắc chính

Khi build KPI cho một kỳ report:

### 1. Ưu tiên cộng từ các row `Day` nằm trong kỳ

Vì `Day` là dữ liệu chi tiết nhất, sát thực tế nhất.

### 2. Nếu còn khoảng trống chưa được phủ, mới dùng tiếp các row `Week/Month/Year`

Nhưng chỉ dùng khi row đó:

* **nằm trọn trong kỳ report**
* và **không đè lên các ngày đã được phủ bởi row chi tiết hơn**

### 3. Không chia đều row `Week/Month/Year` xuống từng ngày

Tức là không prorate.

### 4. Không dùng row chỉ overlap một phần

Ví dụ report là `2025-04-10 -> 2025-04-20`, mà có row `Month` cho `2025-04-01 -> 2025-04-30` thì **không dùng** row này để tính cho custom range đó.

---

# Vì sao cách này hợp lý

## Nó giữ đúng tinh thần Option B

Roadmap đã chốt rằng row phủ nhiều ngày chỉ dùng ở đúng kỳ tổng, không chia đều xuống daily. 

Cách bạn vừa đề xuất vẫn tôn trọng điều đó, vì:

* row `Week/Month/Year` chỉ được dùng như **một block tổng**
* không bị bẻ nhỏ thành daily giả lập

## Đồng thời nó thực dụng hơn “exact match only”

Vì thực tế user có thể nhập lẫn:

* nhiều ngày riêng lẻ
* một tuần
* một tháng

Nếu chỉ exact match thì sẽ bỏ lỡ rất nhiều dữ liệu hợp lệ.

---

# Mô hình mình đề xuất

## Coverage hierarchy

Ưu tiên theo độ chi tiết:

```text
Day > Week > Month > Year
```

Nghĩa là:

* nếu ngày nào đã có `Day` thì không để `Week/Month/Year` đè lên
* nếu chưa có `Day`, có thể dùng `Week` phủ phần còn thiếu
* nếu vẫn thiếu, mới xét `Month`
* rồi đến `Year`

---

# Cách hiểu bằng ví dụ

## Ví dụ 1: Weekly report

Report: `2025-04-14 -> 2025-04-20`

Dữ liệu có:

* `Day` cho 14, 15, 16
* `Week` cho 14-20
* `Month` cho 01-30

### Kết quả nên là:

* lấy `Day` cho 14, 15, 16
* **không lấy `Week`**, vì `Week` đè lên 3 ngày đã có data chi tiết hơn, mà lại không thể tách phần còn lại nếu không prorate
* `Month` cũng không dùng vì không exact block phù hợp và còn thô hơn

### Nghĩa là:

* summary KPI chỉ tính từ các `Day` đã có
* coverage = partial
* phải báo rõ là “KPI coverage incomplete”

Đây là điểm quan trọng:
**không phải lúc nào cũng cố lấp đầy đủ 100% kỳ report**.

---

## Ví dụ 2: Monthly report

Report: `2025-04-01 -> 2025-04-30`

Dữ liệu có:

* `Day` cho 01-10
* `Week` cho 14-20
* `Week` cho 21-27
* `Month` cho 01-30

### Kết quả nên là:

* lấy `Day` cho 01-10
* lấy `Week` 14-20 và 21-27 nếu các block đó chưa bị `Day` phủ
* **không lấy `Month` 01-30** vì nó overlap với các block chi tiết hơn, mà không thể trừ phần overlap một cách chính xác nếu không có raw composition

=> summary KPI được cộng từ các block rời rạc hợp lệ:

* 10 day rows
* 2 week rows

và báo:

* coverage không full tháng nếu còn gap 11-13 và 28-30

---

## Ví dụ 3: Monthly report nhưng chỉ có 1 row `Month`

Report: `2025-04-01 -> 2025-04-30`

Dữ liệu có:

* `Month` 01-30

### Kết quả:

* dùng luôn row `Month`
* coverage = full
* rất đẹp, đúng nghiệp vụ

---

## Ví dụ 4: Custom report

Report: `2025-04-10 -> 2025-04-20`

Dữ liệu có:

* `Month` 01-30
* không có `Day`, không có `Week`

### Kết quả:

* **không dùng** row `Month`
* vì row này không nằm trọn trong custom range
* và nếu dùng thì là lấy số tháng áp vào 10 ngày, sai nghiệp vụ

=> KPI unavailable hoặc coverage = 0

Đây là lý do mình nói custom range là case khó nhất.

---

