Có 1 thay đổi lớn như sau:
1. về energy:
	- Mỗi 1 khu vực sẽ có những meter của trạm phân phối tổng như: 
		+ Diode:  MSB1, MSB2
		+ ICO: MSB1, MSB2
		+ Skari:  DBADH " tủ này lấy từ MSB1 của ICO".
	- Trong mỗi một khu vực cũng sẽ có vài vị trí chưa được đo đạc, 
		+ ví dụ tủ DBADH của Sakari đo tổng năng lượng điện tiêu thụ của toàn bộ SAKARI, 
                 nhưng tổng các meter con bên trong sẽ luôn nhỏ hơn DBADH do còn vài nơi chưa có meter nên mình sẽ tự thêm 1 object trong context đại diện cho tải không xác định này để hiển thị ở column cuối cùng của bảng Daily Energy Detail.
	- Do đó:
		+ Khi tính tổng cho toàn nhà máy thì mình sẽ chỉ tính tổng các đồng hồ phân phối chính của từng khu vực. " Có thể lấy column Total_engy trong table energy_kpi"
		+ Khi tính tổng của mỗi khu vực cũng chỉ cần lấy tổng của các đồng hồ phân phối chính." Có thể lấy column ICO_engy,DIODE_engy,SAKARI_engy trong table energy_kpi"
		+ Khi tính top cho toàn nhà máy hoặc một khu vực thì luôn luôn bỏ các đồng hồ tổng ra khỏi danh sách.
	- Sau khi quy hoạch theo cách trên thì mình sẽ hiển thị thêm energy cho các tải không xác định luôn.
	- Ngoài ra có thể kiểm tra chéo, nếu tổng tiêu thụ của các đồng hồ nhánh bên dưới mà lớn hơn của đồng hồ tổng nhánh đó thì cảnh báo dữ liệu bất thường.
2. về dữ liệu cảm biến của phần uitility lưu ở bảng processvalue có các column sau:
	- ich_rettemp: là nhiệt độ(°C) nước hồi về của chiller khu ICO.
	- ich_suptemp: là nhiệt độ(°C) nước cấp của chiller khu ICO.
	- ich_supflow: là lưu lượng nước(Kg/H) cấp của chiller khu ICO.
	- ich_suppress: là áp suất(Bar) nước cấp của chiller khu ICO.

	- dch_rettemp: là nhiệt độ(°C) nước hồi về của chiller khu DIODE.
	- dch_suptemp: là nhiệt độ(°C) nước cấp của chiller khu DIODE.
	- dch_supflow: là lưu lượng nước(Kg/H) cấp của chiller khu DIODE.
	- dch_suppress: là áp suất(Bar) nước cấp của chiller khu DIODE.

	- iac_press: là áp suất khí nén(Bar) của khu vực ICO.
	- iac_aitflow: là lưu lượng khí nén(m3/H) của khu vực ICO.

	- dac_press: là áp suất khí nén(Bar) của khu vực DIODE.
	- dac_airflow: là lưu lượng khí nén(m3/H) của khu vực DIODE.

	- boi_steamflow: là lưu lượng hơi(m3/H).
	- boi_steampress: là áp suất hơi(Bar). 

	- dom_waterflow:lưu lượng nước(m3/Hr) sinh hoạt
3.yêu cầu cho phần report cảm biến này:
	- là hiển thị các giá trị MAX,MIN,AVG theo period.
	- vẽ biểu đồ đường.
