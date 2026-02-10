"""
Priority-based Object Dictionary.
Higher priority wins when multiple keywords match.

This implements the 3-Layer Priority Model to solve the "Identity Theft" problem
where flat keyword matching incorrectly identifies objects.

Example:
    "Ván khuôn móng bê tông M200" was incorrectly matched as "Bê tông"
    With priority matching, "Ván khuôn" (Priority 1) wins over "Bê tông" (Priority 3)
"""

from typing import Tuple, Optional, List
from functools import lru_cache
from .text_normalizer import normalize_vietnamese, build_normalized_dict, _is_word_boundary_match

try:
    from rapidfuzz import fuzz as _fuzz
    from rapidfuzz import process as _rfprocess
except ImportError:
    _fuzz = None
    _rfprocess = None

# --- Hardcoded fallback dictionaries (used when JSON is unavailable) ---

# Priority 1: Biện pháp/Hoạt động (Methods/Activities)
# Rule: Nếu match → DỪNG QUÉT NGAY, đây là Object chính
_HARDCODED_P1 = {
    # Ván khuôn - QUAN TRỌNG: không để "bê tông" thắng
    'ván khuôn': 'Ván khuôn',
    'van khuon': 'Ván khuôn',
    'cốp pha': 'Ván khuôn',
    'cop pha': 'Ván khuôn',

    # Vận chuyển
    'vận chuyển': 'Vận chuyển',
    'van chuyen': 'Vận chuyển',
    'vân chuyển': 'Vận chuyển',  # Typo variant

    # Công tác đất - Đào
    'đào phá dỡ': 'Đào phá dỡ',
    'dao pha do': 'Đào phá dỡ',
    'đào khuôn đường': 'Đào khuôn đường',
    'dao khuon duong': 'Đào khuôn đường',
    'đào đất': 'Đào đất',
    'dao dat': 'Đào đất',
    'đào': 'Đào',
    'dao': 'Đào',

    # Công tác đất - Đắp
    'đắp đất nền': 'Đắp đất nền',
    'dap dat nen': 'Đắp đất nền',
    'đắp đất đầm chặt': 'Đắp đất nền',
    'dap dat dam chat': 'Đắp đất nền',
    'đầm chặt k': 'Đắp đất nền',
    'dam chat k': 'Đắp đất nền',
    'đắp đất hoàn trả': 'Đắp đất hoàn trả',
    'dap dat hoan tra': 'Đắp đất hoàn trả',
    'đắp đất': 'Đắp đất',
    'dap dat': 'Đắp đất',
    'đắp': 'Đắp',
    'dap': 'Đắp',
    'san nền': 'San nền',
    'san nen': 'San nền',
    'lu lèn': 'Lu lèn',
    'lu len': 'Lu lèn',
    'đầm nén': 'Đầm nén',
    'dam nen': 'Đầm nén',

    # Công tác nhựa đường
    'tưới lớp thấm bám': 'Tưới nhựa',
    'tuoi lop tham bam': 'Tưới nhựa',
    'tưới nhựa': 'Tưới nhựa',
    'tuoi nhua': 'Tưới nhựa',
    'rải nhựa': 'Rải nhựa',
    'rai nhua': 'Rải nhựa',
    'thấm nhập': 'Tưới thấm nhập',
    'tham nhap': 'Tưới thấm nhập',
    'rải thảm mặt đường': 'Mặt đường',
    'rai tham mat duong': 'Mặt đường',
    'rải thảm': 'Rải thảm',
    'rai tham': 'Rải thảm',

    # Công tác hoàn thiện
    'trát thành': 'Trát',
    'trat thanh': 'Trát',
    'trát': 'Trát',
    'trat': 'Trát',
    'láng đáy': 'Láng',
    'lang day': 'Láng',
    'láng': 'Láng',
    'lang': 'Láng',
    'chèn vữa': 'Chèn vữa',
    'chen vua': 'Chèn vữa',
    'tấm bê tông lát mái': 'Tấm lát mái',
    'tam be tong lat mai': 'Tấm lát mái',
    'tấm lát mái': 'Tấm lát mái',
    'tam lat mai': 'Tấm lát mái',
    'lát': 'Lát',
    'lat': 'Lát',
    'ốp': 'Ốp',
    'op': 'Ốp',
    'quét': 'Quét',
    'quet': 'Quét',

    # Xây - specific patterns first
    'xây bể cáp': 'Xây bể cáp',
    'xay be cap': 'Xây bể cáp',
    'xây hố ga': 'Xây gạch',
    'xay ho ga': 'Xây gạch',
    'xây tường chắn': 'Xây tường',
    'xay tuong chan': 'Xây tường',
    'xây tường': 'Xây tường',
    'xay tuong': 'Xây tường',
    'xây đá hộc': 'Xây đá',
    'xay da hoc': 'Xây đá',
    'xây đá': 'Xây đá',
    'xay da': 'Xây đá',
    'xây gạch': 'Xây gạch',
    'xay gach': 'Xây gạch',
    'xây': 'Xây',
    'xay': 'Xây',

    # Trồng cây
    'đất màu trồng cỏ': 'Đất màu',
    'dat mau trong co': 'Đất màu',
    'đất màu': 'Đất màu',
    'dat mau': 'Đất màu',
    'trồng cỏ': 'Trồng cỏ',
    'trong co': 'Trồng cỏ',
}

# Priority 2: Cấu kiện đặc thù (Specific Components)
# Rule: Nếu match → Object = Cấu kiện, KHÔNG phải vật liệu
_HARDCODED_P2 = {
    # Cấu kiện đường - specific patterns first
    'bó vỉa đá': 'Bó vỉa',
    'bo via da': 'Bó vỉa',
    'bó vỉa': 'Bó vỉa',
    'bo via': 'Bó vỉa',
    'tấm đan rãnh': 'Tấm đan rãnh',
    'tam dan ranh': 'Tấm đan rãnh',
    'tấm đan': 'Tấm đan',
    'tam dan': 'Tấm đan',
    'rãnh thoát nước': 'Rãnh thoát nước',
    'ranh thoat nuoc': 'Rãnh thoát nước',
    'rãnh thoát': 'Rãnh thoát nước',
    'ranh thoat': 'Rãnh thoát nước',

    # Móng đường - must match before "móng"
    'móng cấp phối đá dăm': 'Móng đường',
    'mong cap phoi da dam': 'Móng đường',
    'móng cấp phối': 'Móng đường',
    'mong cap phoi': 'Móng đường',
    'thi công móng': 'Móng đường',
    'thi cong mong': 'Móng đường',

    # Cấu kiện thoát nước - specific first
    # IMPORTANT: "Nắp hố ga" must be before "Hố ga" to prevent wrong matching
    'nắp hố ga': 'Nắp hố ga',
    'nap ho ga': 'Nắp hố ga',
    'nắp ga': 'Nắp hố ga',  # Variant without "hố"
    'nap ga': 'Nắp hố ga',
    # "Bê tông đáy/thành/nắp hố ga" should be Bê tông, not Hố ga
    'bê tông đáy hố ga': 'Bê tông',
    'be tong day ho ga': 'Bê tông',
    'bê tông thành hố ga': 'Bê tông',
    'be tong thanh ho ga': 'Bê tông',
    'bê tông nắp hố ga': 'Bê tông',
    'be tong nap ho ga': 'Bê tông',
    'hố ga': 'Hố ga',
    'ho ga': 'Hố ga',
    'cống hộp đôi': 'Cống hộp',
    'cong hop doi': 'Cống hộp',
    'cống hộp': 'Cống hộp',
    'cong hop': 'Cống hộp',
    'cống tròn': 'Cống tròn',
    'cong tron': 'Cống tròn',
    'cống': 'Cống thoát nước',
    'cong': 'Cống thoát nước',
    'hố thu': 'Hố thu',
    'ho thu': 'Hố thu',
    'giếng thăm': 'Giếng thăm',
    'gieng tham': 'Giếng thăm',
    'nắp hố ga': 'Nắp hố ga',
    'nap ho ga': 'Nắp hố ga',
    'song chắn rác': 'Song chắn rác',
    'song chan rac': 'Song chắn rác',
    'cửa xả': 'Cửa xả',
    'cua xa': 'Cửa xả',

    # Bê tông special - specific positions (MUST be before ván khuôn)
    'bê tông mặt đường': 'Bê tông mặt đường',
    'be tong mat duong': 'Bê tông mặt đường',
    'bê tông vỉa hè': 'Bê tông vỉa hè',
    'be tong via he': 'Bê tông vỉa hè',
    'bê tông tấm đan': 'Bê tông',
    'be tong tam dan': 'Bê tông',
    'bê tông lót móng bó vỉa': 'Bê tông lót',
    'be tong lot mong bo via': 'Bê tông lót',
    'bê tông lót móng': 'Bê tông lót',
    'be tong lot mong': 'Bê tông lót',
    'bê tông lót': 'Bê tông lót',
    'be tong lot': 'Bê tông lót',

    # Cấu kiện lát
    'gạch lát': 'Gạch lát',
    'gach lat': 'Gạch lát',
    'gạch ốp': 'Gạch ốp',
    'gach op': 'Gạch ốp',
    'gạch men': 'Gạch men',
    'gach men': 'Gạch men',
    'gạch ceramic': 'Gạch Ceramic',
    'gach ceramic': 'Gạch Ceramic',
    'gạch granite': 'Gạch Granite',
    'gach granite': 'Gạch Granite',

    # Cấu kiện giao thông
    'biển chỉ hướng': 'Biển báo',
    'bien chi huong': 'Biển báo',
    'biển báo tam giác': 'Biển báo',
    'bien bao tam giac': 'Biển báo',
    'biển báo': 'Biển báo',
    'bien bao': 'Biển báo',
    'lan can': 'Lan can',
    'cột đèn trang trí': 'Cột đèn trang trí',
    'cot den trang tri': 'Cột đèn trang trí',
    'cột đèn bát giác': 'Cột đèn',
    'cot den bat giac': 'Cột đèn',
    'cột đèn': 'Cột đèn',
    'cot den': 'Cột đèn',
    'dải phân cách': 'Dải phân cách',
    'dai phan cach': 'Dải phân cách',
    'hộ lan tôn sóng': 'Hộ lan tôn sóng',
    'ho lan ton song': 'Hộ lan tôn sóng',
    'hộ lan': 'Hộ lan',
    'ho lan': 'Hộ lan',
    'tôn sóng': 'Hộ lan tôn sóng',
    'ton song': 'Hộ lan tôn sóng',
    'vạch sơn': 'Vạch sơn',
    'vach son': 'Vạch sơn',
    'đinh phản quang': 'Đinh phản quang',
    'dinh phan quang': 'Đinh phản quang',

    # Thiết bị điện - MCCB/MCB/RCCB (Must be higher priority than generic keywords)
    'mccb': 'MCCB',
    'mcb': 'MCB',
    'rccb': 'RCCB',
    'rcbo': 'RCBO',
    'rcd': 'RCD',
    'acb': 'ACB',
    'contactor': 'Contactor',
    'aptomat': 'Aptomat',

    # Công tắc (MUST be before "cống" to prevent "Công tắc" → "Cống thoát nước")
    'công tắc mực nước': 'Công tắc',
    'cong tac muc nuoc': 'Công tắc',
    'công tắc hẹn giờ': 'Công tắc hẹn giờ',
    'cong tac hen gio': 'Công tắc hẹn giờ',
    'công tắt hẹn giờ': 'Công tắc hẹn giờ',
    'cong tat hen gio': 'Công tắc hẹn giờ',
    'công tắc nhiệt độ': 'Công tắc nhiệt độ',
    'cong tac nhiet do': 'Công tắc nhiệt độ',
    'công tắt nhiệt độ': 'Công tắc nhiệt độ',
    'cong tat nhiet do': 'Công tắc nhiệt độ',
    'công tắc chọn': 'Công tắc chọn',
    'cong tac chon': 'Công tắc chọn',
    'công tắt chọn': 'Công tắc chọn',
    'cong tat chon': 'Công tắc chọn',
    'công tắt': 'Công tắc',
    'cong tat': 'Công tắc',
    'công tắc': 'Công tắc',
    'cong tac': 'Công tắc',

    # Công tơ điện
    'công tơ': 'Công tơ điện',
    'cong to': 'Công tơ điện',

    # Cầu chì
    'cầu chì': 'Cầu chì',
    'cau chi': 'Cầu chì',

    # Chống sét (MUST be before "cống" to prevent false match)
    'chống sét lan truyền': 'Chống sét lan truyền',
    'chong set lan truyen': 'Chống sét lan truyền',
    'chống sét': 'Chống sét',
    'chong set': 'Chống sét',

    # Bồn dầu (MUST be before P1 "quét" to prevent false match on "quét nhựa đường")
    'bồn dầu': 'Bồn dầu',
    'bon dau': 'Bồn dầu',

    # Ống cấp/hồi dầu (MUST be before "inox304" to prevent Inox winning)
    'ống cấp dầu inox': 'Ống Inox',
    'ong cap dau inox': 'Ống Inox',
    'ống hồi dầu inox': 'Ống Inox',
    'ong hoi dau inox': 'Ống Inox',
    'ống cấp dầu': 'Ống Inox',
    'ong cap dau': 'Ống Inox',
    'ống hồi dầu': 'Ống Inox',
    'ong hoi dau': 'Ống Inox',

    # Họng tiếp dầu
    'họng tiếp dầu': 'Họng tiếp dầu',
    'hong tiep dau': 'Họng tiếp dầu',

    # Máy biến áp / Máy phát điện / Thiết bị lớn MEP
    'máy biến áp': 'Máy biến áp',
    'may bien ap': 'Máy biến áp',
    'máy phát điện': 'Máy phát điện',
    'may phat dien': 'Máy phát điện',
    'máy điều hòa': 'Máy điều hòa',
    'may dieu hoa': 'Máy điều hòa',
    'máy điều hoà': 'Máy điều hòa',
    'may dieu hoa': 'Máy điều hòa',
    'điều hòa không khí': 'Máy điều hòa',
    'dieu hoa khong khi': 'Máy điều hòa',
    'điều hoà không khí': 'Máy điều hòa',

    # ATS / DOL / Bộ khởi động mềm
    'bộ điều khiển ats': 'Tủ điều khiển ATS',
    'bo dieu khien ats': 'Tủ điều khiển ATS',
    'bộ điều khiển': 'Tủ điều khiển',
    'bo dieu khien': 'Tủ điều khiển',
    'ats': 'ATS',

    # Quạt các loại
    'quạt hướng trục': 'Quạt hướng trục',
    'quat huong truc': 'Quạt hướng trục',
    'quạt gắn tường': 'Quạt gắn tường',
    'quat gan tuong': 'Quạt gắn tường',
    'quạt gió thải': 'Quạt gió thải',
    'quat gio thai': 'Quạt gió thải',
    'quạt thông gió': 'Quạt thông gió',
    'quat thong gio': 'Quạt thông gió',
    'quạt hút': 'Quạt hút',
    'quat hut': 'Quạt hút',
    'quạt': 'Quạt',
    'quat': 'Quạt',

    # Camera
    'camera dome': 'Camera',
    'camera thân': 'Camera',
    'camera than': 'Camera',
    'camera trong thang máy': 'Camera',
    'camera': 'Camera',

    # Switch mạng / Thiết bị mạng
    'core switch': 'Switch mạng',
    'switch poe': 'Switch mạng',
    'switch 24 ports': 'Switch mạng',
    'switch 16 ports': 'Switch mạng',
    'switch 12 ports': 'Switch mạng',
    'switch mạng': 'Switch mạng',
    'switch mang': 'Switch mạng',
    'switch': 'Switch mạng',

    # Đầu ghi hình
    'đầu ghi hình': 'Đầu ghi hình',
    'dau ghi hinh': 'Đầu ghi hình',

    # Loa
    'loa hộp chống nước': 'Loa',
    'loa hop chong nuoc': 'Loa',
    'loa âm trần': 'Loa',
    'loa am tran': 'Loa',
    'loa hộp': 'Loa',
    'loa hop': 'Loa',
    'loa': 'Loa',

    # Thiết bị PA (Public Address)
    'bàn gọi chọn vùng': 'Bàn gọi PA',
    'ban goi chon vung': 'Bàn gọi PA',
    'bàn gọi': 'Bàn gọi PA',
    'ban goi': 'Bàn gọi PA',

    # UPS
    'bộ lưu điện ups': 'UPS',
    'bo luu dien ups': 'UPS',
    'bộ lưu điện ubs': 'UPS',
    'bo luu dien ubs': 'UPS',
    'bộ lưu điện': 'UPS',
    'bo luu dien': 'UPS',
    'ups': 'UPS',

    # Tủ rack
    'tủ rack': 'Tủ rack',
    'tu rack': 'Tủ rack',

    # Đồng hồ (MUST be before generic patterns)
    'đồng hồ đa năng': 'Đồng hồ đa năng',
    'dong ho da nang': 'Đồng hồ đa năng',
    'đồng hồ kwh': 'Đồng hồ điện',
    'dong ho kwh': 'Đồng hồ điện',
    'đồng hồ đo dòng điện': 'Đồng hồ đo dòng',
    'dong ho do dong dien': 'Đồng hồ đo dòng',
    'đồng hồ đo điện áp': 'Đồng hồ đo áp',
    'dong ho do dien ap': 'Đồng hồ đo áp',

    # Hộp đấu nối / Hộp nối cáp
    'hộp đấu nối quang': 'Hộp đấu nối quang',
    'hop dau noi quang': 'Hộp đấu nối quang',
    'hộp đấu nối': 'Hộp đấu nối',
    'hop dau noi': 'Hộp đấu nối',
    'hộp nối cáp': 'Hộp nối cáp',
    'hop noi cap': 'Hộp nối cáp',

    # Máng cáp
    'máng cáp': 'Máng cáp',
    'mang cap': 'Máng cáp',
    'hộp cáp': 'Máng cáp',
    'hop cap': 'Máng cáp',

    # Biến dòng CT (MCT = Measurement CT, PCT = Protection CT)
    'mct': 'Biến dòng (CT)',
    'pct': 'Biến dòng (CT)',

    # Phụ kiện tủ điện / ACB / MCCB
    'phụ kiện acb': 'Phụ kiện ACB',
    'phu kien acb': 'Phụ kiện ACB',
    'phụ kiện mccb': 'Phụ kiện MCCB',
    'phu kien mccb': 'Phụ kiện MCCB',
    'motor mechanism': 'Phụ kiện ACB',

    # Timer relay
    'time loại trễ': 'Rơ le thời gian',
    'time loai tre': 'Rơ le thời gian',
    'timer': 'Rơ le thời gian',

    # Rơ le (with and without space — "Rơle" normalizes to "role", "Rơ le" to "ro le")
    'rơ le': 'Rơ le',
    'ro le': 'Rơ le',
    'relay': 'Rơ le',
    'rơle': 'Rơ le',
    'role': 'Rơ le',

    # HVAC Ductwork components
    'miệng gió hút thải': 'Miệng gió',
    'mieng gio hut thai': 'Miệng gió',
    'miệng gió': 'Miệng gió',
    'mieng gio': 'Miệng gió',
    'fire damper': 'Fire Damper',
    'mfd': 'Fire Damper',
    'manual fire damper': 'Fire Damper',
    'chuyển vuông tròn': 'Chuyển vuông tròn',
    'chuyen vuong tron': 'Chuyển vuông tròn',
    'gót giày ống gió': 'Gót giày ống gió',
    'got giay ong gio': 'Gót giày ống gió',
    'gót giày': 'Gót giày ống gió',
    'got giay': 'Gót giày ống gió',
    'co ống gió': 'Co ống gió',
    'co ong gio': 'Co ống gió',
    'giảm ống gió': 'Giảm ống gió',
    'giam ong gio': 'Giảm ống gió',
    'ống gió mềm': 'Ống gió',
    'ong gio mem': 'Ống gió',
    'ống gió tôn': 'Ống gió',
    'ong gio ton': 'Ống gió',
    'ống gió': 'Ống gió',
    'ong gio': 'Ống gió',

    # Ống GI / Ống Inox / Ống đồng (MUST be before generic "Ống")
    'ống đồng': 'Ống đồng',
    'ong dong': 'Ống đồng',
    'ống gas': 'Ống đồng',
    'ong gas': 'Ống đồng',
    'ống gas lạnh': 'Ống đồng',
    'ong gas lanh': 'Ống đồng',
    'ống gi': 'Ống GI',
    'ong gi': 'Ống GI',
    'ống inox': 'Ống Inox',
    'ong inox': 'Ống Inox',
    'inox304': 'Inox',
    'inox 304': 'Inox',

    # Tủ điện MEP
    'tủ gom công tơ': 'Tủ gom công tơ',
    'tu gom cong to': 'Tủ gom công tơ',
    'tủ điện tổng': 'Tủ điện tổng (MSB)',
    'tu dien tong': 'Tủ điện tổng (MSB)',
    'tủ điện phân phối': 'Tủ điện phân phối (DB)',
    'tu dien phan phoi': 'Tủ điện phân phối (DB)',
    'tủ 10 module': 'Tủ điện',
    'tu 10 module': 'Tủ điện',
    'tủ module': 'Tủ điện',
    'tu module': 'Tủ điện',
    'tủ điện': 'Tủ điện',
    'tu dien': 'Tủ điện',

    # Van các loại - specific first
    'van khóa tay gạt': 'Van khóa tay gạt',
    'van khoa tay gat': 'Van khóa tay gạt',
    'van cổng nối bích': 'Van cổng',
    'van cong noi bich': 'Van cổng',
    'van cổng ren đồng': 'Van cổng',
    'van cong ren dong': 'Van cổng',
    'van cổng bb': 'Van cổng',
    'van cong bb': 'Van cổng',
    'van cổng': 'Van cổng',
    'van cong': 'Van cổng',
    'van bướm kèm công tắc': 'Van bướm',
    'van buom kem cong tac': 'Van bướm',
    'van bướm': 'Van bướm',
    'van buom': 'Van bướm',
    'van 1 chiều nối bích': 'Van 1 chiều',
    'van 1 chieu noi bich': 'Van 1 chiều',
    'van một chiều nối bích': 'Van 1 chiều',
    'van mot chieu noi bich': 'Van 1 chiều',
    'van 1 chiều': 'Van 1 chiều',
    'van một chiều': 'Van 1 chiều',
    'cụm van quản lý': 'Cụm van quản lý',
    'cum van quan ly': 'Cụm van quản lý',
    'cụm van xả khí': 'Cụm van xả khí',
    'cum van xa khi': 'Cụm van xả khí',
    'alarm valve': 'Van báo động (Alarm Valve)',
    'van phao': 'Van phao',
    'van xả': 'Van xả',
    'van xa': 'Van xả',
    'van giảm áp': 'Van giảm áp',
    'van giam ap': 'Van giảm áp',
    # Van bi patterns - "rắc co đôi" variant must be checked before plain "van bi"
    'van bi tay gạt rắc co đôi': 'Van bi rắc co đôi',
    'van bi tay gat rac co doi': 'Van bi rắc co đôi',
    'van bi rắc co đôi': 'Van bi rắc co đôi',
    'van bi rac co doi': 'Van bi rắc co đôi',
    'van bi rắc co': 'Van bi rắc co đôi',
    'van bi rac co': 'Van bi rắc co đôi',
    'van bi': 'Van bi',
    'van góc cho chậu rửa chén': 'Van góc',
    'van goc cho chau rua chen': 'Van góc',
    'van góc cho chậu rửa': 'Van góc',
    'van goc cho chau rua': 'Van góc',
    'van góc cho lavabo': 'Van góc',
    'van goc cho lavabo': 'Van góc',
    'van góc cho': 'Van góc',
    'van goc cho': 'Van góc',
    'van góc': 'Van góc',
    'van goc': 'Van góc',
    'van': 'Van',

    # Thiết bị vệ sinh
    'chậu rửa chén inox': 'Chậu rửa',
    'chau rua chen inox': 'Chậu rửa',
    'chậu rửa chén': 'Chậu rửa',
    'chau rua chen': 'Chậu rửa',
    'chậu rửa inox': 'Chậu rửa',
    'chau rua inox': 'Chậu rửa',
    'chậu rửa': 'Chậu rửa',
    'chau rua': 'Chậu rửa',
    'lavabo': 'Chậu rửa',

    # Bơm các loại - specific first
    'bơm chữa cháy': 'Bơm chữa cháy',
    'bom chua chay': 'Bơm chữa cháy',
    'bơm cứu hỏa': 'Bơm chữa cháy',
    'bom cuu hoa': 'Bơm chữa cháy',
    'bơm bù áp': 'Bơm bù áp',
    'bom bu ap': 'Bơm bù áp',
    'bơm chìm thoát nước': 'Bơm chìm nước thải',
    'bom chim thoat nuoc': 'Bơm chìm nước thải',
    'bơm chìm': 'Bơm chìm nước thải',
    'bom chim': 'Bơm chìm nước thải',
    'bơm nước': 'Bơm nước',
    'bom nuoc': 'Bơm nước',
    'bơm': 'Bơm',
    'bom': 'Bơm',
    'bệ bơm': 'Bệ bơm',
    'be bom': 'Bệ bơm',

    # Bình/Thiết bị PCCC
    'bình tích áp': 'Bình tích áp',
    'binh tich ap': 'Bình tích áp',
    'bình cầu nổ chữa cháy': 'Bình chữa cháy',
    'binh cau no chua chay': 'Bình chữa cháy',
    'bình cầu nổ': 'Bình chữa cháy',
    'binh cau no': 'Bình chữa cháy',
    'bình chữa cháy': 'Bình chữa cháy',
    'binh chua chay': 'Bình chữa cháy',
    'hộp đựng bình chữa cháy': 'Hộp đựng bình chữa cháy',
    'hop dung binh chua chay': 'Hộp đựng bình chữa cháy',
    'lò xo giảm chấn': 'Lò xo giảm chấn',
    'lo xo giam chan': 'Lò xo giảm chấn',
    'sprinkler': 'Sprinkler',
    'đầu phun sprinkler': 'Đầu phun Sprinkler',
    'dau phun sprinkler': 'Đầu phun Sprinkler',
    'trụ cứu hỏa': 'Trụ cứu hỏa',
    'tru cuu hoa': 'Trụ cứu hỏa',
    'họng cứu hỏa': 'Họng cứu hỏa',

    # Phụ kiện ống nước - specific first (angle + type)
    'cút 90 độ': 'Cút 90 độ',
    'cut 90 do': 'Cút 90 độ',
    'cút 45 độ': 'Cút 45 độ',
    'cut 45 do': 'Cút 45 độ',
    'chếch 45 độ': 'Chếch 45 độ',
    'chech 45 do': 'Chếch 45 độ',
    'tê thu': 'Tê thu',
    'te thu': 'Tê thu',
    'tê đều': 'Tê đều',
    'te deu': 'Tê đều',
    'tê hàn': 'Tê hàn',
    'te han': 'Tê hàn',
    'tê': 'Tê',
    'te': 'Tê',
    'y thu': 'Y thu',
    'y đều': 'Y đều',
    'y deu': 'Y đều',
    'y lọc': 'Y lọc',
    'y loc': 'Y lọc',
    'côn thu': 'Côn thu',
    'con thu': 'Côn thu',
    'côn': 'Côn',
    'con': 'Côn',
    'cút': 'Cút',
    'cut': 'Cút',
    'chếch': 'Chếch',
    'chech': 'Chếch',
    'đai khởi thủy': 'Đai khởi thủy',
    'dai khoi thuy': 'Đai khởi thủy',
    'khớp nối mềm': 'Khớp nối mềm',
    'khop noi mem': 'Khớp nối mềm',
    'khớp mềm': 'Khớp nối mềm',
    'khop mem': 'Khớp nối mềm',
    'mối nối mềm': 'Mối nối mềm',
    'moi noi mem': 'Mối nối mềm',
    'khâu nối ren ngoài': 'Khâu nối ren ngoài',
    'khau noi ren ngoai': 'Khâu nối ren ngoài',
    'khâu nối': 'Khâu nối',
    'khau noi': 'Khâu nối',
    'rắc co ren ngoài': 'Rắc co ren ngoài',
    'rac co ren ngoai': 'Rắc co ren ngoài',
    'rắc co': 'Rắc co',
    'rac co': 'Rắc co',
    'bích hàn lồng': 'Mặt bích (Bích hàn)',
    'bich han long': 'Mặt bích (Bích hàn)',
    'bích rỗng': 'Bích rỗng',
    'bich rong': 'Bích rỗng',
    'bích đặc': 'Bích đặc',
    'bich dac': 'Bích đặc',
    'bích ttk': 'Bích TTK',
    'bich ttk': 'Bích TTK',
    'mặt bích': 'Mặt bích',
    'mat bich': 'Mặt bích',
    'bích thép': 'Bích thép',
    'bich thep': 'Bích thép',
    'nút bịt hàn': 'Đầu bịt/Nút bịt',
    'nut bit han': 'Đầu bịt/Nút bịt',
    'nút bịt đầu ống': 'Nút bịt',
    'nut bit dau ong': 'Nút bịt',
    'nút bịt': 'Nút bịt',
    'nut bit': 'Nút bịt',
    'đầu bịt ppr': 'Đầu bịt PPR',
    'dau bit ppr': 'Đầu bịt PPR',
    'đầu bịt': 'Đầu bịt',
    'dau bit': 'Đầu bịt',
    'nối bích': 'Nối bích',
    'noi bich': 'Nối bích',
    'đầu nối ren ngoài': 'Đầu nối ren ngoài',
    'dau noi ren ngoai': 'Đầu nối ren ngoài',
    'đầu nối ren': 'Đầu nối ren',
    'dau noi ren': 'Đầu nối ren',
    'đầu nối': 'Đầu nối',
    'dau noi': 'Đầu nối',
    'măng sông ren trong': 'Măng sông ren trong',
    'mang song ren trong': 'Măng sông ren trong',
    'măng sông ren ngoài': 'Măng sông ren ngoài',
    'mang song ren ngoai': 'Măng sông ren ngoài',
    'măng sông nối ống': 'Măng sông nối ống',
    'mang song noi ong': 'Măng sông nối ống',
    'măng xông': 'Măng sông',
    'mang xong': 'Măng sông',
    'măng sông': 'Măng sông',
    'mang song': 'Măng sông',
    'nút loe': 'Nút loe',
    'nut loe': 'Nút loe',
    'kép ren': 'Kép ren',
    'kep ren': 'Kép ren',
    'rọ hút': 'Rọ hút',
    'ro hut': 'Rọ hút',
    'hộp van': 'Hộp van',
    'hop van': 'Hộp van',
    'gối đỡ ống': 'Gối đỡ ống',
    'goi do ong': 'Gối đỡ ống',

    # Đồng hồ đo (specific types first)
    'đồng hồ ampe': 'Đồng hồ Ampe',
    'dong ho ampe': 'Đồng hồ Ampe',
    'đồng hồ đo nước': 'Đồng hồ nước',
    'dong ho do nuoc': 'Đồng hồ nước',
    'hộp đồng hồ': 'Hộp đồng hồ',
    'hop dong ho': 'Hộp đồng hồ',
    'đồng hồ nước': 'Đồng hồ nước',
    'dong ho nuoc': 'Đồng hồ nước',
    'đồng hồ đo dòng': 'Đồng hồ đo dòng',
    'dong ho do dong': 'Đồng hồ đo dòng',
    'đồng hồ đo điện': 'Đồng hồ đo áp',
    'dong ho do dien': 'Đồng hồ đo áp',
    'đồng hồ đa năng': 'Đồng hồ đa năng',
    'dong ho da nang': 'Đồng hồ đa năng',
    'đồng hồ kwh': 'Đồng hồ điện',
    'dong ho kwh': 'Đồng hồ điện',
    'đồng hồ đo': 'Đồng hồ',
    'dong ho do': 'Đồng hồ',
    'đồng hồ': 'Đồng hồ',
    'dong ho': 'Đồng hồ',

    # Đèn các loại
    'đèn tín hiệu': 'Đèn tín hiệu',
    'den tin hieu': 'Đèn tín hiệu',
    'đèn báo pha': 'Đèn báo pha',
    'den bao pha': 'Đèn báo pha',
    'đèn chiếu sáng': 'Đèn chiếu sáng',
    'den chieu sang': 'Đèn chiếu sáng',
    'bộ đèn cầu': 'Đèn chiếu sáng',
    'bo den cau': 'Đèn chiếu sáng',
    'đèn led': 'Đèn LED',
    'den led': 'Đèn LED',
    'đèn đui xoáy': 'Đèn đui xoáy',
    'đèn': 'Đèn',
    'den': 'Đèn',

    # Tiếp địa
    'cọc tiếp địa': 'Cọc tiếp địa',
    'coc tiep dia': 'Cọc tiếp địa',
    'kim thu sét': 'Kim thu sét',
    'kim thu set': 'Kim thu sét',

    # Cọc các loại
    'cọc khoan nhồi': 'Cọc khoan nhồi',
    'coc khoan nhoi': 'Cọc khoan nhồi',
    'cọc bê tông': 'Cọc bê tông',
    'coc be tong': 'Cọc bê tông',
    'cọc ép': 'Cọc ép',
    'coc ep': 'Cọc ép',
    'đóng cọc tre': 'Cọc tre',
    'dong coc tre': 'Cọc tre',
    'cọc tre gia cố': 'Cọc tre',
    'coc tre gia co': 'Cọc tre',
    'thi cọc tre': 'Cọc tre',
    'cọc tre': 'Cọc tre',
    'coc tre': 'Cọc tre',

    # Nắp gang
    'nắp gang': 'Nắp gang',
    'nap gang': 'Nắp gang',

    # Khung bulong
    'khung bulong móng': 'Khung móng',
    'khung mong cot bulong': 'Khung móng',
    'khung móng cột': 'Khung móng',
    'khung bulong': 'Khung bulong móng',
    'bulong móng': 'Bulong móng',
    'bulong mong': 'Bulong móng',

    # Móng trụ
    'móng trụ chống sét': 'Móng trụ',
    'mong tru chong set': 'Móng trụ',
    'móng trụ': 'Móng trụ',
    'mong tru': 'Móng trụ',

    # Bệ tủ
    'bệ tủ phối quang': 'Bệ tủ',
    'be tu phoi quang': 'Bệ tủ',
    'bệ tủ': 'Bệ tủ',
    'be tu': 'Bệ tủ',

    # Mạch điều khiển
    'mạch điều khiển': 'Mạch điều khiển',
    'mach dieu khien': 'Mạch điều khiển',

    # Các thiết bị điện khác
    'biến tần': 'Biến tần',
    'bien tan': 'Biến tần',
    'vsd': 'Biến tần (VSD)',
    'ổn áp': 'Ổn áp',
    'on ap': 'Ổn áp',
    'avr': 'Ổn áp (AVR)',
    'bộ đếm sét': 'Bộ đếm sét',
    'bo dem set': 'Bộ đếm sét',
    'khóa chuyển mạch': 'Khóa chuyển mạch',
    'khoa chuyen mach': 'Khóa chuyển mạch',
    'khóa chuyển': 'Khóa chuyển mạch',
    'khoa chuyen': 'Khóa chuyển mạch',

    # Hàn
    'hàn hồ quang': 'Hàn hồ quang',
    'han ho quang': 'Hàn hồ quang',

    # Thiết bị điện khác
    'bộ khởi động': 'Bộ khởi động',
    'bo khoi dong': 'Bộ khởi động',
    'biến dòng': 'Biến dòng (CT)',
    'bien dong': 'Biến dòng (CT)',
    'ổ cắm': 'Ổ cắm',
    'o cam': 'Ổ cắm',

    # Tủ điện components
    'vỏ tủ': 'Vỏ tủ điện',
    'vo tu': 'Vỏ tủ điện',
    'thanh cái': 'Thanh cái',
    'thanh cai': 'Thanh cái',

    # Thang thép
    'thang leo thép': 'Thang leo thép',
    'thang leo': 'Thang leo',
    'thang thép': 'Thang thép',
    'thang thep': 'Thang thép',
    'thang cáp': 'Thang cáp',
    'thang cap': 'Thang cáp',

    # Vòi nước / PCCC
    'vòi cấp nước': 'Vòi cấp nước',
    'voi cap nuoc': 'Vòi cấp nước',
    'vòi tưới': 'Vòi tưới',
    'voi tuoi': 'Vòi tưới',

    # Dây đồng trần
    'dây đồng trần': 'Dây đồng trần',
    'day dong tran': 'Dây đồng trần',

    # Thép hình
    'thép dẹt': 'Thép dẹt',
    'thep det': 'Thép dẹt',
    'thép hình': 'Thép hình',
    'thep hinh': 'Thép hình',
    'thép góc': 'Thép góc',
    'thep goc': 'Thép góc',
    'thép nắp đan': 'Thép nắp đan',
    'thep nap dan': 'Thép nắp đan',
    'thép d': 'Cốt thép',
    'thep d': 'Cốt thép',

    # Ống các loại - Must be before cốt thép patterns
    'ống thép mạ kẽm': 'Ống thép',
    'ong thep ma kem': 'Ống thép',
    'ống thép tráng kẽm': 'Ống thép',
    'ong thep trang kem': 'Ống thép',
    'ống ttk': 'Ống thép',
    'ong ttk': 'Ống thép',
    'ống thép đen': 'Ống thép',
    'ong thep den': 'Ống thép',
    'ống thép dn': 'Ống thép',
    'ong thep dn': 'Ống thép',
    'ống thép d': 'Ống thép',
    'ong thep d': 'Ống thép',
    'ống thép': 'Ống thép',
    'ong thep': 'Ống thép',

    # Cốt thép - Must be Priority 2 to win over cống tròn
    'sản xuất, lắp dựng cốt thép': 'Cốt thép',
    'san xuat, lap dung cot thep': 'Cốt thép',
    'lắp dựng cốt thép': 'Cốt thép',
    'lap dung cot thep': 'Cốt thép',
    'cốt thép móng': 'Cốt thép',
    'cot thep mong': 'Cốt thép',
    'cốt thép': 'Cốt thép',
    'cot thep': 'Cốt thép',
    'thép d12': 'Cốt thép',
    'thep d12': 'Cốt thép',
    'thép d': 'Cốt thép',
    'thep d': 'Cốt thép',

    # Đất
    'đất màu': 'Đất màu',
    'dat mau': 'Đất màu',

    # Đá hộc/Đá dăm
    'đa hộc xếp khan': 'Đá hộc',
    'đá hộc xếp khan': 'Đá hộc',
    'đá hộc': 'Đá hộc',
    'da hoc': 'Đá hộc',
    'đá dăm đệm': 'Đá dăm',
    'da dam dem': 'Đá dăm',

    # Vật liệu khác
    'vải địa kỹ thuật': 'Vải địa kỹ thuật',
    'vai dia ky thuat': 'Vải địa kỹ thuật',
    'vải địa': 'Vải địa kỹ thuật',
    'vai dia': 'Vải địa kỹ thuật',
    'nilon tái sinh': 'Nilon',
    'nilon tai sinh': 'Nilon',
    'nilon': 'Nilon',
    'bản quan trắc': 'Bản quan trắc',
    'ban quan trac': 'Bản quan trắc',
    'lưới cảnh báo': 'Lưới cảnh báo',
    'luoi canh bao': 'Lưới cảnh báo',
    'gạch đặc': 'Gạch',
    'gach dac': 'Gạch',
    'gạch': 'Gạch',
    'gach': 'Gạch',

    # Hàn / Mối hàn
    'mối hàn điện': 'Mối hàn điện',
    'moi han dien': 'Mối hàn điện',
    'hàn hóa nhiệt': 'Hàn hóa nhiệt',
    'han hoa nhiet': 'Hàn hóa nhiệt',
    'mối hàn': 'Mối hàn',
    'moi han': 'Mối hàn',

    # Bu lông / Ổ khóa
    'bu lông': 'Bu lông',
    'bu long': 'Bu lông',
    'ổ khóa': 'Ổ khóa',
    'o khoa': 'Ổ khóa',

    # Thanh dẫn hướng
    'thanh dẫn hướng': 'Thanh dẫn hướng',
    'thanh dan huong': 'Thanh dẫn hướng',

    # Tiếp địa
    'thanh tiếp địa': 'Thanh tiếp địa',
    'thanh tiep dia': 'Thanh tiếp địa',
    'dây tiếp địa': 'Dây tiếp địa',
    'day tiep dia': 'Dây tiếp địa',
    'hộp kiểm tra tiếp địa': 'Hộp kiểm tra tiếp địa',
    'hop kiem tra tiep dia': 'Hộp kiểm tra tiếp địa',

    # Vữa
    'vữa chèn': 'Vữa',
    'vua chen': 'Vữa',
    'vữa': 'Vữa',
    'vua': 'Vữa',
    'chét khe': 'Chét khe',
    'chet khe': 'Chét khe',

    # Cột thép
    'cột thép': 'Cột thép',
    'cot thep': 'Cột thép',

    # Gem hóa chất
    'gem hóa chất': 'Gem hóa chất',
    'gem hoa chat': 'Gem hóa chất',

    # Đế âm
    'đế âm': 'Đế âm',
    'de am': 'Đế âm',

    # Vật tư phụ / Chi phí
    'vật tư phụ': 'Vật tư phụ',
    'vat tu phu': 'Vật tư phụ',
    'chi phí kiểm định': 'Chi phí',
    'chi phi kiem dinh': 'Chi phí',
    'chi phí thí nghiệm': 'Chi phí',
    'chi phi thi nghiem': 'Chi phí',
    'chi phí': 'Chi phí',
    'chi phi': 'Chi phí',

    # Ống luồn dây / Ống mềm
    'ống nhựa xoắn': 'Ống luồn dây',
    'ong nhua xoan': 'Ống luồn dây',
    'ống luồn dây': 'Ống luồn dây',
    'ong luon day': 'Ống luồn dây',
    'ống mềm': 'Ống luồn dây',
    'ong mem': 'Ống luồn dây',
}

# Priority 3: Vật liệu gốc (Raw Materials)
# Rule: Chỉ match khi KHÔNG có Priority 1-2
_HARDCODED_P3 = {
    # Bê tông
    'bê tông cốt thép': 'BTCT',
    'be tong cot thep': 'BTCT',
    'bê tông thương phẩm': 'Bê tông thương phẩm',
    'be tong thuong pham': 'Bê tông thương phẩm',
    'bê tông': 'Bê tông',
    'be tong': 'Bê tông',
    'btct': 'BTCT',

    # Đá/Cát
    'đá granite': 'Đá Granite',
    'da granite': 'Đá Granite',
    'đá tự nhiên': 'Đá tự nhiên',
    'da tu nhien': 'Đá tự nhiên',
    'đá dăm': 'Đá dăm',
    'da dam': 'Đá dăm',
    'đá': 'Đá',
    'da': 'Đá',
    'cát': 'Cát',
    'cat': 'Cát',
    'sỏi': 'Sỏi',
    'soi': 'Sỏi',
    'cấp phối đá dăm': 'CPĐD',
    'cap phoi da dam': 'CPĐD',
    'cpđd': 'CPĐD',

    # Nhựa đường
    'bê tông nhựa': 'BTN',
    'be tong nhua': 'BTN',
    'nhựa đường': 'Nhựa đường',
    'nhua duong': 'Nhựa đường',
    'btn': 'BTN',
    'asphalt': 'BTN',

    # MEP materials - Ống (only non-steel pipes left here)
    'ống nhựa hdpe': 'Ống HDPE',
    'ong nhua hdpe': 'Ống HDPE',
    'ống hdpe': 'Ống HDPE',
    'ong hdpe': 'Ống HDPE',
    'ống u.pvc': 'Ống uPVC',
    'ong u.pvc': 'Ống uPVC',
    'ống upvc': 'Ống uPVC',
    'ong upvc': 'Ống uPVC',
    'ống pvc': 'Ống PVC',
    'ong pvc': 'Ống PVC',
    'ống ppr': 'Ống PPR',
    'ong ppr': 'Ống PPR',
    'ống gi': 'Ống GI',
    'ong gi': 'Ống GI',
    'ống inox': 'Ống Inox',
    'ong inox': 'Ống Inox',
    'ống nhựa': 'Ống nhựa',
    'ong nhua': 'Ống nhựa',
    'ống điện': 'Ống luồn dây',
    'ong dien': 'Ống luồn dây',
    'ống': 'Ống',
    'ong': 'Ống',

    # Cáp điện
    'cáp trung thế': 'Cáp trung thế',
    'cap trung the': 'Cáp trung thế',
    'cáp hạ thế': 'Cáp hạ thế',
    'cap ha the': 'Cáp hạ thế',
    'cáp rs232': 'Cáp tín hiệu',
    'cap rs232': 'Cáp tín hiệu',
    'cáp rs485': 'Cáp tín hiệu',
    'cap rs485': 'Cáp tín hiệu',
    'cáp cu/xlpe/pvc/dsta/pvc': 'Cáp điện',
    'cap cu/xlpe/pvc/dsta/pvc': 'Cáp điện',
    'cu/xlpe/pvc/dsta/pvc': 'Cáp điện',
    'cu/xple/pvc/dsta/pvc': 'Cáp điện',
    'cáp cu/xlpe/pvc': 'Cáp điện',
    'cap cu/xlpe/pvc': 'Cáp điện',
    'cu/xlpe/pvc': 'Cáp điện',
    'cu/xple/pvc': 'Cáp điện',
    'cu/mica/xlpe': 'Cáp điện',
    'cáp trong ống': 'Cáp',
    'cap trong ong': 'Cáp',
    'cáp điện ngầm': 'Cáp điện ngầm',
    'cap dien ngam': 'Cáp điện ngầm',
    'cáp điện': 'Cáp điện',
    'cap dien': 'Cáp điện',
    'cáp': 'Cáp',
    'cap': 'Cáp',
    'dây điện': 'Dây điện',
    'day dien': 'Dây điện',
    # Cable by material pattern (Cu/xxx or Cu-xxx)
    'cu-fr/xlpe/pvc': 'Cáp điện',
    'cu/pvc/pvc': 'Cáp điện',
    'cu/pvc': 'Cáp điện',
    'cu/xlpe': 'Cáp điện',
    'cu/xple': 'Cáp điện',
}

_HARDCODED_EXCLUSION_PATTERNS = {
    'cong': [
        'cong suat',     # công suất (power)
        'cong cong',     # công cộng (public)
        'thi cong',      # thi công (construct)
        'cong nhan',     # công nhân (worker)
        'cong trinh',    # công trình (project)
        'cong truong',   # công trường (site)
        'hoan cong',     # hoàn công (completion)
        'gia cong',      # gia công (fabricate)
        'cong viec',     # công việc (work)
        'cong nghe',     # công nghệ (technology)
        'cong ty',       # công ty (company)
        'te cong',       # tê cong (pipe elbow fitting)
        'chong an mon',  # chống ăn mòn (anti-corrosion)
        'chong xoay',    # chống xoáy (anti-vortex)
        'co cong',       # co cong (elbow fitting)
    ],
    'cong tac': [
        'kem cong tac',  # kèm công tắc = accessory switch, not main object
    ],
    'quet': [
        'bon dau',       # bồn dầu + quét nhựa đường → bồn dầu, not quét
    ],
    'may phat dien': [
        'mang cap',      # máng cáp từ máy phát điện → máng cáp, not máy phát điện
    ],
}

# --- Resolve data source: JSON → hardcoded fallback ---
_DATA_SOURCE = 'hardcoded'
try:
    from .data_loader import load_priority_dictionaries as _load_priority_dicts
    _priority_data = _load_priority_dicts()
    PRIORITY_1_METHODS = _priority_data['priority_1_methods']
    PRIORITY_2_COMPONENTS = _priority_data['priority_2_components']
    PRIORITY_3_MATERIALS = _priority_data['priority_3_materials']
    _EXCLUSION_PATTERNS = _priority_data['exclusion_patterns']
    _DATA_SOURCE = 'json'
except Exception:
    PRIORITY_1_METHODS = _HARDCODED_P1
    PRIORITY_2_COMPONENTS = _HARDCODED_P2
    PRIORITY_3_MATERIALS = _HARDCODED_P3
    _EXCLUSION_PATTERNS = _HARDCODED_EXCLUSION_PATTERNS

# Combine all for backward compatibility
ALL_PRIORITY_OBJECTS = {
    **PRIORITY_1_METHODS,
    **PRIORITY_2_COMPONENTS,
    **PRIORITY_3_MATERIALS,
}

# Sort by length for longest match first
ALL_PRIORITY_OBJECTS_SORTED = dict(
    sorted(ALL_PRIORITY_OBJECTS.items(), key=lambda x: len(x[0]), reverse=True)
)

# Build normalized (ASCII) lookup tables for diacritics-tolerant matching
# These deduplicate entries like "ván khuôn" + "van khuon" → single "van khuon"
_NORM_P1 = dict(sorted(
    build_normalized_dict(PRIORITY_1_METHODS).items(),
    key=lambda x: len(x[0]), reverse=True,
))
_NORM_P2 = dict(sorted(
    build_normalized_dict(PRIORITY_2_COMPONENTS).items(),
    key=lambda x: len(x[0]), reverse=True,
))
_NORM_P3 = dict(sorted(
    build_normalized_dict(PRIORITY_3_MATERIALS).items(),
    key=lambda x: len(x[0]), reverse=True,
))

# Pre-group P2/P3 keywords by word count for O(1) lookup in fuzzy matching.
# Structure: {word_count: [(keyword, obj_name, priority, type_name), ...]}
_FUZZY_KEYWORDS_BY_WORDCOUNT = {}
for _priority, _type_name, _norm_dict in [
    (2, 'component', _NORM_P2),
    (3, 'material', _NORM_P3),
]:
    for _kw, _obj in _norm_dict.items():
        _wc = len(_kw.split())
        _FUZZY_KEYWORDS_BY_WORDCOUNT.setdefault(_wc, []).append((_kw, _obj, _priority, _type_name))

# Build choices list per word count for rapidfuzz.process.extract
_FUZZY_CHOICES_BY_WORDCOUNT = {
    wc: [entry[0] for entry in entries]
    for wc, entries in _FUZZY_KEYWORDS_BY_WORDCOUNT.items()
}
# Build keyword→(obj_name, priority, type_name) lookup for quick resolution
_FUZZY_KW_LOOKUP = {}
for entries in _FUZZY_KEYWORDS_BY_WORDCOUNT.values():
    for kw, obj, pri, typ in entries:
        _FUZZY_KW_LOOKUP[kw] = (obj, pri, typ)


import re


# Keywords that share the same "cong" ambiguity.
# Any keyword starting with "cong " inherits the "cong" exclusion list.
_CONG_COMPOUND_KEYWORDS = {'cong hop', 'cong tron', 'cong btct'}

# Regex to detect "den" used as preposition "đến" (to/until) rather than
# noun "đèn" (lamp). Matches when "den" appears mid-text followed by a
# destination word or number. Does NOT match when "den" starts the text
# (which is the typical "Đèn LED..." pattern).
_DEN_AS_PREPOSITION = re.compile(
    r'[a-z0-9]\s+den\s+(?:dan|danh|tang|truc|tu\b|tu |'
    r'ky\b|phong|khu|may|he\b|dong|nha|cap|'
    r'\d)'
)

# Regex to detect "cat" as cable category (Cat5, Cat6, CAT 6E, etc.)
# rather than "cát" (sand). Matches "cat" immediately or with space
# followed by a digit — e.g. "cat6", "cat 6e", "cat5e".
_CAT_AS_CABLE = re.compile(r'cat\s*\d')


def _is_excluded(text_norm: str, keyword: str) -> bool:
    """Check if a keyword match should be excluded based on context."""
    # Direct exclusion lookup
    exclusions = _EXCLUSION_PATTERNS.get(keyword)
    if exclusions and any(excl in text_norm for excl in exclusions):
        return True
    # Compound "cong *" keywords inherit the "cong" exclusion list
    if keyword in _CONG_COMPOUND_KEYWORDS:
        cong_exclusions = _EXCLUSION_PATTERNS.get('cong', [])
        if any(excl in text_norm for excl in cong_exclusions):
            return True
    # "den" as preposition "đến" (to), not noun "đèn" (lamp)
    if keyword == 'den' and _DEN_AS_PREPOSITION.search(text_norm):
        return True
    # "cat" as cable category (Cat5/Cat6/CAT 6E), not "cát" (sand)
    if keyword == 'cat' and _CAT_AS_CABLE.search(text_norm):
        return True
    return False


def identify_object(text: str) -> Tuple[Optional[str], int]:
    """
    Identify object using priority dictionary.

    Uses normalized (diacritics-stripped) matching for automatic
    typo tolerance on Vietnamese diacritics.

    Priority order:
    1. Methods/Activities (Ván khuôn, Vận chuyển, Đào, Đắp, etc.)
    2. Specific Components (Bó vỉa, Tấm đan, Hố ga, Cống, etc.)
    3. Raw Materials (Bê tông, Đá, Cát, Thép, etc.)

    Args:
        text: Input description text

    Returns:
        Tuple of (object_name, priority_level) or (None, 0) if not found.
        priority_level: 1 = Method, 2 = Component, 3 = Material, 0 = Not found
    """
    text_norm = normalize_vietnamese(text)

    # Check each priority level using normalized matching
    for priority, norm_dict in [(1, _NORM_P1), (2, _NORM_P2), (3, _NORM_P3)]:
        for keyword, obj_name in norm_dict.items():
            if _is_word_boundary_match(text_norm, keyword):
                if _is_excluded(text_norm, keyword):
                    continue
                return (obj_name, priority)

    return (None, 0)


def identify_object_with_details(text: str) -> dict:
    """
    Identify object with additional details.

    Uses normalized (diacritics-stripped) matching for automatic
    typo tolerance on Vietnamese diacritics.

    Args:
        text: Input description text

    Returns:
        Dict with keys:
        - object_name: Identified object name or None
        - priority: Priority level (1, 2, 3, or 0)
        - priority_type: 'method', 'component', 'material', or 'unknown'
        - matched_keyword: The keyword that matched
    """
    text_norm = normalize_vietnamese(text)

    # Special case: When text starts with "Bê tông" and "ván khuôn" appears later
    if text_norm.startswith('be tong'):
        # Check for specific bê tông types first
        for keyword, obj_name in [
            ('be tong mat duong', 'Bê tông mặt đường'),
            ('be tong via he', 'Bê tông vỉa hè'),
            ('be tong tam dan', 'Bê tông'),
            ('be tong lot', 'Bê tông lót'),
        ]:
            if keyword in text_norm:
                return {
                    'object_name': obj_name,
                    'priority': 2,
                    'priority_type': 'component',
                    'matched_keyword': keyword,
                }
        # Default concrete
        return {
            'object_name': 'Bê tông',
            'priority': 3,
            'priority_type': 'material',
            'matched_keyword': 'be tong',
        }

    priority_types = {
        1: ('method', _NORM_P1),
        2: ('component', _NORM_P2),
        3: ('material', _NORM_P3),
    }

    for priority, (type_name, norm_dict) in priority_types.items():
        for keyword, obj_name in norm_dict.items():
            if _is_word_boundary_match(text_norm, keyword):
                if _is_excluded(text_norm, keyword):
                    continue
                return {
                    'object_name': obj_name,
                    'priority': priority,
                    'priority_type': type_name,
                    'matched_keyword': keyword,
                }

    return {
        'object_name': None,
        'priority': 0,
        'priority_type': 'unknown',
        'matched_keyword': None,
    }


def identify_all_objects(text: str) -> List[dict]:
    """
    Identify ALL matching objects across P1/P2/P3, not stopping after P1.

    Returns:
        List of dicts (same format as identify_object_with_details),
        sorted by priority (P1 first, then P2, then P3).
        Duplicate object_names are excluded.
    """
    text_norm = normalize_vietnamese(text)
    results = []
    matched_object_names = set()

    # Special case: When text starts with "Bê tông"
    if text_norm.startswith('be tong'):
        for keyword, obj_name in [
            ('be tong mat duong', 'Bê tông mặt đường'),
            ('be tong via he', 'Bê tông vỉa hè'),
            ('be tong tam dan', 'Bê tông'),
            ('be tong lot', 'Bê tông lót'),
        ]:
            if keyword in text_norm and obj_name not in matched_object_names:
                results.append({
                    'object_name': obj_name,
                    'priority': 2,
                    'priority_type': 'component',
                    'matched_keyword': keyword,
                })
                matched_object_names.add(obj_name)
                break
        else:
            # Default concrete
            results.append({
                'object_name': 'Bê tông',
                'priority': 3,
                'priority_type': 'material',
                'matched_keyword': 'be tong',
            })
            matched_object_names.add('Bê tông')

    priority_types = {
        1: ('method', _NORM_P1),
        2: ('component', _NORM_P2),
        3: ('material', _NORM_P3),
    }

    for priority, (type_name, norm_dict) in priority_types.items():
        for keyword, obj_name in norm_dict.items():
            if obj_name in matched_object_names:
                continue
            if _is_word_boundary_match(text_norm, keyword):
                if _is_excluded(text_norm, keyword):
                    continue
                results.append({
                    'object_name': obj_name,
                    'priority': priority,
                    'priority_type': type_name,
                    'matched_keyword': keyword,
                })
                matched_object_names.add(obj_name)

    # Suppress matches whose keyword is a word-subset of another matched keyword.
    # Example: "van" (P2) is word-prefix of "van khuon" (P1) → suppress "van"
    if len(results) > 1:
        all_keywords = {r['matched_keyword'] for r in results if r['matched_keyword']}

        def is_dominated(kw):
            for other_kw in all_keywords:
                if kw == other_kw:
                    continue
                if (other_kw.startswith(kw + ' ') or
                    (' ' + kw + ' ') in other_kw or
                    other_kw.endswith(' ' + kw)):
                    return True
            return False

        results = [r for r in results if not is_dominated(r['matched_keyword'])]

    return results


# Minimum fuzzy match score (0-100)
_FUZZY_THRESHOLD = 85

_NO_FUZZY_MATCH = {
    'object_name': None,
    'priority': 0,
    'priority_type': 'unknown',
    'matched_keyword': None,
    'match_type': 'fuzzy',
    'fuzzy_score': 0,
}


@lru_cache(maxsize=512)
def _cached_fuzzy_identify(text_norm: str) -> tuple:
    """Cached inner fuzzy matching. Returns tuple for hashability, or None."""
    text_words = text_norm.split()
    best_kw = None
    best_score = 0

    for wc, choices in _FUZZY_CHOICES_BY_WORDCOUNT.items():
        if len(text_words) < wc:
            continue

        # Generate n-grams of this word count
        ngrams = [' '.join(text_words[i:i + wc]) for i in range(len(text_words) - wc + 1)]

        for ngram in ngrams:
            if _rfprocess is not None:
                result = _rfprocess.extractOne(
                    ngram, choices, scorer=_fuzz.ratio, score_cutoff=_FUZZY_THRESHOLD,
                )
                if result and result[1] > best_score:
                    matched_kw = result[0]
                    if not _is_excluded(text_norm, matched_kw):
                        best_score = result[1]
                        best_kw = matched_kw
            else:
                # Fallback: manual loop (no rapidfuzz.process)
                for kw in choices:
                    score = _fuzz.ratio(ngram, kw)
                    if score >= _FUZZY_THRESHOLD and score > best_score:
                        if not _is_excluded(text_norm, kw):
                            best_score = score
                            best_kw = kw

    if best_kw:
        obj, pri, typ = _FUZZY_KW_LOOKUP[best_kw]
        return (obj, pri, typ, best_kw, best_score)
    return None


def fuzzy_identify(text: str) -> dict:
    """
    Fuzzy matching fallback for when exact matching fails.

    Only applies to P2 (components) and P3 (materials) patterns.
    P1 methods require exact match to avoid misclassification.

    Uses rapidfuzz with pre-grouped keywords and LRU cache for performance.

    Args:
        text: Input description text

    Returns:
        Dict with keys:
        - object_name: Best fuzzy match or None
        - priority: Priority level (2, 3, or 0)
        - priority_type: 'component', 'material', or 'unknown'
        - matched_keyword: The keyword that matched
        - match_type: 'fuzzy'
        - fuzzy_score: Match score (0-100)
    """
    if _fuzz is None:
        return dict(_NO_FUZZY_MATCH)

    text_norm = normalize_vietnamese(text)
    cached = _cached_fuzzy_identify(text_norm)

    if cached:
        obj_name, priority, priority_type, matched_keyword, fuzzy_score = cached
        return {
            'object_name': obj_name,
            'priority': priority,
            'priority_type': priority_type,
            'matched_keyword': matched_keyword,
            'match_type': 'fuzzy',
            'fuzzy_score': fuzzy_score,
        }

    return dict(_NO_FUZZY_MATCH)
