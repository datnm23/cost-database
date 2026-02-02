# **Báo Cáo Nghiên Cứu Chuyên Sâu Về Hệ Thống Hóa và Tiêu Chuẩn Hóa Danh Pháp Công Tác Xây Dựng Tại Việt Nam: Từ Định Mức Pháp Lý Đến Tích Hợp Mô Hình Thông Tin Công Trình (BIM)**

## **1\. Tổng Quan Về Sự Cần Thiết Của Việc Chuẩn Hóa Danh Pháp Trong Ngành Xây Dựng**

Trong bối cảnh ngành xây dựng Việt Nam đang trải qua giai đoạn chuyển đổi số mạnh mẽ, nhu cầu về một hệ thống ngôn ngữ chung để giao tiếp dữ liệu giữa các bên tham gia dự án trở nên cấp thiết hơn bao giờ hết. Sự phân mảnh thông tin giữa các giai đoạn thiết kế, lập dự toán, đấu thầu và quản lý thi công đang tạo ra những rào cản lớn, dẫn đến lãng phí nguồn lực và gia tăng rủi ro tranh chấp. Hệ thống định mức dự toán xây dựng do Bộ Xây dựng ban hành, điển hình là Thông tư 12/2021/TT-BXD, đóng vai trò là xương sống pháp lý cho việc quản lý chi phí đầu tư công.1 Tuy nhiên, cấu trúc dữ liệu truyền thống của hệ thống này, vốn được thiết kế cho quy trình làm việc trên giấy tờ và bảng tính thủ công, đang bộc lộ những hạn chế đáng kể khi tích hợp vào các nền tảng kỹ thuật số hiện đại như Mô hình Thông tin Công trình (BIM).

Vấn đề cốt lõi nằm ở "danh pháp" (naming convention) – cách thức đặt tên và mã hóa các đầu mục công việc (work items). Một cái tên không chỉ đơn thuần là nhãn dán, mà là một gói tin chứa đựng các thuộc tính kỹ thuật, quy cách vật liệu, phương biện pháp thi công và vị trí không gian. Khi các kỹ sư định giá (QS) phải dành hàng nghìn giờ để "biên dịch" thủ công các đối tượng từ mô hình 3D sang mã hiệu định mức, sai sót là điều không thể tránh khỏi.2 Do đó, nghiên cứu này không chỉ dừng lại ở việc phân tích hiện trạng, mà còn đi sâu vào việc xây dựng một khung chuẩn hóa tên gọi mới, kết hợp sự chặt chẽ của pháp lý Việt Nam với tính linh hoạt của các tiêu chuẩn quốc tế như ISO 19650 và TCVN 12006-2, nhằm tạo ra một dòng chảy dữ liệu liền mạch suốt vòng đời dự án.

## **2\. Phân Tích Cấu Trúc Và Hệ Thống Mã Hóa Theo Pháp Lý Hiện Hành**

Hệ thống định mức xây dựng tại Việt Nam được xây dựng dựa trên nguyên tắc quản lý chi phí chặt chẽ, nơi mỗi công tác được định danh bằng một mã hiệu và một tên gọi mô tả quy cách cụ thể. Thông tư 12/2021/TT-BXD là văn bản pháp lý cao nhất hiện nay quy định về vấn đề này, thay thế cho các quy định trước đó và thiết lập một trật tự mới cho việc phân loại công tác.4

### **2.1. Cấu Trúc Mã Hiệu Định Mức (Coding System Ontology)**

Hệ thống mã hiệu trong định mức dự toán không phải là những con số ngẫu nhiên mà là một hệ thống phân loại có cấu trúc (hierarchical classification system), được thiết kế để nhóm các công việc có cùng bản chất kỹ thuật. Mã hiệu bao gồm hai phần chính: phần chữ (tiền tố) và phần số.

#### **2.1.1. Phân loại theo nhóm công tác (Tiền tố chữ cái)**

Tiền tố của mã hiệu định mức thường bao gồm hai chữ cái, trong đó chữ cái đầu tiên xác định loại hình định mức lớn (Phụ lục), và chữ cái thứ hai xác định nhóm công việc cụ thể. Dựa trên dữ liệu từ Thông tư 12/2021/TT-BXD, cấu trúc này được phân rã như sau 1:

* **Nhóm Khảo sát (Prefix C):** Được quy định tại Phụ lục I.  
  * **CA:** Công tác đào đất đá bằng thủ công để lấy mẫu thí nghiệm. Đây là nhóm công tác đầu tiên trong quy trình khảo sát, bao gồm các hoạt động xâm nhập bề mặt đất để thu thập dữ liệu địa chất.1  
  * **CB:** Công tác thăm dò địa vật lý. Nhóm này bao gồm các phương pháp không phá hủy như đo điện, đo địa chấn để xác định cấu trúc địa tầng.  
  * **CC:** Công tác khoan. Bao gồm khoan xoay bơm rửa, khoan lấy mẫu, phục vụ cho việc khảo sát địa chất công trình chuyên sâu.  
  * **CD:** Công tác đặt ống quan trắc mực nước ngầm.  
  * **CE:** Công tác thí nghiệm tại hiện trường (như thí nghiệm xuyên tiêu chuẩn SPT, cắt cánh).  
  * **CF \- CK:** Các công tác đo đạc, lập lưới khống chế, đo vẽ bản đồ địa hình và số hóa bản đồ.  
* **Nhóm Xây dựng (Prefix A):** Được quy định tại Phụ lục II, đây là nhóm mã hiệu phổ biến và quan trọng nhất trong lập dự toán công trình.7  
  * **AA:** Công tác chuẩn bị mặt bằng. Bao gồm phát quang, chặt cây, phá dỡ kết cấu cũ, và công tác đất sơ bộ.  
  * **AB:** Công tác đào, đắp đất, đá, cát. Nhóm này phân biệt rõ rệt giữa đào thủ công và đào máy, cũng như các cấp đất đá khác nhau.  
  * **AC:** Công tác gia cố nền móng. Bao gồm các công nghệ phức tạp như cọc khoan nhồi, tường vây Barrette, đóng cọc bê tông cốt thép.  
  * **AD:** Công tác xây dựng mặt đường. Bao gồm các lớp móng đường, mặt đường nhựa, bê tông xi măng.  
  * **AE:** Công tác xây gạch, đá. Nhóm này bao trùm các công việc xây tường, xây móng, xây trụ bằng các loại vật liệu nung và không nung.  
  * **AF:** Công tác bê tông. Đây là nhóm lớn nhất, bao gồm sản xuất vữa, đổ bê tông tại chỗ cho các cấu kiện móng, cột, dầm, sàn, mái.  
  * **AG:** Công tác cấu kiện bê tông đúc sẵn. Bao gồm đúc, vận chuyển và lắp dựng các cấu kiện như cọc, dầm cầu, tấm tường.9  
  * **AI:** Công tác kết cấu thép. Bao gồm gia công và lắp dựng khung thép, mái tôn, và các cấu kiện kim loại khác.8  
  * **AK:** Công tác hoàn thiện. Bao gồm trát, láng, ốp, lát, sơn, làm trần, cửa.  
  * **AL:** Các công tác khác (công tác rọ đá, bấc thấm, hoàn thiện hạ tầng kỹ thuật).4  
* **Nhóm Lắp đặt và Sửa chữa:**  
  * Phụ lục III quy định các mã hiệu cho công tác lắp đặt hệ thống kỹ thuật (điện, nước, thông gió).5  
  * Phụ lục VI quy định các mã hiệu cho công tác sửa chữa, bảo dưỡng (thường bắt đầu bằng **S**, ví dụ **SA** cho phá dỡ, **SB** cho sửa chữa kết cấu).5

#### **2.1.2. Phân loại chi tiết (Phần số)**

Phần số theo sau tiền tố chữ cái thường bao gồm 5 chữ số (ví dụ: AF.11111), tuân theo nguyên tắc phân cấp từ tổng quát đến chi tiết:

1. **Chữ số đầu:** Nhóm loại công tác (Ví dụ trong AF: 1 là bê tông móng, 2 là bê tông tường...).  
2. **Chữ số thứ hai:** Phương pháp thi công hoặc loại vật liệu chính (Ví dụ: đổ thủ công hay đổ máy, bê tông thương phẩm hay trộn tại chỗ).  
3. **Chữ số thứ ba và bốn:** Quy cách kỹ thuật cụ thể (Chiều dày, chiều cao, kích thước tiết diện).  
4. **Chữ số thứ năm:** Đặc tính vật liệu chi tiết (Mác vữa, loại đá cốt liệu).

Ví dụ phân tích mã hiệu **AF.11111**:

* **AF:** Công tác bê tông.  
* **1:** Bê tông móng.  
* **1:** Chiều rộng \<= 250 cm.  
* **1:** Vữa bê tông mác 150\.  
* **1:** Đá 4x6 (Giả định dựa trên logic quy ước thông thường của định mức).

### **2.2. Phân Tích Cú Pháp Đặt Tên Công Tác (Syntax Analysis)**

Tên công tác trong định mức nhà nước được xây dựng dựa trên một cú pháp mô tả (descriptive syntax) nhằm định nghĩa chính xác phạm vi công việc để xác định đơn giá. Qua phân tích hàng nghìn đầu mục công việc trong tài liệu 1 và các nguồn dữ liệu bổ sung 5, có thể rút ra cấu trúc cú pháp chuẩn như sau:

**\[Hành động\] \+ \[Đối tượng chính\] \+ \[Vị trí/Phạm vi\] \+ \+ \[Phương pháp thi công/Vật liệu\]**

#### **2.2.1. Phân tích chi tiết các thành phần cú pháp**

1. **Hành động (Verb):** Thường là các động từ chỉ hoạt động thi công như "Đào", "Đắp", "Xây", "Đổ", "Lắp đặt", "Gia công". Trong một số trường hợp, hành động bị ẩn đi (ví dụ: "Bê tông móng" thay vì "Đổ bê tông móng"), nhưng vẫn được hiểu ngầm định là thi công trọn gói.1  
2. **Đối tượng chính (Object):** Là thành phần chịu tác động trực tiếp, ví dụ: "đất", "đá", "tường", "cột", "dầm", "sàn".  
3. **Vị trí/Phạm vi (Location/Scope):** Xác định nơi chốn hoặc giới hạn của công việc, ví dụ: "móng", "tầng hầm", "trên cạn", "dưới nước".  
4. **Thông số kỹ thuật (Parameters):** Đây là phần quan trọng nhất để phân biệt các mã hiệu. Các thông số thường gặp bao gồm:  
   * *Kích thước hình học:* Chiều dày (\<=33cm), Chiều cao (\<=16m, \<=50m), Chiều rộng, Tiết diện.6  
   * *Cấp loại:* Cấp đất (I, II, III, IV), Cấp đá.4  
5. **Phương pháp/Vật liệu (Method/Material):** Mô tả công nghệ hoặc vật liệu sử dụng, ví dụ: "bằng thủ công", "bằng máy đào 1.25m3", "vữa xi măng PC30", "đá 1x2".1

#### **2.2.2. Ví dụ minh họa từ dữ liệu thực tế**

* **Mã hiệu CA.11100 (Khảo sát):**  
  * Tên: "ĐÀO KHÔNG CHỐNG ĐỘ SÂU TỪ 0M ĐẾN 2M".1  
  * Phân tích: Hành động (Đào) \+ Phương pháp (Không chống) \+ Quy cách (Độ sâu 0-2m).  
  * Lưu ý: Tên này phụ thuộc vào chương "Đào đất đá bằng thủ công", nên yếu tố "thủ công" và "đất đá" được hiểu ngầm từ tiêu đề chương.  
* **Mã hiệu AE.22200 (Xây dựng \- Giả định dựa trên cấu trúc):**  
  * Tên điển hình: "Xây tường thẳng, chiều dày \> 33 cm, gạch 6.5x10.5x22, vữa xi măng PC30".6  
  * Phân tích: Hành động (Xây) \+ Đối tượng (Tường thẳng) \+ Kích thước (Chiều dày \> 33cm) \+ Vật liệu (Gạch... vữa...).  
* **Mã hiệu AF.1xxx (Bê tông):**  
  * Tên: "Bê tông móng, chiều rộng \<= 250 cm, vữa bê tông PC30".  
  * Đặc điểm: Sử dụng các toán tử so sánh (\<=, \>) để phân loại định mức.

### **2.3. Những Bất Cập Của Hệ Thống Hiện Hành Trong Bối Cảnh Số Hóa**

Mặc dù hệ thống tên gọi hiện tại phục vụ tốt cho mục đích quản lý nhà nước và thanh quyết toán thủ công, nó bộc lộ nhiều điểm yếu chí mạng khi áp dụng vào quy trình BIM và tự động hóa.

**Thứ nhất, tính mô tả dài dòng và thiếu cấu trúc dữ liệu.** Tên công tác thường là các chuỗi văn bản dài (long strings), chứa đựng nhiều thông tin hỗn hợp mà không có sự phân tách rõ ràng giữa các trường dữ liệu (fields). Ví dụ, thông tin về "chiều dày" và "mác vữa" nằm chung trong một câu, khiến máy tính khó tự động trích xuất (parse) để liên kết với các tham biến trong mô hình BIM.1

**Thứ hai, sự không nhất quán trong quy ước.** Việc sử dụng các ký tự đặc biệt như dấu phẩy, dấu ngoặc đơn, ngoặc vuông không tuân theo một quy tắc lập trình nào. Có lúc sử dụng "nhỏ hơn hoặc bằng", có lúc dùng "≤", có lúc dùng "\<=". Sự thiếu nhất quán này làm giảm khả năng tìm kiếm và lọc dữ liệu trên các phần mềm dự toán như G8 hay Eta, buộc người dùng phải nhớ mã hiệu thay vì tìm theo tên.11

**Thứ ba, thiếu tính định danh duy nhất (Unique Identifier) độc lập.** Tên công tác thường phụ thuộc vào ngữ cảnh của Chương hoặc Nhóm. Ví dụ, "Đào đất" xuất hiện ở cả phần Xây dựng (AB) và Khảo sát (CA), nếu tách rời mã hiệu, tên gọi này trở nên mơ hồ. Trong môi trường CDE (Môi trường dữ liệu chung) của BIM, mỗi đối tượng thông tin cần một định danh duy nhất và rõ ràng.12

## **3\. Chuyển Đổi Số Và Các Tiêu Chuẩn Quốc Tế Về Quản Lý Thông Tin**

Để giải quyết các hạn chế nêu trên, ngành xây dựng Việt Nam đang hướng tới việc áp dụng các tiêu chuẩn quốc tế về quản lý thông tin, đặc biệt là bộ tiêu chuẩn ISO 19650 và hệ thống phân loại TCVN 12006-2.

### **3.1. Tiêu chuẩn ISO 19650 và TCVN 14177**

Bộ tiêu chuẩn ISO 19650 (được chuyển dịch thành TCVN 14177\) là khung quy định quốc tế về quản lý thông tin sử dụng BIM. Một trong những yêu cầu cốt lõi của tiêu chuẩn này là quy ước đặt tên cho các "gói thông tin" (Information Containers) – bao gồm file, bản vẽ, mô hình và tài liệu.12

#### **3.1.1. Quy ước đặt tên gói thông tin (Container Naming Strategy)**

Theo ISO 19650-2 và Phụ lục quốc gia (National Annex) của nhiều nước, một tên file chuẩn phải bao gồm các trường dữ liệu (metadata fields) được ngăn cách bởi dấu gạch ngang (-). Cấu trúc phổ biến được áp dụng tại các dự án BIM ở Việt Nam hiện nay là 13:

**\- \- \[Hệ thống/Khu vực\] \- \[Vị trí/Cao độ\] \- \[Loại tài liệu\] \- \-**

* *Dự án (Project ID):* Mã định danh dự án (2-6 ký tự).  
* *Bên tạo lập (Originator):* Mã đơn vị thực hiện (ví dụ: ARC cho Kiến trúc, STR cho Kết cấu).  
* *Hệ thống/Khu vực (Volume/System):* Phân khu chức năng hoặc hệ thống kỹ thuật.  
* *Vị trí/Cao độ (Level/Location):* Tầng hoặc cao độ (ví dụ: 01, ZZ, XX).  
* *Loại tài liệu (Type):* M3 (Mô hình 3D), DR (Bản vẽ 2D), DO (Tài liệu).  
* *Bộ môn (Discipline):* A (Kiến trúc), S (Kết cấu), M (Cơ khí).  
* *Số thứ tự (Number):* Dãy số (0001, 0002...).

*Ví dụ:* VNM-ABC-Z1-01-M3-A-0001 (Mô hình 3D kiến trúc tầng 1, khu vực 1 của dự án VNM do công ty ABC thực hiện).

Quy ước này giải quyết tốt vấn đề quản lý *file*, nhưng chưa đi sâu vào việc đặt tên cho *nội dung bên trong file* – tức là các cấu kiện (Elements) và công tác (Work Items) trong bảng dự toán. Đây là khoảng trống lớn mà nghiên cứu này cần lấp đầy.

### **3.2. Hệ thống phân loại TCVN 12006-2 (ISO 12006-2)**

TCVN 12006-2:202X (dự thảo tương đương ISO 12006-2:2015) cung cấp khung phân loại cho thông tin xây dựng.16 Tiêu chuẩn này không đưa ra một danh sách phân loại cứng nhắc, mà cung cấp các nguyên tắc để xây dựng các bảng phân loại (classification tables) như OmniClass (Mỹ) hay UniClass 2015 (Anh).

Tại Việt Nam, việc áp dụng OmniClass hoặc UniClass đang gặp khó khăn do sự khác biệt về hệ thống pháp lý và văn hóa xây dựng. Các mã hiệu trong OmniClass (ví dụ: Table 21 \- Elements) không khớp 1:1 với mã hiệu định mức của Bộ Xây dựng. Ví dụ, OmniClass phân loại theo chức năng (Cột, Dầm), trong khi định mức Việt Nam phân loại theo quy trình thi công và chi phí (Bê tông cột, Ván khuôn cột, Cốt thép cột). Sự lệch pha này (mapping gap) đòi hỏi một lớp "phiên dịch" dữ liệu trung gian.18

### **3.3. Thách thức liên kết dữ liệu BIM và Chi phí (5D BIM)**

Mục tiêu tối thượng của BIM 5D là tự động hóa việc xuất khối lượng và dự toán từ mô hình. Tuy nhiên, rào cản lớn nhất hiện nay là sự không tương thích về ngôn ngữ 20:

* **Ngôn ngữ Mô hình (Model Language):** Các phần mềm như Revit quản lý đối tượng theo Family và Type. Tên Family thường do người dùng tự đặt (ví dụ: M\_Concrete\_Rectangular\_Column). Các tham biến (Parameters) chứa thông tin kích thước và vật liệu.  
* **Ngôn ngữ Định mức (Normative Language):** Định mức Việt Nam yêu cầu tên công tác phải chứa đầy đủ thông tin pháp lý (ví dụ: Bê tông cột, đá 1x2, mác 300, chiều cao \<= 4m).

Để nối hai thế giới này, các kỹ sư thường phải gán thủ công mã định mức vào tham biến Assembly Code hoặc Keynote trong Revit.21 Quá trình này rất dễ sai sót nếu tên công tác trong định mức quá phức tạp và khó nhớ.

## **4\. Phân Tích So Sánh Các Phương Án Đặt Tên (Comparative Analysis)**

Để tìm ra giải pháp tối ưu cho việc đặt tên công tác xây dựng tương thích với cả con người và máy tính, nghiên cứu này đã tiến hành so sánh 5 phương án đặt tên khác nhau dựa trên các tiêu chí: Tính dễ đọc (Readability), Tính tự nhiên (Naturalness), Sự ngắn gọn (Conciseness), Sự rõ ràng (Clarity), Khả năng xử lý bởi máy (Parse-ability) và Tính thực tế (Practicality).1

### **4.1. Phương Án 1: Gạch Ngang và Hai Chấm**

* **Cấu trúc:** \[Động từ\]\[Vật liệu\] \- \[Vị trí\] \- : \[Chi tiết\]  
* **Ví dụ:** Đổ Bê tông \- Móng \- M300 : Thương phẩm  
* **Đánh giá:**  
  * *Ưu điểm:* Giao diện sạch sẽ, phân cấp thông tin rõ ràng. Dễ nhìn hơn so với việc dùng nhiều ngoặc.  
  * *Nhược điểm:* Dấu gạch ngang (-) rất dễ bị nhầm lẫn với dấu âm trong các thông số kỹ thuật (ví dụ: cao độ \-1.5m). Điều này gây rủi ro lớn khi máy tính đọc dữ liệu.

### **4.2. Phương Án 2: Dấu Gạch Đứng (Pipe Separator)**

* **Cấu trúc:** \[Động từ\]\[Vật liệu\] | \[Vị trí\] | | \[Ghi chú\]  
* **Ví dụ:** Đổ Bê tông | Móng | M300 | Thương phẩm  
* **Đánh giá:**  
  * *Ưu điểm:* Đây là định dạng tốt nhất cho máy tính (machine-readable) vì dấu | hiếm khi xuất hiện trong văn bản thông thường, giúp việc tách chuỗi (string split) cực kỳ chính xác.  
  * *Nhược điểm:* Mang tính "kỹ thuật" quá cao, nhìn rối mắt và thiếu tự nhiên đối với kỹ sư hiện trường hoặc nhân viên hành chính. Tên công tác bị kéo dài do cần khoảng trắng bao quanh dấu gạch đứng.

### **4.3. Phương Án 3: Dấu Phẩy và Nhóm Logic**

* **Cấu trúc:** \[Động từ\]\[Vật liệu\], \[Vị trí\],, \[Ghi chú\]  
* **Ví dụ:** Đổ Bê tông, Móng, M300, Thương phẩm  
* **Đánh giá:**  
  * *Ưu điểm:* Quen thuộc, giống văn phong liệt kê hàng ngày. Ngắn gọn nhất trong các phương án.  
  * *Nhược điểm:* Rất dễ gây lỗi xử lý dữ liệu vì dấu phẩy thường xuyên xuất hiện trong các con số (ví dụ: 1,5m; 2,5 tấn) theo quy ước số học Việt Nam. Việc phân biệt đâu là dấu phẩy ngăn cách trường dữ liệu và đâu là dấu phẩy thập phân là một bài toán khó cho thuật toán.

### **4.4. Phương Án 4: Từ Khóa Viết Hoa (Tagging)**

* **Cấu trúc:** \[Động từ\]\[Vật liệu\] VỊ TRÍ \[tên\] THÔNG SỐ \[giá trị\] GHI CHÚ \[nội dung\]  
* **Ví dụ:** Đổ Bê tông VỊ TRÍ Móng THÔNG SỐ M300 GHI CHÚ Thương phẩm  
* **Đánh giá:**  
  * *Ưu điểm:* Cực kỳ rõ ràng, không thể nhầm lẫn ý nghĩa của từng phần (self-documenting).  
  * *Nhược điểm:* Tên công tác trở nên quá dài, chiếm dụng không gian hiển thị trên bản vẽ và phần mềm. Việc sử dụng nhiều chữ in hoa gây mỏi mắt (visual fatigue) cho người đọc.

### **4.5. Phương Án 5: Kết Hợp Tự Nhiên (Natural Syntax) \- Đề Xuất**

* **Cấu trúc:** \[Động từ\]\[Vật liệu\]\[vị trí\] \- \- \[Chi tiết\]  
* **Ví dụ:** Đổ bê tông móng \- M300 \- thương phẩm  
* **Đánh giá:**  
  * *Ưu điểm:* Đạt điểm số cao nhất (27/30) trong bảng đánh giá tổng hợp. Cân bằng hoàn hảo giữa tính tự nhiên của ngôn ngữ và khả năng cấu trúc hóa dữ liệu. Loại bỏ hoàn toàn các dấu ngoặc \`\`, () gây rối mắt. Sử dụng trật tự từ ngữ và quy tắc viết hoa/thường để phân định thông tin mà không cần quá nhiều ký tự đặc biệt.  
  * *Nhược điểm:* Cần một thời gian đào tạo ngắn để nhân sự làm quen với quy tắc viết thường vị trí và đặt thông số sau dấu gạch ngang.

## **5\. Đề Xuất Quy Tắc Đặt Tên Chuẩn Hóa: Mô Hình "Tự Nhiên"**

Dựa trên kết quả so sánh, báo cáo đề xuất áp dụng **Mô hình Tự Nhiên (Natural Naming Convention)** làm tiêu chuẩn cho việc đặt tên công tác xây dựng trong môi trường số và BIM tại Việt Nam.

### **5.1. Các Quy Tắc Cốt Lõi (Core Rules)**

Hệ thống này dựa trên 6 quy tắc vàng nhằm đảm bảo tính nhất quán và khả năng tích hợp 1:

1. **Cụm Động từ & Vật liệu (Headline):** Luôn đứng đầu tên công tác, viết hoa chữ cái đầu tiên của câu. Đây là từ khóa chính để tìm kiếm.  
   * *Ví dụ:* **Đổ bê tông**, **Gia công cốt thép**, **Lắp dựng ván khuôn**.  
2. **Vị trí Thi công (Position):** Viết **chữ thường toàn bộ**, đặt ngay sau phần vật liệu mà không dùng dấu ngăn cách đặc biệt. Nếu có nhiều vị trí, nối bằng khoảng trắng.  
   * *Lý do:* Việc viết thường giúp mắt người đọc tự động phân tách cụm từ này với phần Tiêu đề viết Hoa ở đầu, tạo cảm giác ngắt nghỉ tự nhiên (visual hierarchy) mà không cần thêm ký tự.  
   * *Ví dụ:* Đổ bê tông móng, Trát tường ngoài, Sơn dầm trần.  
3. **Thông số Kỹ thuật Chính (Primary Specs):** Được đặt sau dấu gạch ngang (-) đầu tiên. Đây là nơi chứa các thông tin định lượng quan trọng nhất ảnh hưởng đến đơn giá.  
   * *Ví dụ:* \- M300, \- D18, \- dày 200mm.  
4. **Chi tiết Bổ sung/Ghi chú (Secondary Details):** Được đặt sau dấu gạch ngang (-) thứ hai (nếu có). Chứa các thông tin về phương pháp hoặc điều kiện đặc thù.  
   * *Ví dụ:* \- đá 1x2, \- thương phẩm, \- cao \> 16m.  
5. **Hạn chế Ký tự Đặc biệt:** Tuyệt đối không sử dụng dấu ngoặc vuông \`\` hoặc ngoặc đơn () để bao quanh vị trí hoặc thông số, trừ khi đó là quy ước kỹ thuật bắt buộc (ví dụ: công thức kính hộp 6+12A+6).  
6. **Độ dài Tối ưu:** Giữ tên công tác trong khoảng 40-80 ký tự để đảm bảo hiển thị tốt trên các giao diện phần mềm dự toán và bảng tính.

### **5.2. Ứng Dụng Thực Tế Cho Các Nhóm Công Tác Chính**

Việc áp dụng quy tắc chung cần được cụ thể hóa cho từng nhóm công tác đặc thù để đảm bảo tính chính xác kỹ thuật. Dưới đây là hướng dẫn chi tiết cho các nhóm công tác phổ biến nhất.8

#### **5.2.1. Nhóm Công Tác Đất và Cọc (Earthworks & Piling)**

Nhóm này đặc trưng bởi các thông số về cấp đất và kích thước cấu kiện ngầm lớn.

* **Mẫu chuẩn:** \[Hành động\]\[Đối tượng\]\[vị trí\] \- \- \[Cấp đất/Ghi chú\]  
* **Ví dụ:**  
  * Đào đất hố móng bằng máy \- 1.25m3 \- đất cấp 3  
  * Cung cấp cọc PHC \- D500A L=12m  
  * Ép cọc robot \- 200 tấn \- đất cấp 2  
  * Thí nghiệm nén tĩnh cọc \- 200 tấn

#### **5.2.2. Nhóm Công Tác Bê Tông và Cốt Thép (Concrete & Rebar)**

Đây là nhóm chiếm tỷ trọng lớn nhất. Quy tắc cần làm rõ Mác bê tông (Grade) và Loại cấu kiện để map chính xác với định mức AF.

* **Mẫu chuẩn:** \[vị trí\] \-  
* **Ví dụ:**  
  * Bê tông: Đổ bê tông lót móng \- M100 đá 4x6 (Thay vì tên dài dòng: Bê tông lót móng, chiều rộng \<=250cm...).  
  * Bê tông kết cấu: Đổ bê tông dầm sàn \- M350 \- thương phẩm.  
  * Cốt thép: Gia công lắp dựng cốt thép móng \- D\<10 CB300 hoặc Cốt thép cột \- D\>18 CB400.24  
  * Ván khuôn: Lắp dựng ván khuôn vách \- phủ phim dày 18mm.

#### **5.2.3. Nhóm Công Tác Hoàn Thiện (Finishing)**

Nhóm này có độ phức tạp cao do sự đa dạng của vật liệu (gạch, đá, sơn, trần). Tên công tác cần chứa đủ thông tin để định danh vật liệu mà không cần tra cứu hồ sơ kỹ thuật (Spec).

* **Mẫu chuẩn:** \[Động từ\]\[Vật liệu\]\[vị trí\] \- \[Quy cách/Kích thước\] \- \[Mã hiệu/Màu sắc\]  
* **Ví dụ:**  
  * Xây tường gạch ống \- dày 100mm \- vữa M75.  
  * Lát gạch sàn phòng khách \- 600x600 \- Granite bóng kính.  
  * Sơn nước tường trong \- 1 lót 2 phủ \- màu trắng kem.  
  * Lắp dựng trần thạch cao khung chìm \- tấm chống ẩm 9mm.1

#### **5.2.4. Nhóm Kết Cấu Thép và MEP (Structural Steel & MEP)**

Đối với phần lắp đặt (MEP) và kết cấu thép (Mã AI), tên gọi cần tập trung vào quy cách vật liệu và phương pháp liên kết.

* **Ví dụ:**  
  * Gia công dầm thép tổ hợp \- H400x200x8x12 \- SS400.  
  * Lắp dựng kết cấu thép hệ khung giàn \- Bailey.8  
  * Sơn chống cháy kết cấu thép \- 120 phút \- định mức 1.2kg/m2.  
  * Lắp đặt ống thông gió \- tôn tráng kẽm \- bọc cách nhiệt.

### **5.3. Bảng So Sánh Hiệu Quả: Định Mức Cũ vs. Chuẩn Mới**

Để minh chứng cho hiệu quả của phương pháp mới, bảng dưới đây so sánh trực quan giữa cách đặt tên theo định mức hiện hành và theo chuẩn "Tự nhiên" đề xuất:

| Mã Hiệu (Tham khảo) | Tên Theo Định Mức 12/2021 (Hiện hành) | Tên Theo Chuẩn "Tự Nhiên" (Đề Xuất) | Phân Tích Hiệu Quả |
| :---- | :---- | :---- | :---- |
| **AF.11xxx** | Bê tông lót móng, chiều rộng \<= 250 cm, vữa bê tông PC30 | **Đổ bê tông lót móng \- M100 đá 4x6 \- PC30** | Ngắn gọn hơn 30%. Đưa thông số quan trọng (M100) lên vị trí dễ nhìn. Loại bỏ từ "chiều rộng" dư thừa. |
| **AE.22xxx** | Xây tường thẳng, chiều dày \> 33 cm, gạch 6.5x10.5x22, vữa xi măng PC30 | **Xây tường thẳng gạch ống \- dày 330mm \- vữa M75** | Thay thế các ký hiệu toán học (\<, \>) bằng thông số trực quan. Dễ đọc cho cả người và máy. |
| **AG.11xxx** | Bê tông cọc, tiết diện \> 0.1m2 | **Đúc cọc bê tông cốt thép \- tiết diện 400x400 \- M400** | Cụ thể hóa hành động "Đúc". Thay khoảng giá trị chung chung (\>0.1m2) bằng kích thước thực tế của dự án. |
| **AI.6xxxx** | Lắp dựng kết cấu thép dạng Bailey | **Lắp dựng kết cấu thép hệ khung giàn \- Bailey** | Chuẩn hóa thuật ngữ "hệ khung giàn" giúp dễ dàng nhóm (group) các công việc cùng loại khi lọc dữ liệu. |

## **6\. Chiến Lược Triển Khai và Tích Hợp Hệ Thống Phần Mềm**

Việc chuẩn hóa tên gọi chỉ thực sự mang lại giá trị khi được triển khai đồng bộ trên các nền tảng phần mềm quản lý và thiết kế.

### **6.1. Lộ Trình Triển Khai (Migration Roadmap)**

Để chuyển đổi từ hệ thống cũ sang hệ thống mới mà không gây gián đoạn hoạt động, các doanh nghiệp nên áp dụng lộ trình 3 bước (kéo dài khoảng 7 tuần) 1:

1. **Giai đoạn Thí điểm (Pilot \- 1 tuần):**  
   * Lựa chọn 50 công tác phổ biến nhất (chiếm 80% khối lượng dự án như bê tông, thép, xây trát).  
   * Viết lại tên theo format mới và áp dụng thử nghiệm cho một dự án nhỏ.  
   * Thu thập phản hồi từ kỹ sư QS và kỹ sư hiện trường về tính dễ đọc.  
2. **Giai đoạn Triển khai diện rộng (Rollout \- 2 tuần):**  
   * Xây dựng "Từ điển công tác chuẩn" (Master Database) chứa khoảng 300-400 đầu việc thường dùng.  
   * Cập nhật cơ sở dữ liệu này vào thư viện của các phần mềm dự toán (tạo file đơn giá người dùng trong G8, Eta) và phần mềm BIM.  
   * Tổ chức đào tạo nội bộ về quy tắc "viết thường vị trí" và "sử dụng dấu gạch ngang".  
3. **Giai đoạn Giám sát và Tinh chỉnh (Monitor \- 4 tuần):**  
   * Theo dõi các trường hợp ngoại lệ (Edge cases) mà quy tắc chưa bao phủ hết (ví dụ: công tác bảo dưỡng phức tạp).  
   * Tinh chỉnh quy tắc để đảm bảo tính thực tế và linh hoạt.

### **6.2. Giải Pháp Kỹ Thuật Cho Phần Mềm**

#### **6.2.1. Tích hợp với Phần mềm Dự toán (G8, Eta, F1)**

Các phần mềm dự toán tại Việt Nam thường tìm kiếm dựa trên mã hiệu hoặc từ khóa trong tên công tác gốc. Để áp dụng tên chuẩn hóa mà không mất liên kết với định mức nhà nước:

* Sử dụng tính năng "Tên công tác người dùng" hoặc "Sửa tên công tác" có sẵn trong phần mềm.  
* Tạo một bộ cơ sở dữ liệu riêng (User Data) map giữa Mã hiệu gốc (ví dụ AF.11111) và Tên chuẩn hóa mới. Khi lập dự toán, người dùng gọi mã AF.11111 nhưng phần mềm sẽ hiển thị tên chuẩn hóa.11

#### **6.2.2. Tích hợp với Phần mềm BIM (Revit)**

Để tự động hóa việc gán tên công tác cho đối tượng 3D, cần thiết lập một quy trình Mapping dữ liệu 23:

* **Sử dụng Keynote hoặc Assembly Code:** Gán mã định mức (ví dụ AF.11111) vào tham biến Keynote hoặc Assembly Code của đối tượng Revit.  
* **Sử dụng Shared Parameters:** Tạo một tham biến chia sẻ (Shared Parameter) tên là VN\_TenCongTac.  
* **Bảng Mapping (Lookup Table):** Xây dựng một file Excel hoặc Text file chứa danh sách ánh xạ: \[Keynote\] \<-\>. Sử dụng Dynamo hoặc Plugin để tự động điền giá trị VN\_TenCongTac dựa trên Keynote đã gán.

Cách làm này cho phép mô hình BIM vừa chứa mã định mức (để phục vụ xuất dự toán theo quy định nhà nước) vừa hiển thị tên công tác chuẩn hóa "Tự nhiên" (để phục vụ quản lý thi công và giao tiếp).

## **7\. Kết Luận và Kiến Nghị**

Nghiên cứu đã chỉ ra rằng việc áp dụng nguyên trạng tên công tác theo định mức Thông tư 12/2021/TT-BXD vào môi trường số là không hiệu quả do tính dài dòng và thiếu cấu trúc dữ liệu. Việc chuẩn hóa danh pháp là bước đi bắt buộc để ngành xây dựng Việt Nam bắt kịp xu hướng BIM và quản lý dự án dựa trên dữ liệu (Data-driven).

**Các kiến nghị chiến lược:**

1. **Chấp nhận chuẩn "Tự nhiên" (Phương án 5):** Các doanh nghiệp nên thống nhất sử dụng cấu trúc \[Động từ\]\[Vật liệu\]\[vị trí\] \- làm chuẩn nội bộ. Đây là điểm cân bằng tối ưu giữa khả năng đọc hiểu của con người và khả năng xử lý của máy tính.  
2. **Xây dựng Thư viện Master:** Không nên để mỗi kỹ sư tự đặt tên ngẫu hứng. Cần có một bộ từ điển công tác chuẩn được ban hành và kiểm soát bởi bộ phận quản lý kỹ thuật/BIM của công ty.  
3. **Tuân thủ ISO 19650 ở cấp độ File:** Đối với việc đặt tên file và thư mục, cần tuân thủ nghiêm ngặt quy ước của ISO 19650 để đảm bảo khả năng tương tác dữ liệu trong CDE. Tuy nhiên, đối với nội dung chi tiết bên trong (tên công tác), hãy ưu tiên sự rõ ràng và hiệu quả thực tế của phương pháp "Tự nhiên".

Bằng cách thực hiện đồng bộ các giải pháp này, chúng ta không chỉ giải quyết được bài toán phân mảnh dữ liệu hiện tại mà còn đặt nền móng vững chắc cho việc ứng dụng các công nghệ tiên tiến hơn như AI và Big Data trong ngành xây dựng Việt Nam tương lai.

---

**Tài liệu trích dẫn:** .1

#### **Nguồn trích dẫn**

1. SO\_SANH\_FORMAT\_DAT\_TEN.md  
2. Trends in BIM Tools Adoption in Construction Project Implementation: A Case Study in Vietnam \- ResearchGate, truy cập vào tháng 2 2, 2026, [https://www.researchgate.net/publication/363263061\_Trends\_in\_BIM\_Tools\_Adoption\_in\_Construction\_Project\_Implementation\_A\_Case\_Study\_in\_Vietnam](https://www.researchgate.net/publication/363263061_Trends_in_BIM_Tools_Adoption_in_Construction_Project_Implementation_A_Case_Study_in_Vietnam)  
3. The Implementation of Building Information Modelling (BIM) in Construction Industry: Case Studies in Vietnam, truy cập vào tháng 2 2, 2026, [https://www.ijetch.org/vol10/1080-K0051.pdf](https://www.ijetch.org/vol10/1080-K0051.pdf)  
4. Điểm mới Thông tư 12/2021/TT /BXD \- XÂY DỰNG KIWI, truy cập vào tháng 2 2, 2026, [http://xaydungkiwi.com/diem-moi-thong-tu-12-2021-tt-bxd-.html](http://xaydungkiwi.com/diem-moi-thong-tu-12-2021-tt-bxd-.html)  
5. Những điểm mới của Thông tư số 12/2021/TT-BXD ban hanh định mức xây dựng, truy cập vào tháng 2 2, 2026, [https://dutoaneta.vn/nhung-diem-moi-cua-thong-tu-so-12-2021/](https://dutoaneta.vn/nhung-diem-moi-cua-thong-tu-so-12-2021/)  
6. Tổng hợp các điểm mới về định mức xây dựng theo Thông tư 12/2021/TT-BXD \- MISA AMIS, truy cập vào tháng 2 2, 2026, [https://amis.misa.vn/80002/dinh-muc-xay-dung/](https://amis.misa.vn/80002/dinh-muc-xay-dung/)  
7. Thông tư 09/2024/TT-BXD định mức xây dựng \- Dự toán GXD, truy cập vào tháng 2 2, 2026, [https://dutoan.gxd.vn/dinh-muc/thong-tu-09-2024-TT-BXD.html](https://dutoan.gxd.vn/dinh-muc/thong-tu-09-2024-TT-BXD.html)  
8. \[Tóm tắt\] những cập nhật mới nhất về Định mức xây dựng 2021 (theo Thông tư số 12/2021/TT-BXD) \- HocThatNhanh.vn, truy cập vào tháng 2 2, 2026, [https://hocthatnhanh.vn/dinh-muc-xay-dung-moi-nhat-theo-thong-tu-so-12-2021-tt-bxd](https://hocthatnhanh.vn/dinh-muc-xay-dung-moi-nhat-theo-thong-tu-so-12-2021-tt-bxd)  
9. 2810 | PDF \- Scribd, truy cập vào tháng 2 2, 2026, [https://www.scribd.com/document/795086759/2810-1](https://www.scribd.com/document/795086759/2810-1)  
10. pl1-ket-qua-dinh-muc-du-toan-xay-dung\_in.docx, truy cập vào tháng 2 2, 2026, [https://datafiles.chinhphu.vn/cpp/files/vbpq/pl1-ket-qua-dinh-muc-du-toan-xay-dung\_in.docx](https://datafiles.chinhphu.vn/cpp/files/vbpq/pl1-ket-qua-dinh-muc-du-toan-xay-dung_in.docx)  
11. Trục trặc và cách giải quyết: tra tên công tác trong G8, truy cập vào tháng 2 2, 2026, [https://www.dutoang8.com/forum/printer\_friendly\_posts.asp?TID=26606\&SID=c8d8ecb4dbe92a1138f4zbezd437fz9f](https://www.dutoang8.com/forum/printer_friendly_posts.asp?TID=26606&SID=c8d8ecb4dbe92a1138f4zbezd437fz9f)  
12. Tiêu chuẩn ISO 12006 \- BIM 5D GXD, truy cập vào tháng 2 2, 2026, [https://bim.gxd.vn/tieu-chuan/iso-12006.html](https://bim.gxd.vn/tieu-chuan/iso-12006.html)  
13. Task: File Naming Convention \- BIM Level 2 Guidance, truy cập vào tháng 2 2, 2026, [https://bimarchive.scottishfuturestrust.org.uk/level2/stage/1/task/47/file-naming-convention](https://bimarchive.scottishfuturestrust.org.uk/level2/stage/1/task/47/file-naming-convention)  
14. TCVN X12006-2 : 202x ISO 12006-2 \- BIM 5D GXD, truy cập vào tháng 2 2, 2026, [https://bim.gxd.vn/tieu-chuan/tcvn-iso-12006-2.html](https://bim.gxd.vn/tieu-chuan/tcvn-iso-12006-2.html)  
15. File Naming Convention Best Practices in Construction Projects \- Onsite, truy cập vào tháng 2 2, 2026, [https://onsite.us/file-naming-convention-best-practices-in-construction-projects/](https://onsite.us/file-naming-convention-best-practices-in-construction-projects/)  
16. ISO 12006-2-Phan 2 khung phan loai.docx \- Bộ Xây dựng, truy cập vào tháng 2 2, 2026, [https://moc.gov.vn/Images/editor/files/Duthao/2023/ISO%2012006-2-Phan%202%20khung%20phan%20loai.docx](https://moc.gov.vn/Images/editor/files/Duthao/2023/ISO%2012006-2-Phan%202%20khung%20phan%20loai.docx)  
17. TIÊU CHUẨN QUỐC GIA TCVN XXXXX-2 : 202x ISO 12006-2 \- Bộ Xây dựng, truy cập vào tháng 2 2, 2026, [https://moc.gov.vn/Images/editor/files/Duthao/2023/3\_%20D%E1%BB%B1%20th%E1%BA%A3o%20TCVN%20XXXXX-2\_202X%20(ISO%2012006-2).pdf](https://moc.gov.vn/Images/editor/files/Duthao/2023/3_%20D%E1%BB%B1%20th%E1%BA%A3o%20TCVN%20XXXXX-2_202X%20\(ISO%2012006-2\).pdf)  
18. BÁO CÁO KẾT QUẢ THỰC HIỆN ĐỀ TÀI \- Viện Kinh tế Xây dựng, truy cập vào tháng 2 2, 2026, [https://kinhtexaydung.gov.vn/wp-content/uploads/2024/09/CLS-BC-Bao-cao-thuc-hien-de-tai.pdf](https://kinhtexaydung.gov.vn/wp-content/uploads/2024/09/CLS-BC-Bao-cao-thuc-hien-de-tai.pdf)  
19. Lập dự toán trên nền tảng BIM cho các công trình thủy lợi tại Việt Nam, truy cập vào tháng 2 2, 2026, [https://vawr.org.vn/lap-du-toan-tren-nen-tang-bim-cho-cac-cong-trinh-thuy-loi-tai-viet-nam](https://vawr.org.vn/lap-du-toan-tren-nen-tang-bim-cho-cac-cong-trinh-thuy-loi-tai-viet-nam)  
20. (PDF) Developing BIM Objects Libraries for Provision of BIM Services: An Action Research \- ResearchGate, truy cập vào tháng 2 2, 2026, [https://www.researchgate.net/publication/387705157\_Developing\_BIM\_Objects\_Libraries\_for\_Provision\_of\_BIM\_Services\_An\_Action\_Research](https://www.researchgate.net/publication/387705157_Developing_BIM_Objects_Libraries_for_Provision_of_BIM_Services_An_Action_Research)  
21. (PDF) Application of Building Information Modeling (BIM) for automatic integration of construction costs management information into 3D models in consideration of Vietnamese regulations \- ResearchGate, truy cập vào tháng 2 2, 2026, [https://www.researchgate.net/publication/342848614\_Application\_of\_Building\_Information\_Modeling\_BIM\_for\_automatic\_integration\_of\_construction\_costs\_management\_information\_into\_3D\_models\_in\_consideration\_of\_Vietnamese\_regulations](https://www.researchgate.net/publication/342848614_Application_of_Building_Information_Modeling_BIM_for_automatic_integration_of_construction_costs_management_information_into_3D_models_in_consideration_of_Vietnamese_regulations)  
22. Implementation of Building Information Model (BIM) in terms of quantity takeoff (QTO) and estimation at construction consultant \- Theseus, truy cập vào tháng 2 2, 2026, [https://www.theseus.fi/bitstream/handle/10024/153497/Master%20thesis%20-%20Ngo.pdf?sequence=1\&isAllowed=y](https://www.theseus.fi/bitstream/handle/10024/153497/Master%20thesis%20-%20Ngo.pdf?sequence=1&isAllowed=y)  
23. 06d Revit for Quantity Surveyors (Keynotes and Assembly Codes) \- YouTube, truy cập vào tháng 2 2, 2026, [https://www.youtube.com/watch?v=ukzC4vKG0Pg](https://www.youtube.com/watch?v=ukzC4vKG0Pg)  
24. Mã hiệu đơn giá công việc có chữ a hoặc dấu \+ nhưng chi phí vật liệu lại bằng 0, truy cập vào tháng 2 2, 2026, [https://quyettoan.vn/dutoan/Ma-hieu-don-gia-cong-viec-co-chu-a-hoac-dau-nhung-chi-phi-vat-lieu-lai-bang-0-vn-4-364-6.aspx](https://quyettoan.vn/dutoan/Ma-hieu-don-gia-cong-viec-co-chu-a-hoac-dau-nhung-chi-phi-vat-lieu-lai-bang-0-vn-4-364-6.aspx)  
25. Hướng dẫn nhập Mã hiệu và tên công việc trên Dự toán Eta, truy cập vào tháng 2 2, 2026, [https://dutoaneta.vn/huong-dan-nhap-ma-hieu-va-ten-cong-viec-tren-du-toan-eta/](https://dutoaneta.vn/huong-dan-nhap-ma-hieu-va-ten-cong-viec-tren-du-toan-eta/)  
26. Làm công tác tạm tính và đổi tên vật tư cực nhanh khi lập dự toán cơ điện MEP, truy cập vào tháng 2 2, 2026, [https://dutoanduthau.com/lam-cong-tac-tam-tinh-va-doi-ten-vat-tu-cuc-nhanh-khi-lap-du-toan-co-dien-mep.html](https://dutoanduthau.com/lam-cong-tac-tam-tinh-va-doi-ten-vat-tu-cuc-nhanh-khi-lap-du-toan-co-dien-mep.html)  
27. Solved: Shared parameters naming convention \- Forums, Autodesk, truy cập vào tháng 2 2, 2026, [https://forums.autodesk.com/t5/revit-architecture-forum/shared-parameters-naming-convention/td-p/10912546](https://forums.autodesk.com/t5/revit-architecture-forum/shared-parameters-naming-convention/td-p/10912546)  
28. Keynotes in Revit Tutorial | Advanced Revit Course 08 \- YouTube, truy cập vào tháng 2 2, 2026, [https://www.youtube.com/watch?v=\_md-rOUHgiI](https://www.youtube.com/watch?v=_md-rOUHgiI)  
29. Quy ước đặt tên các gói thông tin theo ISO 19650, truy cập vào tháng 2 2, 2026, [https://tapchixaydung.vn/quy-uoc-dat-ten-cac-goi-thong-tin-theo-iso-19650-20201224000022635.html](https://tapchixaydung.vn/quy-uoc-dat-ten-cac-goi-thong-tin-theo-iso-19650-20201224000022635.html)  
30. Phần 3: Tiêu chuẩn, hướng dẫn và triển khai BIM cho dự án \- BIM 5D GXD, truy cập vào tháng 2 2, 2026, [https://bim.gxd.vn/tai-lieu/phan-3-tieu-chuan-trien-khai.html](https://bim.gxd.vn/tai-lieu/phan-3-tieu-chuan-trien-khai.html)  
31. Áp dụng quy tắc đặt tên theo tiêu chuẩn BIM ISO 19650 trên ADSCIVIL CDE, truy cập vào tháng 2 2, 2026, [https://adscivil.vn/v2/blog-detail?id=ap-dung-quy-tac-dat-ten-theo-tieu-chuan-bim-iso-19650-tren-adscivil-cde](https://adscivil.vn/v2/blog-detail?id=ap-dung-quy-tac-dat-ten-theo-tieu-chuan-bim-iso-19650-tren-adscivil-cde)  
32. ANALYSIS OF 5D BIM FOR COST ESTIMATION, COST CONTROL, AND PAYMENTS \- Journal of Information Technology in Construction, truy cập vào tháng 2 2, 2026, [https://itcon.org/papers/2024\_24-ITcon-Pishdad.pdf](https://itcon.org/papers/2024_24-ITcon-Pishdad.pdf)  
33. Sửa đổi, bổ sung một số định mức xây dựng ban hành tại Thông tư số 12/2021/TT-BXD ngày 31/8/2021 của Bộ trưởng Bộ Xây dựng, truy cập vào tháng 2 2, 2026, [https://moc.gov.vn/vn/tin-tuc/1176/85737/sua-doi--bo-sung-mot-so-dinh-muc-xay-dung-ban-hanh-tai-thong-tu-so-122021tt-bxd-ngay-3182021-cua-bo-truong-bo-xay-dung.aspx](https://moc.gov.vn/vn/tin-tuc/1176/85737/sua-doi--bo-sung-mot-so-dinh-muc-xay-dung-ban-hanh-tai-thong-tu-so-122021tt-bxd-ngay-3182021-cua-bo-truong-bo-xay-dung.aspx)