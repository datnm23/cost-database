"""
Master Resource Dictionary - Data-driven configuration for all object types.

This dictionary replaces the 68 if-else blocks in _assemble() with
declarative configurations for each object type.

Benefits:
- Easy to extend: add new object type by adding dict entry
- Easy to maintain: logic is centralized
- Fewer bugs: unified configuration for all types
"""
from .field_mappings import ObjectConfig, FieldMapping


def _dict_to_field_mapping(d):
    """Convert a JSON dict back to a FieldMapping."""
    return FieldMapping(
        source=d.get('source', 'default'),
        key=d.get('key'),
        fallback=d.get('fallback', 'Theo thiết kế'),
        transform=d.get('transform'),
        combine=d.get('combine', []),
        separator=d.get('separator', ' '),
    )


def _dict_to_object_config(d):
    """Convert a JSON dict back to an ObjectConfig."""
    return ObjectConfig(
        object_name=d['object_name'],
        extractor=d.get('extractor'),
        output_object=d.get('output_object'),
        part1=_dict_to_field_mapping(d.get('part1', {})),
        part2=_dict_to_field_mapping(d.get('part2', {})),
        part3=_dict_to_field_mapping(d.get('part3', {})),
        aliases=d.get('aliases', []),
        defaults=d.get('defaults', {}),
    )


def _load_from_json():
    """Try to load master resource from JSON."""
    from .data_loader import load_master_resource
    raw = load_master_resource()
    return {name: _dict_to_object_config(cfg) for name, cfg in raw.items()}


_DATA_SOURCE = 'hardcoded'
try:
    MASTER_RESOURCE_DICTIONARY = _load_from_json()
    _DATA_SOURCE = 'json'
except Exception:
    pass

_HARDCODED_MASTER_RESOURCE = {
    # ==========================================================================
    # ELECTRICAL DEVICES
    # ==========================================================================
    "MCCB": ObjectConfig(
        object_name="MCCB",
        extractor="ElectricalExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="poles", fallback="Theo thiết kế"),
        part3=FieldMapping(source="computed", transform="combine_electrical_specs"),
    ),
    "MCB": ObjectConfig(
        object_name="MCB",
        extractor="ElectricalExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="poles", fallback="Theo thiết kế"),
        part3=FieldMapping(source="computed", transform="combine_electrical_specs"),
    ),
    "RCCB": ObjectConfig(
        object_name="RCCB",
        extractor="ElectricalExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="poles", fallback="Theo thiết kế"),
        part3=FieldMapping(source="computed", transform="combine_electrical_specs"),
    ),
    "ACB": ObjectConfig(
        object_name="ACB",
        extractor="ElectricalExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="poles", fallback="Theo thiết kế"),
        part3=FieldMapping(source="computed", transform="combine_electrical_specs"),
    ),
    "Công tơ điện": ObjectConfig(
        object_name="Công tơ điện",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="poles", fallback="Theo thiết kế"),
        part3=FieldMapping(source="spec", key="current", fallback="Theo thiết kế"),
    ),
    "Đèn báo pha": ObjectConfig(
        object_name="Đèn báo pha",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_colors"),
        part3=FieldMapping(source="spec", key="voltage", fallback="Theo thiết kế"),
    ),
    "Đèn tín hiệu": ObjectConfig(
        object_name="Đèn tín hiệu",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_signal_type"),
        part3=FieldMapping(source="computed", transform="extract_signal_colors"),
    ),
    "Thanh cái": ObjectConfig(
        object_name="Thanh cái",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_busbar_material"),
        part3=FieldMapping(source="computed", transform="extract_busbar_specs"),
    ),
    "Cầu chì": ObjectConfig(
        object_name="Cầu chì",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="fixed", key="Hạ thế"),
        part3=FieldMapping(source="computed", transform="extract_cau_chi_specs"),
    ),
    "Khóa chuyển mạch": ObjectConfig(
        object_name="Khóa chuyển mạch",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="switch_type", fallback="Ampe"),
        part3=FieldMapping(source="spec", key="current", fallback="Theo thiết kế"),
    ),
    "Công tắc": ObjectConfig(
        object_name="Công tắc",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_switch_specs"),
        part3=FieldMapping(source="fixed", key="Theo thiết kế"),
    ),
    "Công tắc hẹn giờ": ObjectConfig(
        object_name="Công tắc hẹn giờ",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="fixed", key="Công tắc"),
        part2=FieldMapping(source="fixed", key="Hẹn giờ"),
        part3=FieldMapping(source="fixed", key="Theo thiết kế"),
    ),
    "Công tắc nhiệt độ": ObjectConfig(
        object_name="Công tắc nhiệt độ",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="fixed", key="Công tắc"),
        part2=FieldMapping(source="fixed", key="Nhiệt độ (Thermostat)"),
        part3=FieldMapping(source="fixed", key="Theo thiết kế"),
    ),
    "Công tắc chọn": ObjectConfig(
        object_name="Công tắc chọn",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="fixed", key="Công tắc"),
        part2=FieldMapping(source="fixed", key="Chọn vùng"),
        part3=FieldMapping(source="fixed", key="Theo thiết kế"),
    ),
    "RCBO": ObjectConfig(
        object_name="RCBO",
        extractor="ElectricalExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="poles", fallback="Theo thiết kế"),
        part3=FieldMapping(source="computed", transform="combine_electrical_specs"),
    ),
    "Chống sét": ObjectConfig(
        object_name="Chống sét",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="fixed", key="Theo thiết kế"),
        part3=FieldMapping(source="fixed", key="Theo thiết kế"),
    ),
    "Chống sét lan truyền": ObjectConfig(
        object_name="Chống sét lan truyền",
        extractor="ElectricalExtractor",
        part1=FieldMapping(source="fixed", key="Chống sét lan truyền"),
        part2=FieldMapping(source="spec", key="poles", fallback="Theo thiết kế"),
        part3=FieldMapping(source="computed", transform="combine_electrical_specs"),
    ),
    "Máy biến áp": ObjectConfig(
        object_name="Máy biến áp",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_mep_power"),
        part3=FieldMapping(source="fixed", key="Theo thiết kế"),
    ),
    "Máy phát điện": ObjectConfig(
        object_name="Máy phát điện",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_mep_power"),
        part3=FieldMapping(source="fixed", key="Theo thiết kế"),
    ),
    "Máy điều hòa": ObjectConfig(
        object_name="Máy điều hòa",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_mep_power"),
        part3=FieldMapping(source="fixed", key="Theo thiết kế"),
    ),
    "ATS": ObjectConfig(
        object_name="ATS",
        extractor="ElectricalExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="poles", fallback="Theo thiết kế"),
        part3=FieldMapping(source="computed", transform="combine_electrical_specs"),
    ),
    "Tủ điều khiển ATS": ObjectConfig(
        object_name="Tủ điều khiển ATS",
        extractor="ElectricalExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="poles", fallback="Theo thiết kế"),
        part3=FieldMapping(source="computed", transform="combine_electrical_specs"),
    ),
    "Tủ điều khiển": ObjectConfig(
        object_name="Tủ điều khiển",
        extractor="ElectricalExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="poles", fallback="Theo thiết kế"),
        part3=FieldMapping(source="computed", transform="combine_electrical_specs"),
    ),
    "Quạt": ObjectConfig(
        object_name="Quạt",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_dimensions_wxh"),
        part3=FieldMapping(source="computed", transform="extract_mep_power"),
    ),
    "Quạt hướng trục": ObjectConfig(
        object_name="Quạt hướng trục",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_dimensions_wxh"),
        part3=FieldMapping(source="computed", transform="extract_mep_power"),
    ),
    "Quạt gắn tường": ObjectConfig(
        object_name="Quạt gắn tường",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_dimensions_wxh"),
        part3=FieldMapping(source="computed", transform="extract_mep_power"),
    ),
    "Quạt gió thải": ObjectConfig(
        object_name="Quạt gió thải",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_dimensions_wxh"),
        part3=FieldMapping(source="computed", transform="extract_mep_power"),
    ),
    "Quạt hút": ObjectConfig(
        object_name="Quạt hút",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_dimensions_wxh"),
        part3=FieldMapping(source="computed", transform="extract_mep_power"),
    ),
    "Quạt thông gió": ObjectConfig(
        object_name="Quạt thông gió",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_dimensions_wxh"),
        part3=FieldMapping(source="computed", transform="extract_mep_power"),
    ),
    "Camera": ObjectConfig(
        object_name="Camera",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_mep_type"),
        part3=FieldMapping(source="computed", transform="extract_camera_specs"),
    ),
    "Switch mạng": ObjectConfig(
        object_name="Switch mạng",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_switch_network_specs"),
        part3=FieldMapping(source="fixed", key="Theo thiết kế"),
    ),
    "Đầu ghi hình": ObjectConfig(
        object_name="Đầu ghi hình",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_dvr_specs"),
        part3=FieldMapping(source="fixed", key="Theo thiết kế"),
    ),
    "Loa": ObjectConfig(
        object_name="Loa",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_mep_type"),
        part3=FieldMapping(source="computed", transform="extract_mep_power"),
    ),
    "UPS": ObjectConfig(
        object_name="UPS",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_mep_power"),
        part3=FieldMapping(source="fixed", key="Theo thiết kế"),
    ),
    "Tủ rack": ObjectConfig(
        object_name="Tủ rack",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_rack_specs"),
        part3=FieldMapping(source="fixed", key="Theo thiết kế"),
    ),
    "Đồng hồ đa năng": ObjectConfig(
        object_name="Đồng hồ đa năng",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_accuracy_class"),
        part3=FieldMapping(source="computed", transform="extract_protocol"),
    ),
    "Đồng hồ điện": ObjectConfig(
        object_name="Đồng hồ điện",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_mep_power"),
        part3=FieldMapping(source="fixed", key="Theo thiết kế"),
    ),
    "Đồng hồ đo dòng": ObjectConfig(
        object_name="Đồng hồ đo dòng",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_ct_ratio"),
        part3=FieldMapping(source="fixed", key="Theo thiết kế"),
    ),
    "Đồng hồ đo áp": ObjectConfig(
        object_name="Đồng hồ đo áp",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_mep_power"),
        part3=FieldMapping(source="fixed", key="Theo thiết kế"),
    ),
    "Hộp đấu nối quang": ObjectConfig(
        object_name="Hộp đấu nối quang",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_junction_box_specs"),
        part3=FieldMapping(source="fixed", key="Theo thiết kế"),
    ),
    "Hộp nối cáp": ObjectConfig(
        object_name="Hộp nối cáp",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="fixed", key="Theo thiết kế"),
        part3=FieldMapping(source="fixed", key="Theo thiết kế"),
    ),
    "Máng cáp": ObjectConfig(
        object_name="Máng cáp",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_cable_tray_specs"),
        part3=FieldMapping(source="fixed", key="Theo thiết kế"),
    ),
    "Miệng gió": ObjectConfig(
        object_name="Miệng gió",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_dimensions_wxh"),
        part3=FieldMapping(source="fixed", key="Theo thiết kế"),
    ),
    "Ống gió": ObjectConfig(
        object_name="Ống gió",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_duct_material"),
        part3=FieldMapping(source="computed", transform="extract_dimensions_wxh"),
    ),
    "Fire Damper": ObjectConfig(
        object_name="Fire Damper",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_dimensions_wxh"),
        part3=FieldMapping(source="fixed", key="Theo thiết kế"),
    ),
    "Chuyển vuông tròn": ObjectConfig(
        object_name="Chuyển vuông tròn",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_dimensions_wxh"),
        part3=FieldMapping(source="computed", transform="extract_duct_material"),
    ),
    "Gót giày ống gió": ObjectConfig(
        object_name="Gót giày ống gió",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_dimensions_wxh"),
        part3=FieldMapping(source="computed", transform="extract_duct_material"),
    ),
    "Co ống gió": ObjectConfig(
        object_name="Co ống gió",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_dimensions_wxh"),
        part3=FieldMapping(source="computed", transform="extract_duct_material"),
    ),
    "Giảm ống gió": ObjectConfig(
        object_name="Giảm ống gió",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_dimensions_wxh"),
        part3=FieldMapping(source="computed", transform="extract_duct_material"),
    ),
    "Ống GI": ObjectConfig(
        object_name="Ống GI",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="fixed", key="Ống GI"),
        part2=FieldMapping(source="fixed", key="Mạ kẽm"),
        part3=FieldMapping(source="computed", transform="combine_pipe_specs"),
    ),
    "Ống Inox": ObjectConfig(
        object_name="Ống Inox",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="fixed", key="Ống Inox"),
        part2=FieldMapping(source="fixed", key="Inox"),
        part3=FieldMapping(source="computed", transform="combine_pipe_specs"),
    ),
    "Ống đồng": ObjectConfig(
        object_name="Ống đồng",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="fixed", key="Ống đồng"),
        part2=FieldMapping(source="fixed", key="Đồng"),
        part3=FieldMapping(source="computed", transform="combine_pipe_specs"),
    ),
    "Tủ điện": ObjectConfig(
        object_name="Tủ điện",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="type", fallback="Theo thiết kế"),
        part3=FieldMapping(source="spec", key="current", fallback="Theo thiết kế"),
    ),
    "Tủ gom công tơ": ObjectConfig(
        object_name="Tủ gom công tơ",
        output_object="Tủ điện",
        part1=FieldMapping(source="fixed", key="Tủ điện"),
        part2=FieldMapping(source="fixed", key="Tủ gom công tơ"),
        part3=FieldMapping(source="fixed", key=""),  # Empty - should result in 2-part output
    ),

    # ==========================================================================
    # EARTHWORK
    # ==========================================================================
    "Đào đất": ObjectConfig(
        object_name="Đào đất",
        extractor="EarthworkExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="soil_type", fallback="Đất cấp 3"),
        part3=FieldMapping(source="computed", transform="extract_dao_context"),
    ),
    "Đào": ObjectConfig(
        object_name="Đào",
        extractor="EarthworkExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="soil_type", fallback="Đất cấp 3"),
        part3=FieldMapping(source="computed", transform="extract_dao_context"),
    ),
    "Đào khuôn đường": ObjectConfig(
        object_name="Đào khuôn đường",
        extractor="EarthworkExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="soil_class", fallback="Đất cấp 3"),
        part3=FieldMapping(source="spec", key="method", fallback="Máy/Thủ công"),
    ),
    "Đào phá dỡ": ObjectConfig(
        object_name="Đào phá dỡ",
        extractor="EarthworkExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_dao_pha_do_context"),
        part3=FieldMapping(source="computed", transform="extract_dao_pha_do_position"),
    ),
    "Đắp đất": ObjectConfig(
        object_name="Đắp đất",
        extractor="EarthworkExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="compaction", fallback="Đất K95"),
        part3=FieldMapping(source="computed", transform="determine_earth_source"),
    ),
    "Đắp đất nền": ObjectConfig(
        object_name="Đắp đất nền",
        extractor="EarthworkExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="compaction", fallback="Đất K95"),
        part3=FieldMapping(source="computed", transform="determine_earth_source"),
    ),
    "Đắp đất hoàn trả": ObjectConfig(
        object_name="Đắp đất hoàn trả",
        extractor="EarthworkExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="compaction", fallback="Đất K95"),
        part3=FieldMapping(source="computed", transform="determine_earth_source"),
    ),
    "Đắp": ObjectConfig(
        object_name="Đắp",
        extractor="EarthworkExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="compaction", fallback="Đất K95"),
        part3=FieldMapping(source="computed", transform="determine_earth_source"),
    ),
    "Vận chuyển": ObjectConfig(
        object_name="Vận chuyển",
        extractor="EarthworkExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="material", fallback="Đất"),
        part3=FieldMapping(source="computed", transform="extract_transport_destination"),
    ),

    # ==========================================================================
    # ROAD CONSTRUCTION
    # ==========================================================================
    "Móng đường": ObjectConfig(
        object_name="Móng đường",
        extractor="RoadExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="material", fallback="CPĐD"),
        part3=FieldMapping(source="computed", transform="combine_layer_compaction"),
    ),
    "Tưới nhựa": ObjectConfig(
        object_name="Tưới nhựa",
        extractor="RoadExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="type", fallback="Thấm bám"),
        part3=FieldMapping(source="computed", transform="extract_tuoi_nhua_dosage"),
    ),
    "Mặt đường": ObjectConfig(
        object_name="Mặt đường",
        extractor="RoadExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="format_asphalt_grade"),
        part3=FieldMapping(source="computed", transform="extract_asphalt_thickness"),
    ),
    "Rải thảm": ObjectConfig(
        object_name="Rải thảm",
        extractor="RoadExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="format_asphalt_grade"),
        part3=FieldMapping(source="computed", transform="extract_asphalt_thickness"),
    ),

    # ==========================================================================
    # FORMWORK
    # ==========================================================================
    "Ván khuôn": ObjectConfig(
        object_name="Ván khuôn",
        extractor="FormworkExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="position", fallback="Theo thiết kế"),
        part3=FieldMapping(source="spec", key="type", fallback="Theo thiết kế"),
    ),

    # ==========================================================================
    # CONCRETE
    # ==========================================================================
    "Bê tông lót": ObjectConfig(
        object_name="Bê tông lót",
        extractor="ConcreteExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="grade", fallback="M100"),
        part3=FieldMapping(source="spec", key="stone", fallback="Đá 1x2"),
    ),
    "Bê tông mặt đường": ObjectConfig(
        object_name="Bê tông mặt đường",
        extractor="ConcreteExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="grade", fallback="M250"),
        part3=FieldMapping(source="spec", key="stone", fallback="Đá 1x2"),
    ),
    "Bê tông vỉa hè": ObjectConfig(
        object_name="Bê tông vỉa hè",
        extractor="ConcreteExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="grade", fallback="M200"),
        part3=FieldMapping(source="spec", key="stone", fallback="Đá 1x2"),
    ),
    "Bê tông": ObjectConfig(
        object_name="Bê tông",
        extractor="ConcreteExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="grade", fallback="M250"),
        part3=FieldMapping(source="spec", key="stone", fallback="Đá 1x2"),
    ),

    # ==========================================================================
    # PRECAST COMPONENTS
    # ==========================================================================
    "Bó vỉa": ObjectConfig(
        object_name="Bó vỉa",
        extractor="PrecastExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="material", fallback="Đá tự nhiên"),
        part3=FieldMapping(source="computed", transform="extract_bo_via_specs"),
    ),
    "Tấm đan": ObjectConfig(
        object_name="Tấm đan",
        extractor="PrecastExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="material", fallback="Đá"),
        part3=FieldMapping(source="computed", transform="convert_cm_to_mm_dimensions"),
    ),
    "Tấm đan rãnh": ObjectConfig(
        object_name="Tấm đan rãnh",
        extractor="PrecastExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="material", fallback="Đá"),
        part3=FieldMapping(source="computed", transform="convert_cm_to_mm_dimensions"),
    ),
    "Tấm lát mái": ObjectConfig(
        object_name="Tấm lát mái",
        extractor="PrecastExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="fixed", key="Bê tông đúc sẵn"),
        part3=FieldMapping(source="spec", key="dimensions", fallback="Theo thiết kế"),
    ),
    "Cống hộp": ObjectConfig(
        object_name="Cống hộp",
        extractor="PrecastExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="material", fallback="BTCT"),
        part3=FieldMapping(source="computed", transform="extract_cong_hop_specs"),
    ),
    "Cống thoát nước": ObjectConfig(
        object_name="Cống thoát nước",
        extractor="PrecastExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="material", fallback="BTCT"),
        part3=FieldMapping(source="computed", transform="combine_cong_thoat_nuoc_specs"),
    ),
    "Cống tròn": ObjectConfig(
        object_name="Cống tròn",
        extractor="PrecastExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="material", fallback="BTCT"),
        part3=FieldMapping(source="spec", key="diameter", fallback="Theo thiết kế"),
    ),
    "Hố ga": ObjectConfig(
        object_name="Hố ga",
        extractor="PrecastExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="material", fallback="BTCT"),
        part3=FieldMapping(source="spec", key="dimensions", fallback="Theo thiết kế"),
    ),
    "Rãnh thoát nước": ObjectConfig(
        object_name="Rãnh thoát nước",
        extractor="PrecastExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="material", fallback="BTCT"),
        part3=FieldMapping(source="spec", key="dimensions", fallback="Theo thiết kế"),
    ),

    # ==========================================================================
    # PIPE FITTINGS
    # ==========================================================================
    "Cút": ObjectConfig(
        object_name="Cút",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_pipe_fitting_material"),
        part3=FieldMapping(source="computed", transform="combine_pipe_fitting_specs"),
    ),
    "Cút 45 độ": ObjectConfig(
        object_name="Cút 45 độ",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_pipe_fitting_material"),
        part3=FieldMapping(source="computed", transform="combine_pipe_fitting_specs"),
    ),
    "Cút 90 độ": ObjectConfig(
        object_name="Cút 90 độ",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_pipe_fitting_material"),
        part3=FieldMapping(source="computed", transform="combine_pipe_fitting_specs"),
    ),
    "Chếch": ObjectConfig(
        object_name="Chếch",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_pipe_fitting_material"),
        part3=FieldMapping(source="computed", transform="combine_pipe_fitting_specs"),
    ),
    "Chếch 45 độ": ObjectConfig(
        object_name="Chếch 45 độ",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_pipe_fitting_material"),
        part3=FieldMapping(source="computed", transform="combine_pipe_fitting_specs"),
    ),
    "Tê": ObjectConfig(
        object_name="Tê",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_pipe_fitting_material"),
        part3=FieldMapping(source="computed", transform="combine_pipe_fitting_specs"),
    ),
    "Tê đều": ObjectConfig(
        object_name="Tê đều",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_pipe_fitting_material"),
        part3=FieldMapping(source="computed", transform="combine_pipe_fitting_specs"),
    ),
    "Tê thu": ObjectConfig(
        object_name="Tê thu",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_pipe_fitting_material"),
        part3=FieldMapping(source="computed", transform="combine_pipe_fitting_specs"),
    ),
    "Tê hàn": ObjectConfig(
        object_name="Tê hàn",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_pipe_fitting_material"),
        part3=FieldMapping(source="computed", transform="combine_pipe_fitting_specs"),
    ),
    "Côn": ObjectConfig(
        object_name="Côn",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_pipe_fitting_material"),
        part3=FieldMapping(source="computed", transform="combine_pipe_fitting_specs"),
    ),
    "Côn thu": ObjectConfig(
        object_name="Côn thu",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_pipe_fitting_material"),
        part3=FieldMapping(source="computed", transform="combine_pipe_fitting_specs"),
    ),
    "Y thu": ObjectConfig(
        object_name="Y thu",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_pipe_fitting_material"),
        part3=FieldMapping(source="computed", transform="combine_pipe_fitting_specs"),
    ),
    "Măng sông": ObjectConfig(
        object_name="Măng sông",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_pipe_fitting_material"),
        part3=FieldMapping(source="computed", transform="combine_pipe_fitting_specs"),
    ),
    "Măng sông ren trong": ObjectConfig(
        object_name="Măng sông ren trong",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_pipe_fitting_material"),
        part3=FieldMapping(source="computed", transform="combine_pipe_fitting_specs"),
    ),
    "Măng sông nối ống": ObjectConfig(
        object_name="Măng sông nối ống",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_pipe_fitting_material"),
        part3=FieldMapping(source="computed", transform="combine_pipe_fitting_specs"),
    ),
    "Rắc co": ObjectConfig(
        object_name="Rắc co",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_pipe_fitting_material"),
        part3=FieldMapping(source="computed", transform="combine_pipe_fitting_specs"),
    ),
    "Rắc co ren ngoài": ObjectConfig(
        object_name="Rắc co ren ngoài",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_pipe_fitting_material"),
        part3=FieldMapping(source="computed", transform="combine_pipe_fitting_specs"),
    ),
    "Nút bịt": ObjectConfig(
        object_name="Nút bịt",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_pipe_fitting_material"),
        part3=FieldMapping(source="computed", transform="combine_pipe_fitting_specs"),
    ),
    "Đầu bịt": ObjectConfig(
        object_name="Đầu bịt",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_pipe_fitting_material"),
        part3=FieldMapping(source="computed", transform="combine_pipe_fitting_specs"),
    ),
    "Đầu bịt/Nút bịt": ObjectConfig(
        object_name="Đầu bịt/Nút bịt",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_pipe_fitting_material"),
        part3=FieldMapping(source="computed", transform="combine_pipe_fitting_specs"),
    ),
    "Đai khởi thủy": ObjectConfig(
        object_name="Đai khởi thủy",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_pipe_fitting_material"),
        part3=FieldMapping(source="computed", transform="combine_pipe_fitting_specs"),
    ),
    "Nút loe": ObjectConfig(
        object_name="Nút loe",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_pipe_fitting_material"),
        part3=FieldMapping(source="computed", transform="combine_pipe_fitting_specs"),
    ),
    "Đầu nối ren ngoài": ObjectConfig(
        object_name="Đầu nối ren ngoài",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_pipe_fitting_material"),
        part3=FieldMapping(source="computed", transform="combine_pipe_fitting_specs"),
    ),
    "Mặt bích (Bích hàn)": ObjectConfig(
        object_name="Mặt bích (Bích hàn)",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_pipe_fitting_material"),
        part3=FieldMapping(source="computed", transform="combine_pipe_fitting_specs"),
    ),
    "Khớp nối mềm": ObjectConfig(
        object_name="Khớp nối mềm",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="connection", fallback="EE"),
        part3=FieldMapping(source="spec", key="diameter", fallback="Theo thiết kế"),
    ),

    # ==========================================================================
    # VALVES
    # ==========================================================================
    "Van khóa tay gạt": ObjectConfig(
        object_name="Van khóa tay gạt",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="fixed", key="Đồng"),  # Default material is Đồng
        part3=FieldMapping(source="computed", transform="extract_valve_specs"),
    ),
    "Van cổng": ObjectConfig(
        object_name="Van cổng",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_valve_connection"),
        part3=FieldMapping(source="computed", transform="extract_valve_specs"),
    ),
    "Van 1 chiều": ObjectConfig(
        object_name="Van 1 chiều",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_valve_connection"),
        part3=FieldMapping(source="computed", transform="extract_valve_specs"),
    ),
    "Van bướm": ObjectConfig(
        object_name="Van bướm",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_valve_connection"),
        part3=FieldMapping(source="computed", transform="extract_valve_specs"),
    ),
    "Van góc": ObjectConfig(
        object_name="Van góc",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_valve_connection"),
        part3=FieldMapping(source="computed", transform="extract_valve_specs"),
    ),
    "Van bi rắc co đôi": ObjectConfig(
        object_name="Van bi rắc co đôi",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_valve_connection"),
        part3=FieldMapping(source="computed", transform="extract_valve_specs_with_handle"),
    ),
    "Van bi": ObjectConfig(
        object_name="Van bi",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_valve_connection"),
        part3=FieldMapping(source="computed", transform="extract_valve_specs_with_handle"),
    ),
    "Van báo động (Alarm Valve)": ObjectConfig(
        object_name="Van báo động (Alarm Valve)",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="material", fallback="Gang"),
        part3=FieldMapping(source="spec", key="diameter", fallback="Theo thiết kế"),
    ),

    # ==========================================================================
    # PUMPS
    # ==========================================================================
    "Bơm chữa cháy": ObjectConfig(
        object_name="Bơm chữa cháy",
        extractor="PumpExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_pump_type"),
        part3=FieldMapping(source="computed", transform="combine_pump_specs"),
    ),
    "Bơm bù áp": ObjectConfig(
        object_name="Bơm bù áp",
        extractor="PumpExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_pump_type"),
        part3=FieldMapping(source="computed", transform="combine_pump_specs"),
    ),
    "Bơm chìm nước thải": ObjectConfig(
        object_name="Bơm chìm nước thải",
        extractor="PumpExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_pump_type"),
        part3=FieldMapping(source="computed", transform="combine_pump_specs"),
    ),
    "Bơm nước": ObjectConfig(
        object_name="Bơm nước",
        extractor="PumpExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_pump_type"),
        part3=FieldMapping(source="computed", transform="combine_pump_specs"),
    ),
    "Bơm": ObjectConfig(
        object_name="Bơm",
        extractor="PumpExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_pump_type"),
        part3=FieldMapping(source="computed", transform="combine_pump_specs"),
    ),
    "Bình tích áp": ObjectConfig(
        object_name="Bình tích áp",
        extractor="PumpExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="type", fallback="Đứng"),
        part3=FieldMapping(source="computed", transform="combine_pressure_tank_specs"),
    ),

    # ==========================================================================
    # PIPES
    # ==========================================================================
    "Ống HDPE": ObjectConfig(
        object_name="Ống HDPE",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="computed", transform="determine_pipe_object"),
        part2=FieldMapping(source="computed", transform="extract_pipe_material"),
        part3=FieldMapping(source="computed", transform="combine_pipe_specs"),
    ),
    "Ống uPVC": ObjectConfig(
        object_name="Ống uPVC",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="computed", transform="determine_pipe_object"),
        part2=FieldMapping(source="computed", transform="extract_pipe_material"),
        part3=FieldMapping(source="computed", transform="combine_pipe_specs"),
    ),
    "Ống PVC": ObjectConfig(
        object_name="Ống PVC",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="computed", transform="determine_pipe_object"),
        part2=FieldMapping(source="computed", transform="extract_pipe_material"),
        part3=FieldMapping(source="computed", transform="combine_pipe_specs"),
    ),
    "Ống PPR": ObjectConfig(
        object_name="Ống PPR",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="computed", transform="determine_pipe_object"),
        part2=FieldMapping(source="computed", transform="extract_pipe_material"),
        part3=FieldMapping(source="computed", transform="combine_pipe_specs"),
    ),
    "Ống thép": ObjectConfig(
        object_name="Ống thép",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="fixed", key="Ống thép"),
        part2=FieldMapping(source="computed", transform="extract_pipe_material"),
        part3=FieldMapping(source="computed", transform="combine_pipe_specs"),
    ),
    "Ống luồn dây": ObjectConfig(
        object_name="Ống luồn dây",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="fixed", key="Ống luồn dây"),
        part2=FieldMapping(source="computed", transform="extract_pipe_material"),
        part3=FieldMapping(source="computed", transform="combine_pipe_specs"),
    ),
    "Ống nhựa": ObjectConfig(
        object_name="Ống nhựa",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="computed", transform="determine_pipe_object"),
        part2=FieldMapping(source="computed", transform="extract_pipe_material"),
        part3=FieldMapping(source="computed", transform="combine_pipe_specs"),
    ),
    "Ống": ObjectConfig(
        object_name="Ống",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="computed", transform="determine_pipe_object"),
        part2=FieldMapping(source="computed", transform="extract_pipe_material"),
        part3=FieldMapping(source="computed", transform="combine_pipe_specs"),
    ),

    # ==========================================================================
    # TRAFFIC SIGNS
    # ==========================================================================
    "Biển báo": ObjectConfig(
        object_name="Biển báo",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_sign_type"),
        part3=FieldMapping(source="computed", transform="extract_sign_specs"),
    ),

    # ==========================================================================
    # MEP EQUIPMENT
    # ==========================================================================
    "Cột đèn": ObjectConfig(
        object_name="Cột đèn",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="pole_type", fallback="Bát giác côn"),
        part3=FieldMapping(source="computed", transform="extract_cot_den_specs"),
    ),
    "Đèn chiếu sáng": ObjectConfig(
        object_name="Đèn chiếu sáng",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_den_chieu_sang_fixture"),
        part3=FieldMapping(source="computed", transform="extract_den_chieu_sang_specs"),
    ),
    "Cọc tiếp địa": ObjectConfig(
        object_name="Cọc tiếp địa",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="profile", fallback="Thép"),
        part3=FieldMapping(source="computed", transform="extract_coc_tiep_dia_length"),
    ),
    "Nắp hố ga": ObjectConfig(
        object_name="Nắp hố ga",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_nap_ho_ga_material"),
        part3=FieldMapping(source="computed", transform="extract_nap_ho_ga_specs"),
    ),
    "Song chắn rác": ObjectConfig(
        object_name="Song chắn rác",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_song_chan_rac_material"),
        part3=FieldMapping(source="computed", transform="extract_song_chan_rac_specs"),
    ),
    "Cáp điện": ObjectConfig(
        object_name="Cáp điện",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="cable_type", fallback="Cu/XLPE/PVC"),
        part3=FieldMapping(source="spec", key="cable_size", fallback="Theo thiết kế"),
    ),
    "Cáp trung thế": ObjectConfig(
        object_name="Cáp trung thế",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="cable_type", fallback="Cu/XLPE/PVC"),
        part3=FieldMapping(source="spec", key="cable_size", fallback="Theo thiết kế"),
    ),
    "Cáp hạ thế": ObjectConfig(
        object_name="Cáp hạ thế",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="cable_type", fallback="Cu/XLPE/PVC"),
        part3=FieldMapping(source="spec", key="cable_size", fallback="Theo thiết kế"),
    ),
    "Cốt thép": ObjectConfig(
        object_name="Cốt thép",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="fixed", key="Theo thiết kế"),
        part3=FieldMapping(source="computed", transform="extract_rebar_size"),
    ),
    "Trụ cứu hỏa": ObjectConfig(
        object_name="Trụ cứu hỏa",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="material", fallback="Gang"),
        part3=FieldMapping(source="spec", key="diameter", fallback="Theo thiết kế"),
    ),
    "Bình chữa cháy": ObjectConfig(
        object_name="Bình chữa cháy",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="ext_type", fallback="Theo thiết kế"),
        part3=FieldMapping(source="computed", transform="extract_binh_chua_chay_model"),
    ),
    "Hộp đựng bình chữa cháy": ObjectConfig(
        object_name="Hộp đựng bình chữa cháy",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="fixed", key="Thép sơn tĩnh điện"),
        part3=FieldMapping(source="fixed", key="Theo thiết kế"),
    ),
    "Lò xo giảm chấn": ObjectConfig(
        object_name="Lò xo giảm chấn",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="fixed", key="Thép/Cao su"),
        part3=FieldMapping(source="computed", transform="extract_lo_xo_purpose"),
    ),
    "Chậu rửa": ObjectConfig(
        object_name="Chậu rửa",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="material", fallback="Theo thiết kế"),
        part3=FieldMapping(source="fixed", key="Theo thiết kế"),
    ),
    "Bồn dầu": ObjectConfig(
        object_name="Bồn dầu",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="capacity", fallback="Theo thiết kế"),
        part3=FieldMapping(source="fixed", key="Theo thiết kế"),
    ),
    "Họng tiếp dầu": ObjectConfig(
        object_name="Họng tiếp dầu",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="fixed", key="Theo thiết kế"),
        part3=FieldMapping(source="fixed", key="Theo thiết kế"),
    ),
    "Phụ kiện ACB": ObjectConfig(
        object_name="Phụ kiện ACB",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="fixed", key="Theo thiết kế"),
        part3=FieldMapping(source="fixed", key="Theo thiết kế"),
    ),
    "Phụ kiện MCCB": ObjectConfig(
        object_name="Phụ kiện MCCB",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="fixed", key="Theo thiết kế"),
        part3=FieldMapping(source="fixed", key="Theo thiết kế"),
    ),
    "Rơ le thời gian": ObjectConfig(
        object_name="Rơ le thời gian",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="fixed", key="Theo thiết kế"),
        part3=FieldMapping(source="fixed", key="Theo thiết kế"),
    ),
    "Bàn gọi PA": ObjectConfig(
        object_name="Bàn gọi PA",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_mep_type"),
        part3=FieldMapping(source="fixed", key="Theo thiết kế"),
    ),
    "Hộp đấu nối": ObjectConfig(
        object_name="Hộp đấu nối",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_junction_box_specs"),
        part3=FieldMapping(source="fixed", key="Theo thiết kế"),
    ),
    "Cáp tín hiệu": ObjectConfig(
        object_name="Cáp tín hiệu",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_signal_cable_type"),
        part3=FieldMapping(source="computed", transform="extract_cable_size"),
    ),
    "Contactor": ObjectConfig(
        object_name="Contactor",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_contactor_specs"),
        part3=FieldMapping(source="fixed", key="Theo thiết kế"),
    ),
    "Biến dòng (CT)": ObjectConfig(
        object_name="Biến dòng (CT)",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_ct_ratio"),
        part3=FieldMapping(source="computed", transform="extract_ct_class"),
    ),
    "Biến tần (VSD)": ObjectConfig(
        object_name="Biến tần (VSD)",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_vsd_specs"),
        part3=FieldMapping(source="fixed", key="Theo thiết kế"),
    ),
    "Đồng hồ nước": ObjectConfig(
        object_name="Đồng hồ nước",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="diameter", fallback="Theo thiết kế"),
        part3=FieldMapping(source="fixed", key="Theo thiết kế"),
    ),
    "Hộp đồng hồ": ObjectConfig(
        object_name="Hộp đồng hồ",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="material", fallback="Inox"),
        part3=FieldMapping(source="computed", transform="extract_hop_dong_ho_dims"),
    ),
    "Cụm van quản lý": ObjectConfig(
        object_name="Cụm van quản lý",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="fixed", key="Theo thiết kế"),
        part3=FieldMapping(source="fixed", key="Trọn bộ"),
    ),
    "Cụm van xả khí": ObjectConfig(
        object_name="Cụm van xả khí",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="fixed", key="Theo thiết kế"),
        part3=FieldMapping(source="fixed", key="Trọn bộ"),
    ),
    "Gối đỡ ống": ObjectConfig(
        object_name="Gối đỡ ống",
        extractor="PipeFittingExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="fixed", key="Bê tông/Composite"),
        part3=FieldMapping(source="fixed", key="Theo thiết kế"),
    ),

    # ==========================================================================
    # MATERIALS
    # ==========================================================================
    "Cọc tre": ObjectConfig(
        object_name="Cọc tre",
        extractor="EarthworkExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="purpose", fallback="Gia cố nền"),
        part3=FieldMapping(source="computed", transform="extract_coc_tre_spec"),
    ),
    "Vải địa kỹ thuật": ObjectConfig(
        object_name="Vải địa kỹ thuật",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="fixed", key="Không dệt"),
        part3=FieldMapping(source="fixed", key="Theo thiết kế"),
    ),
    "Nilon": ObjectConfig(
        object_name="Nilon",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_nilon_type"),
        part3=FieldMapping(source="computed", transform="extract_nilon_purpose"),
    ),
    "Đất màu": ObjectConfig(
        object_name="Đất màu",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="fixed", key="Trồng cây"),
        part3=FieldMapping(source="fixed", key="Theo thiết kế"),
    ),
    "Đá hộc": ObjectConfig(
        object_name="Đá hộc",
        extractor="PrecastExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_da_hoc_type"),
        part3=FieldMapping(source="spec", key="dimensions", fallback="Theo thiết kế"),
    ),
    "Đá dăm": ObjectConfig(
        object_name="Đá dăm",
        extractor="PrecastExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_da_dam_purpose"),
        part3=FieldMapping(source="spec", key="dimensions", fallback="Theo thiết kế"),
    ),
    "Thang thép": ObjectConfig(
        object_name="Thang thép",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="fixed", key="Thép hình"),
        part3=FieldMapping(source="fixed", key="Theo thiết kế"),
    ),

    # ==========================================================================
    # FINISHING WORK
    # ==========================================================================
    "Trát": ObjectConfig(
        object_name="Trát",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_trat_mortar"),
        part3=FieldMapping(source="computed", transform="extract_trat_position"),
    ),
    "Láng": ObjectConfig(
        object_name="Láng",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_trat_mortar"),
        part3=FieldMapping(source="computed", transform="extract_trat_position"),
    ),
    "Chèn vữa": ObjectConfig(
        object_name="Chèn vữa",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_trat_mortar"),
        part3=FieldMapping(source="computed", transform="extract_trat_position"),
    ),
    "Xây gạch": ObjectConfig(
        object_name="Xây gạch",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="material", fallback="Gạch đặc M75"),
        part3=FieldMapping(source="computed", transform="extract_xay_gach_position"),
    ),
    "Xây đá": ObjectConfig(
        object_name="Xây đá",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="spec", key="material", fallback="Đá hộc"),
        part3=FieldMapping(source="spec", key="mortar", fallback="Vữa M100"),
    ),
    "Xây bể cáp": ObjectConfig(
        object_name="Xây bể cáp",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="fixed", key="Gạch"),
        part3=FieldMapping(source="fixed", key="Theo thiết kế"),
    ),
    "Xây tường": ObjectConfig(
        object_name="Xây tường",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="fixed", key="Đá/Gạch"),
        part3=FieldMapping(source="computed", transform="extract_xay_tuong_type"),
    ),
    "Trồng cỏ": ObjectConfig(
        object_name="Trồng cỏ",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_trong_co_position"),
        part3=FieldMapping(source="computed", transform="extract_trong_co_care"),
    ),

    # ==========================================================================
    # STRUCTURAL
    # ==========================================================================
    "Cửa xả": ObjectConfig(
        object_name="Cửa xả",
        extractor="PrecastExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="fixed", key="Bê tông cốt thép"),
        part3=FieldMapping(source="fixed", key="Theo thiết kế"),
    ),
    "Móng trụ": ObjectConfig(
        object_name="Móng trụ",
        extractor="ConcreteExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="fixed", key="Bê tông cốt thép"),
        part3=FieldMapping(source="computed", transform="extract_mong_tru_purpose"),
    ),
    "Khung móng": ObjectConfig(
        object_name="Khung móng",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="fixed", key="Thép"),
        part3=FieldMapping(source="computed", transform="extract_khung_mong_specs"),
    ),
    "Bệ tủ": ObjectConfig(
        object_name="Bệ tủ",
        extractor="ConcreteExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="fixed", key="Bê tông"),
        part3=FieldMapping(source="computed", transform="extract_be_tu_purpose"),
    ),

    # ==========================================================================
    # COSTS / AUXILIARY
    # ==========================================================================
    "Chi phí": ObjectConfig(
        object_name="Chi phí",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_chi_phi_type"),
        part3=FieldMapping(source="computed", transform="extract_chi_phi_scope"),
    ),
    "Vật tư phụ": ObjectConfig(
        object_name="Vật tư phụ",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="fixed", key="Đấu nối tủ điện"),
        part3=FieldMapping(source="fixed", key="Trọn gói"),
    ),
    "Bản quan trắc": ObjectConfig(
        object_name="Bản quan trắc",
        extractor="MEPEquipmentExtractor",
        part1=FieldMapping(source="object_name"),
        part2=FieldMapping(source="computed", transform="extract_quan_trac_type"),
        part3=FieldMapping(source="fixed", key="Trọn bộ"),
    ),
}

if _DATA_SOURCE == 'hardcoded':
    MASTER_RESOURCE_DICTIONARY = _HARDCODED_MASTER_RESOURCE


# Build aliases lookup for faster access
ALIAS_LOOKUP = {}
for obj_name, config in MASTER_RESOURCE_DICTIONARY.items():
    for alias in config.aliases:
        ALIAS_LOOKUP[alias] = obj_name


def get_config(object_name: str) -> ObjectConfig:
    """Get configuration for an object type, including alias lookup."""
    if object_name in MASTER_RESOURCE_DICTIONARY:
        return MASTER_RESOURCE_DICTIONARY[object_name]
    if object_name in ALIAS_LOOKUP:
        return MASTER_RESOURCE_DICTIONARY[ALIAS_LOOKUP[object_name]]
    return None


VALID_SOURCES = {"object_name", "fixed", "spec", "computed", "default"}

VALID_EXTRACTORS = {
    "FormworkExtractor", "RoadExtractor", "PrecastExtractor",
    "ElectricalExtractor", "EarthworkExtractor", "ConcreteExtractor",
    "PipeFittingExtractor", "PumpExtractor", "MEPEquipmentExtractor",
}


def validate_configs():
    """
    Validate all ObjectConfigs at startup.

    Checks:
    - All transform names in FieldMappings exist in TRANSFORMS registry
    - All extractor references resolve to known extractor classes
    - All source values are valid
    - FieldMappings with source="spec" have a key
    - FieldMappings with source="computed" have a transform

    Raises:
        ValueError: If any config is invalid, with details about all errors found
    """
    from .transforms import TRANSFORMS

    errors = []

    for obj_name, config in MASTER_RESOURCE_DICTIONARY.items():
        # Validate extractor reference
        if config.extractor and config.extractor not in VALID_EXTRACTORS:
            errors.append(
                f"[{obj_name}] Unknown extractor: '{config.extractor}'"
            )

        # Validate each part's FieldMapping
        for part_name in ('part1', 'part2', 'part3'):
            mapping = getattr(config, part_name)
            prefix = f"[{obj_name}.{part_name}]"

            # Validate source
            if mapping.source not in VALID_SOURCES:
                errors.append(
                    f"{prefix} Invalid source: '{mapping.source}'"
                )

            # Validate computed has transform
            if mapping.source == "computed":
                if not mapping.transform:
                    errors.append(
                        f"{prefix} source='computed' but no transform specified"
                    )
                elif mapping.transform not in TRANSFORMS:
                    errors.append(
                        f"{prefix} Unknown transform: '{mapping.transform}'"
                    )

            # Validate spec has key
            if mapping.source == "spec" and not mapping.key:
                errors.append(
                    f"{prefix} source='spec' but no key specified"
                )

    if errors:
        error_msg = "ObjectConfig validation errors:\n" + "\n".join(f"  - {e}" for e in errors)
        raise ValueError(error_msg)

    return True
