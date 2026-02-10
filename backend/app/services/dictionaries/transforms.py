"""
Transform functions registry for the Master Resource Dictionary.

Transform functions take (specs, original_text) and return a formatted string
for use in the 3-part output assembly.
"""
import re
from typing import Dict, Callable

# Registry of transform functions
TRANSFORMS: Dict[str, Callable] = {}


def register(name: str):
    """Decorator to register a transform function."""
    def decorator(func):
        TRANSFORMS[name] = func
        return func
    return decorator


# ==========================================================================
# ELECTRICAL TRANSFORMS
# ==========================================================================

@register("combine_electrical_specs")
def combine_electrical_specs(specs: Dict, original: str) -> str:
    """Combine amps and breaking_capacity for electrical devices."""
    parts = []
    if specs.get('amps'):
        parts.append(specs['amps'])
    if specs.get('breaking_capacity'):
        parts.append(specs['breaking_capacity'])
    return ' '.join(parts) if parts else "Theo thiết kế"


@register("extract_busbar_material")
def extract_busbar_material(specs: Dict, original: str) -> str:
    """Extract busbar material (đồng/nhôm)."""
    text_lower = original.lower()
    if 'đồng' in text_lower or 'dong' in text_lower:
        return 'Đồng'
    elif 'nhôm' in text_lower:
        return 'Nhôm'
    return 'Theo thiết kế'


@register("extract_busbar_specs")
def extract_busbar_specs(specs: Dict, original: str) -> str:
    """Extract busbar current or dimensions."""
    if specs.get('current'):
        return specs['current']
    elif specs.get('dimensions'):
        return specs['dimensions']
    return 'Theo thiết kế'


@register("extract_colors")
def extract_colors(specs: Dict, original: str) -> str:
    """Extract color indicators (đỏ/vàng/xanh)."""
    text_lower = original.lower()
    colors = []
    if 'đỏ' in text_lower or 'do ' in text_lower:
        colors.append('Đỏ')
    if 'vàng' in text_lower or 'vang' in text_lower:
        colors.append('Vàng')
    if 'xanh' in text_lower:
        colors.append('Xanh')
    if specs.get('colors'):
        return specs['colors']
    return ', '.join(colors) if colors else 'Theo thiết kế'


@register("extract_signal_type")
def extract_signal_type(specs: Dict, original: str) -> str:
    """Extract signal light type (báo pha/giao thông)."""
    text_lower = original.lower()
    if 'báo pha' in text_lower or 'bao pha' in text_lower:
        return 'Báo pha'
    elif 'giao thông' in text_lower:
        return 'Giao thông'
    return 'Theo thiết kế'


@register("extract_signal_colors")
def extract_signal_colors(specs: Dict, original: str) -> str:
    """Extract colors or voltage for signal lights."""
    text_lower = original.lower()
    colors = []
    if 'đỏ' in text_lower or 'do ' in text_lower:
        colors.append('Đỏ')
    if 'vàng' in text_lower or 'vang' in text_lower:
        colors.append('Vàng')
    if 'xanh' in text_lower:
        colors.append('Xanh')
    if colors:
        return ', '.join(colors)
    if specs.get('voltage'):
        return specs['voltage']
    return 'Theo thiết kế'


# ==========================================================================
# ROAD/EARTHWORK TRANSFORMS
# ==========================================================================

@register("combine_layer_compaction")
def combine_layer_compaction(specs: Dict, original: str) -> str:
    """Combine layer and compaction for road work."""
    from ..imputation_rules import get_cpdd_layer
    parts = []
    layer = get_cpdd_layer(original) or specs.get('layer', '')
    if layer:
        parts.append(layer)
    if specs.get('compaction'):
        parts.append(specs['compaction'])
    return ' '.join(parts) if parts else 'Theo thiết kế'


@register("determine_earth_source")
def determine_earth_source(specs: Dict, original: str) -> str:
    """Determine earth source (Mua mới/Tận dụng)."""
    text_lower = original.lower()
    if specs.get('source'):
        source = specs['source']
        if source == 'Tận dụng nội bộ':
            return 'Tận dụng'
        return source
    if 'đất, cát' in text_lower or 'dat, cat' in text_lower or 'cát, đất' in text_lower:
        return 'Tận dụng'
    if 'mua' in text_lower and 'mới' in text_lower:
        return 'Mua mới'
    return 'Mua mới'


@register("extract_transport_destination")
def extract_transport_destination(specs: Dict, original: str) -> str:
    """Extract transport destination."""
    text_lower = original.lower()
    if 'nội bộ' in text_lower or 'noi bo' in text_lower or 'trong phạm vi' in text_lower:
        return 'Nội bộ dự án'
    elif 'bãi đổ' in text_lower or 'bai do' in text_lower or 'bãi thải' in text_lower:
        return 'Ra bãi thải'
    return specs.get('destination', specs.get('distance', 'Ra bãi thải'))


@register("extract_dao_context")
def extract_dao_context(specs: Dict, original: str) -> str:
    """Extract context for Đào đất."""
    context = specs.get('context', '')
    if context:
        return context
    return 'Theo thiết kế'


@register("extract_dao_pha_do_context")
def extract_dao_pha_do_context(specs: Dict, original: str) -> str:
    """Extract context for Đào phá dỡ."""
    context = specs.get('context', 'Nền đường')
    if '/' in context:
        context = context.split('/')[0]
    return context


@register("extract_dao_pha_do_position")
def extract_dao_pha_do_position(specs: Dict, original: str) -> str:
    """Extract position for Đào phá dỡ."""
    text_lower = original.lower()
    if 'hiện trạng' in text_lower or 'hien trang' in text_lower:
        return 'Hiện trạng'
    return 'Hiện trạng'


@register("format_asphalt_grade")
def format_asphalt_grade(specs: Dict, original: str) -> str:
    """Format asphalt grade (C19, C12.5)."""
    grade = specs.get('asphalt_grade', '')
    if grade:
        return f"Bê tông nhựa {grade}"
    return 'Bê tông nhựa'


@register("extract_asphalt_thickness")
def extract_asphalt_thickness(specs: Dict, original: str) -> str:
    """Extract asphalt thickness."""
    text_lower = original.lower()
    thickness = specs.get('thickness', '')
    if not thickness:
        thick_match = re.search(r'(?:dày|chiều dày)[^\d]*(\d+)\s*(?:cm)?', text_lower)
        if thick_match:
            thickness = f"Dày {thick_match.group(1)}cm"
        else:
            len_match = re.search(r'lèn ép\s*(\d+)', text_lower)
            if len_match:
                thickness = f"Dày {len_match.group(1)}cm"
    if thickness:
        if not thickness.startswith('Dày'):
            thickness = f"Dày {thickness}"
        return thickness
    return 'Theo thiết kế'


@register("extract_tuoi_nhua_dosage")
def extract_tuoi_nhua_dosage(specs: Dict, original: str) -> str:
    """Extract dosage for Tưới nhựa."""
    text_lower = original.lower()
    dosage_match = re.search(r'(\d+(?:[.,]\d+)?)\s*kg/m2', text_lower)
    if dosage_match:
        return f"{dosage_match.group(1)}kg/m2"
    return 'Theo thiết kế'


# ==========================================================================
# CONCRETE TRANSFORMS
# ==========================================================================

@register("extract_stone_spec")
def extract_stone_spec(specs: Dict, original: str) -> str:
    """Extract stone specification for concrete."""
    return specs.get('stone', 'Đá 1x2')


# ==========================================================================
# PIPE FITTING TRANSFORMS
# ==========================================================================

@register("extract_pipe_fitting_material")
def extract_pipe_fitting_material(specs: Dict, original: str) -> str:
    """Extract material for pipe fittings."""
    text_lower = original.lower()
    if specs.get('material'):
        return specs['material']
    if original[0:3].isupper():
        return 'uPVC'
    if 'đầu bơm' in text_lower or 'dau bom' in text_lower:
        return 'Thép/Gang'
    return 'HDPE'


@register("combine_pipe_fitting_specs")
def combine_pipe_fitting_specs(specs: Dict, original: str) -> str:
    """Combine diameter, angle, pressure for pipe fittings."""
    text_lower = original.lower()
    spec_parts = []
    if specs.get('diameter'):
        spec_parts.append(specs['diameter'])
    # Extract angle (e.g., 135 độ, 45 độ)
    # But ONLY if the angle is NOT already in the object name (e.g., "Cút 90 độ")
    # Check if original starts with a fitting type that already has angle
    has_angle_in_name = False
    fitting_patterns = ['cút 90', 'cut 90', 'cút 45', 'cut 45', 'chếch 45', 'chech 45']
    for pattern in fitting_patterns:
        if pattern in text_lower:
            has_angle_in_name = True
            break

    if not has_angle_in_name:
        if specs.get('angle'):
            spec_parts.append(specs['angle'])
        else:
            angle_match = re.search(r'(\d+)\s*độ', text_lower)
            if angle_match:
                spec_parts.append(f"{angle_match.group(1)} độ")

    if specs.get('pressure'):
        spec_parts.append(specs['pressure'])
    if 'đầu bơm' in text_lower or 'dau bom' in text_lower:
        spec_parts.append('Đầu bơm')
    return ' '.join(spec_parts) if spec_parts else 'Theo thiết kế'


@register("extract_valve_connection")
def extract_valve_connection(specs: Dict, original: str) -> str:
    """Extract connection type or material for valves."""
    if specs.get('connection'):
        return specs['connection']
    if specs.get('material'):
        return specs['material']
    return 'Theo thiết kế'


@register("extract_valve_specs")
def extract_valve_specs(specs: Dict, original: str) -> str:
    """Extract diameter and handle for valves."""
    text_lower = original.lower()
    if specs.get('diameter'):
        spec_str = specs['diameter']
        # Only add "Tay gạt" for Van bi (accessory), NOT for Van khóa tay gạt (part of name)
        is_van_khoa = 'van khóa' in text_lower or 'van khoa' in text_lower
        if not is_van_khoa:
            has_tay_gat = 'tay gạt' in text_lower or 'tay gat' in text_lower or specs.get('handle')
            if has_tay_gat:
                spec_str += ' Tay gạt'
        return spec_str
    return 'Theo thiết kế'


# ==========================================================================
# PUMP TRANSFORMS
# ==========================================================================

@register("extract_pump_type")
def extract_pump_type(specs: Dict, original: str) -> str:
    """Extract pump power type (Điện/Diesel)."""
    text_lower = original.lower()
    if 'diesel' in text_lower or 'dầu' in text_lower:
        return 'Diesel'
    return 'Điện'


@register("combine_pump_specs")
def combine_pump_specs(specs: Dict, original: str) -> str:
    """Combine flow, head, power for pumps."""
    spec_parts = []
    for key in ['flow_rate', 'head', 'power']:
        if specs.get(key):
            spec_parts.append(specs[key])
    return ' '.join(spec_parts) if spec_parts else 'Theo thiết kế'


@register("combine_pressure_tank_specs")
def combine_pressure_tank_specs(specs: Dict, original: str) -> str:
    """Combine volume and pressure for Bình tích áp."""
    spec_parts = []
    if specs.get('volume'):
        spec_parts.append(specs['volume'])
    if specs.get('pressure'):
        spec_parts.append(specs['pressure'])
    return ' '.join(spec_parts) if spec_parts else 'Theo thiết kế'


# ==========================================================================
# PIPE TRANSFORMS
# ==========================================================================

@register("determine_pipe_object")
def determine_pipe_object(specs: Dict, original: str) -> str:
    """Determine output object name for pipes."""
    text_lower = original.lower()
    if 'thép' in text_lower:
        return 'Ống thép'
    if 'luồn dây' in text_lower or 'gân xoắn' in text_lower or 'nhựa xoắn' in text_lower:
        return 'Ống luồn dây'
    if re.match(r'^ống\s*pvc\s*d\d+$', text_lower.strip()):
        return 'Ống luồn dây'
    if 'đồng' in text_lower or 'gas' in text_lower:
        return 'Ống đồng'
    return 'Ống nhựa'


@register("extract_pipe_material")
def extract_pipe_material(specs: Dict, original: str) -> str:
    """Extract pipe material."""
    text_lower = original.lower()
    if 'thép tráng kẽm' in text_lower or 'ttk' in text_lower or 'tráng kẽm' in text_lower:
        return 'Thép Tráng kẽm'
    if 'thép đen' in text_lower or 'ống thép đen' in text_lower:
        return 'Đen'
    if 'thép' in text_lower and 'ống' in text_lower:
        # Plain "Ống thép" without qualifier defaults to "Đen"
        return 'Đen'
    if 'ống mềm' in text_lower or 'ong mem' in text_lower:
        return 'Ống mềm'
    if 'hdpe' in text_lower:
        # Check for gân xoắn indicators
        if 'xoắn' in text_lower or 'gân' in text_lower or 'luồn dây' in text_lower:
            return 'HDPE Gân xoắn'
        return 'HDPE'
    if 'pvc' in text_lower and 'luồn dây' in text_lower:
        return 'PVC'
    if 'u.pvc' in text_lower or 'upvc' in text_lower:
        return 'uPVC'
    if 'pvc' in text_lower:
        return 'PVC'
    if 'ppr' in text_lower:
        return 'PPR'
    if specs.get('type'):
        return specs['type']
    return specs.get('material') or 'HDPE'


@register("combine_pipe_specs")
def combine_pipe_specs(specs: Dict, original: str) -> str:
    """Combine diameter and pressure for pipes."""
    spec_parts = []
    if specs.get('diameter'):
        spec_parts.append(specs['diameter'])
    else:
        diam_match = re.search(r'(\d{2,3})\s*/\s*(\d{2,3})', original)
        if diam_match:
            spec_parts.append(f"D{diam_match.group(1)}/{diam_match.group(2)}")
        else:
            text_lower = original.lower()
            dk_match = re.search(r'đường kính\s*(\d+)', text_lower)
            if dk_match:
                spec_parts.append(f"D{dk_match.group(1)}")
    if specs.get('pressure'):
        if re.search(r'[Pp][Nn]\d+', original):
            spec_parts.append(specs['pressure'])
    return ' '.join(spec_parts) if spec_parts else 'Theo thiết kế'


# ==========================================================================
# PRECAST TRANSFORMS
# ==========================================================================

@register("extract_cong_hop_specs")
def extract_cong_hop_specs(specs: Dict, original: str) -> str:
    """Extract specs for Cống hộp (box culvert)."""
    text_lower = original.lower()
    if 'đôi' in text_lower or 'doi' in text_lower:
        dim_match = re.search(r'(\d+)\s*[xX×]\s*(\d+)(?:\s*m)?(?!\s*[xX×]\s*\d)', original)
        if dim_match:
            return f"Đôi {dim_match.group(1)}x{dim_match.group(2)}m"
    triple_match = re.search(r'(\d+)\s*[xX×]\s*(\d+)\s*[xX×]\s*(\d+)', original)
    if triple_match:
        return f"Đôi {triple_match.group(2)}x{triple_match.group(3)}m"
    dim_match = re.search(r'(\d+)\s*[xX×]\s*(\d+)', original)
    if dim_match:
        return f"{dim_match.group(1)}x{dim_match.group(2)}"
    return 'Theo thiết kế'


@register("combine_cong_thoat_nuoc_specs")
def combine_cong_thoat_nuoc_specs(specs: Dict, original: str) -> str:
    """Combine diameter and load for Cống thoát nước."""
    text_lower = original.lower()
    spec_parts = []
    if specs.get('diameter'):
        spec_parts.append(specs['diameter'])
    if 'tải trọng' in text_lower or 'tai trong' in text_lower:
        if 'tc' in text_lower:
            spec_parts.append('Tải trọng TC')
    return ' '.join(spec_parts) if spec_parts else 'Theo thiết kế'


@register("extract_bo_via_specs")
def extract_bo_via_specs(specs: Dict, original: str) -> str:
    """Extract specs for Bó vỉa."""
    text_lower = original.lower()
    dims = specs.get('dimensions', '')
    spec_str = dims if dims else ''
    if 'hạ hè' in text_lower or 'ha he' in text_lower:
        spec_str = (spec_str + ' Hạ hè').strip()
    elif 'vuốt nối' in text_lower:
        spec_str = 'Vuốt nối'
    return spec_str if spec_str else 'Theo thiết kế'


@register("convert_cm_to_mm_dimensions")
def convert_cm_to_mm_dimensions(specs: Dict, original: str) -> str:
    """Convert dimensions from cm to mm for Tấm đan."""
    dims = specs.get('dimensions', '')
    if not dims:
        return 'Theo thiết kế'
    parts = re.split(r'[xX×]', dims)
    if len(parts) >= 2:
        try:
            values = [int(p.strip()) for p in parts]
            if all(v < 200 for v in values):
                converted = [str(v * 10) for v in values]
                return 'x'.join(converted)
        except ValueError:
            pass
    return dims


# ==========================================================================
# MEP EQUIPMENT TRANSFORMS
# ==========================================================================

@register("extract_nap_ho_ga_specs")
def extract_nap_ho_ga_specs(specs: Dict, original: str) -> str:
    """Extract specs for Nắp hố ga."""
    text_lower = original.lower()
    spec_parts = []
    if specs.get('load_rating'):
        spec_parts.append(specs['load_rating'])
    load_match = re.search(r'(\d+(?:[.,]\d+)?)\s*tấn', text_lower)
    if load_match:
        load_val = load_match.group(1).replace(',', '.')
        spec_parts.append(f"{load_val} tấn")
    if specs.get('position'):
        spec_parts.append(specs['position'])
    return ' '.join(spec_parts) if spec_parts else 'Theo thiết kế'


@register("extract_nap_ho_ga_material")
def extract_nap_ho_ga_material(specs: Dict, original: str) -> str:
    """Extract material for Nắp hố ga."""
    text_lower = original.lower()
    if 'loại 2' in text_lower or 'loai 2' in text_lower:
        return 'Composite/Gang'
    return specs.get('material') or 'Gang'


@register("extract_song_chan_rac_specs")
def extract_song_chan_rac_specs(specs: Dict, original: str) -> str:
    """Extract specs for Song chắn rác."""
    spec_parts = []
    dim_match = re.search(r'(\d{3,4})\s*[xX×]\s*(\d{3,4})', original)
    if dim_match:
        spec_parts.append(f"{dim_match.group(1)}x{dim_match.group(2)}")
    kn_match = re.search(r'(\d+)\s*[kK][nN]', original)
    if kn_match:
        spec_parts.append(f"{kn_match.group(1)}kN")
    return ' '.join(spec_parts) if spec_parts else 'Theo thiết kế'


@register("extract_song_chan_rac_material")
def extract_song_chan_rac_material(specs: Dict, original: str) -> str:
    """Extract material for Song chắn rác."""
    text_lower = original.lower()
    material = specs.get('material') or 'Gang'
    if 'en124' in text_lower or 'en 124' in text_lower:
        material += ' EN124'
    return material


@register("extract_cot_den_specs")
def extract_cot_den_specs(specs: Dict, original: str) -> str:
    """Extract specs for Cột đèn."""
    spec_parts = []
    if specs.get('height'):
        spec_parts.append(specs['height'])
    if specs.get('arm_type'):
        spec_parts.append(specs['arm_type'])
    return ' '.join(spec_parts) if spec_parts else 'Theo thiết kế'


@register("extract_den_chieu_sang_fixture")
def extract_den_chieu_sang_fixture(specs: Dict, original: str) -> str:
    """Extract fixture type for Đèn chiếu sáng."""
    return specs.get('fixture_type', 'Theo thiết kế')


@register("extract_den_chieu_sang_specs")
def extract_den_chieu_sang_specs(specs: Dict, original: str) -> str:
    """Extract light specs for Đèn chiếu sáng."""
    return specs.get('light_spec', 'Theo thiết kế')


@register("extract_coc_tiep_dia_length")
def extract_coc_tiep_dia_length(specs: Dict, original: str) -> str:
    """Extract length for Cọc tiếp địa."""
    return specs.get('length', 'Theo thiết kế')


@register("extract_hop_dong_ho_dims")
def extract_hop_dong_ho_dims(specs: Dict, original: str) -> str:
    """Extract dimensions for Hộp đồng hồ."""
    dims = specs.get('dimensions', '')
    if dims:
        return dims
    kt_match = re.search(r'[Kk][Tt]?\s*(\d+)\s*[xX×]\s*(\d+)(?:\s*[xX×]\s*(\d+))?', original)
    if kt_match:
        if kt_match.group(3):
            return f"{kt_match.group(1)}x{kt_match.group(2)}x{kt_match.group(3)}"
        return f"{kt_match.group(1)}x{kt_match.group(2)}"
    return 'Theo thiết kế'


@register("extract_khung_mong_specs")
def extract_khung_mong_specs(specs: Dict, original: str) -> str:
    """Extract specs for Khung móng."""
    text_lower = original.lower()
    spec_parts = []
    bulong_match = re.search(r'bulong\s*[Mm](\d+)', text_lower)
    if bulong_match:
        spec_parts.append(f"Bulong M{bulong_match.group(1)}")
    spec_parts.append('Trọn bộ')
    return ' '.join(spec_parts)


@register("extract_be_tu_purpose")
def extract_be_tu_purpose(specs: Dict, original: str) -> str:
    """Extract purpose for Bệ tủ."""
    text_lower = original.lower()
    if 'phối quang' in text_lower or 'phoi quang' in text_lower:
        return 'Tủ phối quang'
    return 'Theo thiết kế'


@register("extract_lo_xo_purpose")
def extract_lo_xo_purpose(specs: Dict, original: str) -> str:
    """Extract purpose for Lò xo giảm chấn."""
    text_lower = original.lower()
    if 'bơm chữa cháy' in text_lower or 'bom chua chay' in text_lower:
        return 'Bơm chữa cháy'
    elif 'bơm' in text_lower:
        return 'Bơm'
    return 'Theo thiết kế'


@register("extract_nilon_type")
def extract_nilon_type(specs: Dict, original: str) -> str:
    """Extract type for Nilon."""
    text_lower = original.lower()
    if 'tái sinh' in text_lower or 'tai sinh' in text_lower:
        return 'Tái sinh'
    return 'Theo thiết kế'


@register("extract_nilon_purpose")
def extract_nilon_purpose(specs: Dict, original: str) -> str:
    """Extract purpose for Nilon."""
    text_lower = original.lower()
    if 'lót móng' in text_lower or 'lot mong' in text_lower:
        return 'Lót móng'
    elif 'lót' in text_lower:
        return 'Lót'
    return 'Lót móng'


@register("extract_chi_phi_type")
def extract_chi_phi_type(specs: Dict, original: str) -> str:
    """Extract type for Chi phí."""
    text_lower = original.lower()
    if 'thí nghiệm' in text_lower and 'kiểm định' not in text_lower:
        return 'Thí nghiệm'
    elif 'kiểm định' in text_lower and 'thí nghiệm' not in text_lower:
        return 'Kiểm định'
    return 'Kiểm định/Thí nghiệm'


@register("extract_chi_phi_scope")
def extract_chi_phi_scope(specs: Dict, original: str) -> str:
    """Extract scope for Chi phí."""
    text_lower = original.lower()
    if 'điện trở nối đất' in text_lower or 'dien tro noi dat' in text_lower:
        return 'Điện trở nối đất'
    return 'Trọn gói'


@register("extract_da_hoc_type")
def extract_da_hoc_type(specs: Dict, original: str) -> str:
    """Extract type for Đá hộc."""
    text_lower = original.lower()
    if 'xếp khan' in text_lower or 'xep khan' in text_lower:
        return 'Xếp khan'
    return 'Theo thiết kế'


@register("extract_da_dam_purpose")
def extract_da_dam_purpose(specs: Dict, original: str) -> str:
    """Extract purpose for Đá dăm."""
    text_lower = original.lower()
    if 'đệm' in text_lower:
        return 'Đệm móng'
    return 'Theo thiết kế'


@register("extract_trat_position")
def extract_trat_position(specs: Dict, original: str) -> str:
    """Extract position for Trát/Láng/Chèn vữa."""
    text_lower = original.lower()
    if 'tiếp giáp' in text_lower or 'tiep giap' in text_lower:
        if 'cống' in text_lower or 'cong' in text_lower:
            return 'Tiếp giáp cống'
        elif 'hố ga' in text_lower or 'ho ga' in text_lower:
            return 'Tiếp giáp hố ga'
        return 'Tiếp giáp'
    elif 'thành hố ga' in text_lower or 'thanh ho ga' in text_lower:
        return 'Thành hố ga'
    elif 'đáy hố ga' in text_lower or 'day ho ga' in text_lower:
        return 'Đáy hố ga'
    return 'Theo thiết kế'


@register("extract_trat_mortar")
def extract_trat_mortar(specs: Dict, original: str) -> str:
    """Extract mortar type for Trát/Láng/Chèn vữa."""
    text_lower = original.lower()
    if 'xi măng' in text_lower or 'xi mang' in text_lower:
        return 'Xi măng'
    return specs.get('mortar', 'Vữa xi măng')


@register("extract_xay_gach_position")
def extract_xay_gach_position(specs: Dict, original: str) -> str:
    """Extract position for Xây gạch."""
    text_lower = original.lower()
    if 'hố ga' in text_lower:
        return 'Hố ga'
    return 'Theo thiết kế'


@register("extract_xay_tuong_type")
def extract_xay_tuong_type(specs: Dict, original: str) -> str:
    """Extract type for Xây tường."""
    text_lower = original.lower()
    if 'chắn' in text_lower or 'chan' in text_lower:
        return 'Tường chắn'
    return 'Theo thiết kế'


@register("extract_mong_tru_purpose")
def extract_mong_tru_purpose(specs: Dict, original: str) -> str:
    """Extract purpose for Móng trụ."""
    text_lower = original.lower()
    if 'chống sét' in text_lower or 'chong set' in text_lower:
        return 'Chống sét'
    return 'Theo thiết kế'


@register("extract_quan_trac_type")
def extract_quan_trac_type(specs: Dict, original: str) -> str:
    """Extract type for Bản quan trắc."""
    text_lower = original.lower()
    if 'lún' in text_lower or 'lun' in text_lower:
        return 'Quan trắc lún'
    return 'Theo thiết kế'


@register("extract_trong_co_position")
def extract_trong_co_position(specs: Dict, original: str) -> str:
    """Extract position for Trồng cỏ."""
    text_lower = original.lower()
    if 'mái' in text_lower or 'taluy' in text_lower or 'bờ kênh' in text_lower:
        return 'Mái taluy'
    return 'Theo thiết kế'


@register("extract_trong_co_care")
def extract_trong_co_care(specs: Dict, original: str) -> str:
    """Extract care info for Trồng cỏ."""
    text_lower = original.lower()
    if 'chăm sóc' in text_lower or 'cham soc' in text_lower:
        return 'Bao gồm chăm sóc'
    return 'Theo thiết kế'


@register("extract_binh_chua_chay_model")
def extract_binh_chua_chay_model(specs: Dict, original: str) -> str:
    """Extract model for Bình chữa cháy."""
    return specs.get('ext_model', 'Theo thiết kế')


@register("extract_cau_chi_specs")
def extract_cau_chi_specs(specs: Dict, original: str) -> str:
    """Extract specs for Cầu chì."""
    spec_parts = []
    if specs.get('poles'):
        spec_parts.append(specs['poles'])
    if specs.get('current'):
        spec_parts.append(specs['current'])
    if specs.get('voltage'):
        spec_parts.append(specs['voltage'])
    return ' '.join(spec_parts) if spec_parts else 'Theo thiết kế'


@register("extract_coc_tre_spec")
def extract_coc_tre_spec(specs: Dict, original: str) -> str:
    """Extract spec for Cọc tre."""
    spec = specs.get('spec', 'Theo thiết kế')
    return spec.lower() if spec else 'theo thiết kế'


@register("extract_rebar_size")
def extract_rebar_size(specs: Dict, original: str) -> str:
    """Extract rebar size for Cốt thép."""
    rebar_size = specs.get('rebar_diameter') or specs.get('diameter')
    if not rebar_size:
        size_match = re.search(r'[≤<](\d+)\s*mm', original)
        if size_match:
            return f"≤{size_match.group(1)}mm"
        d_match = re.search(r'[Dd](\d+)', original)
        if d_match:
            return f"D{d_match.group(1)}"
    return rebar_size if rebar_size else 'Theo thiết kế'


# ==========================================================================
# TRAFFIC SIGN TRANSFORMS
# ==========================================================================

@register("extract_sign_type")
def extract_sign_type(specs: Dict, original: str) -> str:
    """Extract sign type for Biển báo."""
    text_lower = original.lower()
    if 'tam giác' in text_lower:
        return 'Tam giác'
    if 'chỉ hướng' in text_lower or 'chi huong' in text_lower:
        # Extract code like 414A
        match = re.search(r'chỉ hướng\s*(\d+[A-Za-z]?)', text_lower, re.I)
        if not match:
            match = re.search(r'chi huong\s*(\d+[A-Za-z]?)', text_lower, re.I)
        if match:
            return f"Chỉ hướng {match.group(1).upper()}"
        return 'Chỉ hướng'
    if 'tròn' in text_lower or 'tron' in text_lower:
        return 'Tròn'
    if 'vuông' in text_lower or 'vuong' in text_lower:
        return 'Vuông'
    return 'Theo thiết kế'


@register("extract_sign_specs")
def extract_sign_specs(specs: Dict, original: str) -> str:
    """Extract specs for Biển báo (size, accessories)."""
    text_lower = original.lower()
    parts = []
    # Extract size (A70cm, 100x160cm, etc.)
    size_match = re.search(r'([A-Za-z]?\d+(?:[xX×]\d+)?)\s*cm', original, re.I)
    if size_match:
        parts.append(size_match.group(0))
    # Extract accessories (cột sơn trắng đỏ)
    if 'cột' in text_lower and 'sơn' in text_lower:
        parts.append('Cột sơn trắng đỏ')
    return ' '.join(parts) if parts else 'Theo thiết kế'


# ==========================================================================
# VALVE ACCESSORY TRANSFORMS
# ==========================================================================

@register("extract_valve_type_with_accessories")
def extract_valve_type_with_accessories(specs: Dict, original: str) -> str:
    """Extract valve type with accessories for Van bi."""
    text_lower = original.lower()
    parts = []
    if 'rắc co đôi' in text_lower or 'rac co doi' in text_lower:
        parts.append('rắc co đôi')
    if parts:
        return ' '.join(parts)
    return specs.get('type', 'Theo thiết kế')


@register("extract_valve_specs_with_handle")
def extract_valve_specs_with_handle(specs: Dict, original: str) -> str:
    """Extract valve specs including handle type."""
    text_lower = original.lower()
    spec_parts = []
    if specs.get('diameter'):
        spec_parts.append(specs['diameter'])
    # Only add "Tay gạt" if it's not already in the object name
    # (e.g., "Van bi tay gạt" should add it, but "Van khóa tay gạt" should not)
    if 'van bi' in text_lower and ('tay gạt' in text_lower or 'tay gat' in text_lower):
        spec_parts.append('Tay gạt')
    return ' '.join(spec_parts) if spec_parts else 'Theo thiết kế'


# ==========================================================================
# STEEL PIPE MATERIAL TRANSFORM
# ==========================================================================

@register("extract_steel_pipe_material")
def extract_steel_pipe_material(specs: Dict, original: str) -> str:
    """Extract material for Ống thép (Đen/Tráng kẽm)."""
    text_lower = original.lower()
    if 'mạ kẽm' in text_lower or 'tráng kẽm' in text_lower or 'ttk' in text_lower:
        return 'Thép Tráng kẽm'
    # Default for plain "Ống thép" is "Đen"
    if 'đen' in text_lower:
        return 'Đen'
    # If no explicit material, default to "Đen"
    return 'Đen'


# ==========================================================================
# INSTRUMENT / METERING TRANSFORMS
# ==========================================================================

@register("extract_accuracy_class")
def extract_accuracy_class(specs: Dict, original: str) -> str:
    """Extract accuracy class for meters (e.g., 0.5S)."""
    match = re.search(r'(\d+[.,]\d+\s*[Ss])', original)
    if match:
        return f"Cấp {match.group(1).replace(',', '.')}"
    return "Theo thiết kế"


@register("extract_protocol")
def extract_protocol(specs: Dict, original: str) -> str:
    """Extract communication protocol (Modbus, RS485, etc.)."""
    text_lower = original.lower()
    if 'modbus rtu' in text_lower:
        return 'Modbus RTU'
    if 'modbus' in text_lower:
        return 'Modbus'
    if 'rs485' in text_lower:
        return 'RS485'
    return 'Theo thiết kế'


# ==========================================================================
# GENERIC MEP TRANSFORMS
# ==========================================================================

@register("extract_mep_type")
def extract_mep_type(specs: Dict, original: str) -> str:
    """Extract equipment subtype from description."""
    text_lower = original.lower()
    # Loa subtypes
    if 'âm trần' in text_lower or 'am tran' in text_lower:
        return 'Âm trần'
    if 'hộp' in text_lower and 'chống nước' in text_lower:
        return 'Hộp chống nước'
    if 'loa hộp' in text_lower or 'loa hop' in text_lower:
        return 'Hộp'
    # Fan subtypes
    if 'hướng trục' in text_lower:
        return 'Hướng trục'
    if 'gắn tường' in text_lower:
        return 'Gắn tường'
    if 'gió thải' in text_lower:
        return 'Gió thải'
    if 'hút khói' in text_lower:
        return 'Hút khói'
    if 'thông gió' in text_lower:
        return 'Thông gió'
    if 'gắn trần' in text_lower:
        return 'Gắn trần'
    # Camera subtypes
    if 'dome' in text_lower:
        return 'Dome'
    if 'ptz' in text_lower:
        return 'PTZ'
    if 'thân' in text_lower or 'bullet' in text_lower:
        return 'Thân cố định'
    # Generic subtypes
    if 'chọn vùng' in text_lower:
        return 'Chọn vùng'
    return 'Theo thiết kế'


@register("extract_mep_power")
def extract_mep_power(specs: Dict, original: str) -> str:
    """Extract power/capacity specs: W, kW, kVA, BTU, VA, HP, etc."""
    parts = []
    # kVA
    kva_match = re.search(r'(\d+(?:[.,]\d+)?)\s*[kK][vV][aA]', original)
    if kva_match:
        parts.append(f"{kva_match.group(1)}kVA")
    # kW
    kw_match = re.search(r'(\d+(?:[.,]\d+)?)\s*[kK][wW](?![hH])', original)
    if kw_match:
        parts.append(f"{kw_match.group(1)}kW")
    # Watt (only if no kW found)
    if not kw_match:
        w_match = re.search(r'(\d+(?:[.,]\d+)?)\s*[wW](?!\s*[/xX×])', original)
        if w_match:
            parts.append(f"{w_match.group(1)}W")
    # BTU
    btu_match = re.search(r'(\d+(?:[.,]\d+)?)\s*[bB][tT][uU]', original)
    if btu_match:
        parts.append(f"{btu_match.group(1)}BTU")
    # VA (only if no kVA found)
    if not kva_match:
        va_match = re.search(r'(\d+)\s*VA\b', original)
        if va_match:
            parts.append(f"{va_match.group(1)}VA")
    # HP
    hp_match = re.search(r'(\d+(?:[.,]\d+)?)\s*[hH][pP]', original)
    if hp_match:
        parts.append(f"{hp_match.group(1)}HP")
    # Flow rate l/s or m³/h
    flow_match = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:l/s|m[³3]/h)', original, re.IGNORECASE)
    if flow_match:
        unit = 'l/s' if 'l/s' in original.lower() else 'm³/h'
        parts.append(f"{flow_match.group(1)}{unit}")
    # Current (A) - only standalone, not part of ratio like 2500/5A or model number like RF-01A
    a_match = re.search(r'(?<![/-])\b(\d+)\s*[aA]\b(?!/)', original)
    if a_match:
        parts.append(f"{a_match.group(1)}A")
    return ' '.join(parts) if parts else 'Theo thiết kế'


@register("extract_dimensions_wxh")
def extract_dimensions_wxh(specs: Dict, original: str) -> str:
    """Extract WxH or WxHxD dimensions (e.g., 600x400, 200x100x1.5)."""
    # Match dimensions like 600x400, 200x100x1.5, 300x100
    dim_match = re.search(
        r'(\d+(?:\.\d+)?)\s*[xX×]\s*(\d+(?:\.\d+)?)(?:\s*[xX×]\s*(\d+(?:\.\d+)?))?',
        original
    )
    if dim_match:
        w, h = dim_match.group(1), dim_match.group(2)
        d = dim_match.group(3)
        if d:
            return f"{w}x{h}x{d}"
        return f"{w}x{h}"
    # Diameter Ø or DN
    dia_match = re.search(r'[ØΦ]\s*(\d+)', original)
    if dia_match:
        return f"Ø{dia_match.group(1)}"
    dn_match = re.search(r'DN\s*(\d+)', original, re.IGNORECASE)
    if dn_match:
        return f"DN{dn_match.group(1)}"
    return 'Theo thiết kế'


@register("extract_ct_ratio")
def extract_ct_ratio(specs: Dict, original: str) -> str:
    """Extract CT ratio for Biến dòng (e.g., 2500/5A)."""
    ratio_match = re.search(r'(\d+)\s*/\s*(\d+)\s*[aA]', original)
    if ratio_match:
        return f"{ratio_match.group(1)}/{ratio_match.group(2)}A"
    return 'Theo thiết kế'


@register("extract_ct_class")
def extract_ct_class(specs: Dict, original: str) -> str:
    """Extract CT accuracy class (loại 1, 5P10, 0.5, etc.) and VA."""
    parts = []
    # Class: "loại 1", "loại 0.5", "loại 5P10"
    class_match = re.search(r'loại\s+(\S+)', original, re.IGNORECASE)
    if class_match:
        parts.append(f"Loại {class_match.group(1)}")
    # VA rating
    va_match = re.search(r'(\d+)\s*VA', original)
    if va_match:
        parts.append(f"{va_match.group(1)}VA")
    return ' '.join(parts) if parts else 'Theo thiết kế'


@register("extract_contactor_specs")
def extract_contactor_specs(specs: Dict, original: str) -> str:
    """Extract contactor specs (poles, current, coil voltage)."""
    parts = []
    # Poles: 3P, 4P
    poles_match = re.search(r'(\d)\s*[pP](?:\s|$|,)', original)
    if poles_match:
        parts.append(f"{poles_match.group(1)}P")
    # Current: 9A, 150A
    a_match = re.search(r'(\d+)\s*[aA]\b', original)
    if a_match:
        parts.append(f"{a_match.group(1)}A")
    # Coil voltage: 220VAC
    coil_match = re.search(r'(\d+)\s*V\s*(?:AC|DC)', original, re.IGNORECASE)
    if coil_match:
        parts.append(f"{coil_match.group(1)}VAC")
    return ' '.join(parts) if parts else 'Theo thiết kế'


@register("extract_rcbo_specs")
def extract_rcbo_specs(specs: Dict, original: str) -> str:
    """Extract RCBO/RCCB specs (sensitivity, poles, current)."""
    parts = []
    # Sensitivity: 30mA, 300mA
    ma_match = re.search(r'(\d+)\s*mA', original)
    if ma_match:
        parts.append(f"{ma_match.group(1)}mA")
    # Poles: 3P+N, 1P+N
    poles_match = re.search(r'(\d[pP]\+?[nN]?)', original)
    if poles_match:
        parts.append(poles_match.group(1).upper())
    # Current: 20A, 40A
    a_match = re.search(r'(\d+)\s*[aA]\b', original)
    if a_match:
        parts.append(f"{a_match.group(1)}A")
    return ' '.join(parts) if parts else 'Theo thiết kế'


@register("extract_surge_specs")
def extract_surge_specs(specs: Dict, original: str) -> str:
    """Extract surge protector specs (poles, kA, type)."""
    parts = []
    # Poles: 3P+N, 1P+N
    poles_match = re.search(r'(\d[pP]\+?[nN]?)', original)
    if poles_match:
        parts.append(poles_match.group(1).upper())
    # kA rating
    ka_match = re.search(r'(\d+)\s*kA', original, re.IGNORECASE)
    if ka_match:
        parts.append(f"{ka_match.group(1)}kA")
    # Type: loại 1, loại 2
    type_match = re.search(r'loại\s+(\d)', original, re.IGNORECASE)
    if type_match:
        parts.append(f"Loại {type_match.group(1)}")
    return ' '.join(parts) if parts else 'Theo thiết kế'


@register("extract_switch_specs")
def extract_switch_specs(specs: Dict, original: str) -> str:
    """Extract switch specs (gangs, poles, current)."""
    parts = []
    text_lower = original.lower()
    # Type
    if 'đơn' in text_lower:
        parts.append('Đơn')
    elif 'đôi' in text_lower:
        parts.append('Đôi')
    elif 'ba' in text_lower:
        parts.append('Ba')
    # Poles
    poles_match = re.search(r'(\d)\s*cực', original, re.IGNORECASE)
    if poles_match:
        parts.append(f"{poles_match.group(1)} cực")
    # Current
    a_match = re.search(r'(\d+)\s*[aA]\b', original)
    if a_match:
        parts.append(f"{a_match.group(1)}A")
    return ' '.join(parts) if parts else 'Theo thiết kế'


@register("extract_duct_material")
def extract_duct_material(specs: Dict, original: str) -> str:
    """Extract duct material/thickness."""
    text_lower = original.lower()
    # Tole thickness
    tole_match = re.search(r'tole\s+(?:dày\s+)?(\d+[.,]?\d*)\s*mm', text_lower)
    if tole_match:
        return f"Tole {tole_match.group(1)}mm"
    if 'mềm' in text_lower:
        return 'Mềm'
    if 'tôn' in text_lower or 'tole' in text_lower:
        return 'Tôn'
    return 'Theo thiết kế'


@register("extract_cable_size")
def extract_cable_size(specs: Dict, original: str) -> str:
    """Extract cable size (e.g., 1C 6mm2, 2Cx1.5mm2)."""
    # Pattern: 1C 6mm2, 2Cx1.5mm2, 4x6mm2
    size_match = re.search(
        r'(\d+)\s*[cCxX]\s*[x×]?\s*(\d+(?:[.,]\d+)?)\s*mm2?',
        original, re.IGNORECASE
    )
    if size_match:
        cores = size_match.group(1)
        area = size_match.group(2)
        return f"{cores}C {area}mm2"
    return 'Theo thiết kế'


@register("extract_mcb_specs")
def extract_mcb_specs(specs: Dict, original: str) -> str:
    """Extract MCB specs (current, breaking capacity)."""
    parts = []
    # Current: 16A, 20A, 100A
    a_match = re.search(r'(\d+)\s*[aA]\b', original)
    if a_match:
        parts.append(f"{a_match.group(1)}A")
    # Breaking capacity: 6KA, 10kA
    ka_match = re.search(r'(\d+)\s*[kK][aA]', original)
    if ka_match:
        parts.append(f"{ka_match.group(1)}kA")
    return ' '.join(parts) if parts else 'Theo thiết kế'


@register("extract_vsd_specs")
def extract_vsd_specs(specs: Dict, original: str) -> str:
    """Extract VSD/VFD specs (power, phases, voltage)."""
    parts = []
    # Phases
    phase_match = re.search(r'(\d)[pP]', original)
    if phase_match:
        parts.append(f"{phase_match.group(1)}P")
    # kW
    kw_match = re.search(r'(\d+(?:[.,]\d+)?)\s*kW', original, re.IGNORECASE)
    if kw_match:
        parts.append(f"{kw_match.group(1)}kW")
    # Voltage range
    v_match = re.search(r'(\d+)[.…]+(\d+)\s*V\s*AC', original)
    if v_match:
        parts.append(f"{v_match.group(1)}-{v_match.group(2)}VAC")
    return ' '.join(parts) if parts else 'Theo thiết kế'


@register("extract_camera_specs")
def extract_camera_specs(specs: Dict, original: str) -> str:
    """Extract camera specs (resolution, IR range, lens)."""
    parts = []
    # Resolution: 2.0 Megapixel, 4MP, 8MP
    mp_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:Megapixel|MP)', original, re.IGNORECASE)
    if mp_match:
        parts.append(f"{mp_match.group(1)}MP")
    # IR range
    ir_match = re.search(r'IR.*?(\d+)\s*m', original, re.IGNORECASE)
    if ir_match:
        parts.append(f"IR {ir_match.group(1)}m")
    return ' '.join(parts) if parts else 'Theo thiết kế'


@register("extract_switch_network_specs")
def extract_switch_network_specs(specs: Dict, original: str) -> str:
    """Extract network switch specs (ports, layer, speed)."""
    parts = []
    # Ports
    port_match = re.search(r'(\d+)\s*(?:PORT|port|Port)', original)
    if port_match:
        parts.append(f"{port_match.group(1)} Port")
    # Layer
    layer_match = re.search(r'Layer\s*(\d)', original, re.IGNORECASE)
    if layer_match:
        parts.append(f"Layer {layer_match.group(1)}")
    # PoE
    if 'poe' in original.lower():
        parts.append('PoE')
    return ' '.join(parts) if parts else 'Theo thiết kế'


@register("extract_dvr_specs")
def extract_dvr_specs(specs: Dict, original: str) -> str:
    """Extract DVR/NVR specs (channels, storage)."""
    parts = []
    # Channels
    ch_match = re.search(r'(\d+)\s*(?:kênh|ch)', original, re.IGNORECASE)
    if ch_match:
        parts.append(f"{ch_match.group(1)} kênh")
    # Storage
    tb_match = re.search(r'(\d+)\s*TB', original)
    if tb_match:
        parts.append(f"{tb_match.group(1)}TB")
    return ' '.join(parts) if parts else 'Theo thiết kế'


@register("extract_rack_specs")
def extract_rack_specs(specs: Dict, original: str) -> str:
    """Extract rack specs (U height, dimensions)."""
    parts = []
    # U height: 42U, 19U
    u_match = re.search(r'(\d+)\s*[uU]', original)
    if u_match:
        parts.append(f"{u_match.group(1)}U")
    # Dimensions: 600x800
    dim_match = re.search(r'(\d+)\s*[xX×]\s*(\d+)', original)
    if dim_match:
        parts.append(f"{dim_match.group(1)}x{dim_match.group(2)}")
    return ' '.join(parts) if parts else 'Theo thiết kế'


@register("extract_junction_box_specs")
def extract_junction_box_specs(specs: Dict, original: str) -> str:
    """Extract junction box specs (pairs, FO count)."""
    # Pairs: 10 Đôi
    pair_match = re.search(r'(\d+)\s*(?:Đôi|đôi|pair)', original, re.IGNORECASE)
    if pair_match:
        return f"{pair_match.group(1)} Đôi"
    # Fiber: 24 FO, 32FO
    fo_match = re.search(r'(\d+)\s*FO', original, re.IGNORECASE)
    if fo_match:
        return f"{fo_match.group(1)}FO"
    return 'Theo thiết kế'


@register("extract_cable_tray_specs")
def extract_cable_tray_specs(specs: Dict, original: str) -> str:
    """Extract cable tray dimensions (WxHxT)."""
    dim_match = re.search(
        r'(\d+)\s*[xX×]\s*(\d+)(?:\s*[xX×]\s*(\d+(?:\.\d+)?))?',
        original
    )
    if dim_match:
        w, h = dim_match.group(1), dim_match.group(2)
        t = dim_match.group(3)
        if t:
            return f"{w}x{h}x{t}"
        return f"{w}x{h}"
    return 'Theo thiết kế'


@register("extract_signal_cable_type")
def extract_signal_cable_type(specs: Dict, original: str) -> str:
    """Extract signal cable type (RS232, RS485, etc.)."""
    text_upper = original.upper()
    if 'RS232' in text_upper:
        return 'RS232'
    if 'RS485' in text_upper:
        return 'RS485'
    if 'MODBUS' in text_upper:
        return 'Modbus'
    return 'Theo thiết kế'
