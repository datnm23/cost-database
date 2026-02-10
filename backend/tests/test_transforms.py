"""
Unit tests for transform functions.

Tests representative transforms from each category plus edge cases
(empty specs, missing keys, None values).
"""
import pytest
from app.services.dictionaries.transforms import TRANSFORMS


class TestTransformRegistry:
    """Verify all transforms are registered."""

    def test_all_transforms_registered(self):
        assert len(TRANSFORMS) == 87

    def test_each_transform_is_callable(self):
        for name, func in TRANSFORMS.items():
            assert callable(func), f"Transform '{name}' is not callable"


class TestElectricalTransforms:
    """Tests for electrical domain transforms."""

    def test_combine_electrical_specs_both(self):
        specs = {'amps': '100A', 'breaking_capacity': '25kA'}
        assert TRANSFORMS['combine_electrical_specs'](specs, '') == '100A 25kA'

    def test_combine_electrical_specs_amps_only(self):
        specs = {'amps': '63A'}
        assert TRANSFORMS['combine_electrical_specs'](specs, '') == '63A'

    def test_combine_electrical_specs_empty(self):
        assert TRANSFORMS['combine_electrical_specs']({}, '') == 'Theo thiết kế'

    def test_extract_busbar_material_dong(self):
        assert TRANSFORMS['extract_busbar_material']({}, 'Thanh cái đồng 400A') == 'Đồng'

    def test_extract_busbar_material_nhom(self):
        assert TRANSFORMS['extract_busbar_material']({}, 'Thanh cái nhôm') == 'Nhôm'

    def test_extract_busbar_material_unknown(self):
        assert TRANSFORMS['extract_busbar_material']({}, 'Thanh cái') == 'Theo thiết kế'

    def test_extract_busbar_specs_current(self):
        specs = {'current': '400A'}
        assert TRANSFORMS['extract_busbar_specs'](specs, '') == '400A'

    def test_extract_busbar_specs_dimensions(self):
        specs = {'dimensions': '100x10mm'}
        assert TRANSFORMS['extract_busbar_specs'](specs, '') == '100x10mm'

    def test_extract_busbar_specs_empty(self):
        assert TRANSFORMS['extract_busbar_specs']({}, '') == 'Theo thiết kế'

    def test_extract_colors_multiple(self):
        result = TRANSFORMS['extract_colors']({}, 'Đèn đỏ vàng xanh')
        assert 'Đỏ' in result
        assert 'Vàng' in result
        assert 'Xanh' in result

    def test_extract_colors_from_specs(self):
        specs = {'colors': 'RGB'}
        assert TRANSFORMS['extract_colors'](specs, 'Đèn đỏ') == 'RGB'

    def test_extract_colors_empty(self):
        assert TRANSFORMS['extract_colors']({}, 'Đèn báo') == 'Theo thiết kế'

    def test_extract_signal_type_bao_pha(self):
        assert TRANSFORMS['extract_signal_type']({}, 'Đèn báo pha 3 pha') == 'Báo pha'

    def test_extract_signal_type_giao_thong(self):
        assert TRANSFORMS['extract_signal_type']({}, 'Đèn giao thông') == 'Giao thông'

    def test_extract_signal_type_unknown(self):
        assert TRANSFORMS['extract_signal_type']({}, 'Đèn') == 'Theo thiết kế'

    def test_extract_signal_colors_voltage_fallback(self):
        specs = {'voltage': '220V'}
        assert TRANSFORMS['extract_signal_colors'](specs, 'Đèn báo') == '220V'


class TestRoadEarthworkTransforms:
    """Tests for road/earthwork domain transforms."""

    def test_combine_layer_compaction(self):
        specs = {'compaction': 'K98'}
        result = TRANSFORMS['combine_layer_compaction'](specs, 'CPĐD loại 1')
        assert 'Lớp trên' in result
        assert 'K98' in result

    def test_combine_layer_compaction_empty(self):
        assert TRANSFORMS['combine_layer_compaction']({}, 'ABC') == 'Theo thiết kế'

    def test_determine_earth_source_tan_dung(self):
        assert TRANSFORMS['determine_earth_source']({}, 'Đất, cát tận dụng') == 'Tận dụng'

    def test_determine_earth_source_mua_moi(self):
        assert TRANSFORMS['determine_earth_source']({}, 'Đắp đất mua mới') == 'Mua mới'

    def test_determine_earth_source_default(self):
        assert TRANSFORMS['determine_earth_source']({}, 'Đắp đất') == 'Mua mới'

    def test_determine_earth_source_from_specs(self):
        specs = {'source': 'Tận dụng nội bộ'}
        assert TRANSFORMS['determine_earth_source'](specs, '') == 'Tận dụng'

    def test_extract_transport_destination_noi_bo(self):
        result = TRANSFORMS['extract_transport_destination']({}, 'Vận chuyển nội bộ dự án')
        assert result == 'Nội bộ dự án'

    def test_extract_transport_destination_bai_do(self):
        result = TRANSFORMS['extract_transport_destination']({}, 'Vận chuyển ra bãi đổ')
        assert result == 'Ra bãi thải'

    def test_extract_dao_context_from_specs(self):
        specs = {'context': 'Hố móng'}
        assert TRANSFORMS['extract_dao_context'](specs, '') == 'Hố móng'

    def test_extract_dao_context_empty(self):
        assert TRANSFORMS['extract_dao_context']({}, '') == 'Theo thiết kế'

    def test_format_asphalt_grade_with_grade(self):
        specs = {'asphalt_grade': 'C19'}
        assert TRANSFORMS['format_asphalt_grade'](specs, '') == 'Bê tông nhựa C19'

    def test_format_asphalt_grade_empty(self):
        assert TRANSFORMS['format_asphalt_grade']({}, '') == 'Bê tông nhựa'

    def test_extract_asphalt_thickness(self):
        result = TRANSFORMS['extract_asphalt_thickness']({}, 'BTN dày 5cm')
        assert 'Dày' in result
        assert '5' in result

    def test_extract_asphalt_thickness_empty(self):
        assert TRANSFORMS['extract_asphalt_thickness']({}, 'BTN') == 'Theo thiết kế'

    def test_extract_tuoi_nhua_dosage(self):
        result = TRANSFORMS['extract_tuoi_nhua_dosage']({}, 'Tưới nhựa 1.5kg/m2')
        assert '1.5kg/m2' in result

    def test_extract_tuoi_nhua_dosage_empty(self):
        assert TRANSFORMS['extract_tuoi_nhua_dosage']({}, 'Tưới nhựa') == 'Theo thiết kế'


class TestConcreteTransforms:
    """Tests for concrete domain transforms."""

    def test_extract_stone_spec_from_specs(self):
        specs = {'stone': 'Đá 2x4'}
        assert TRANSFORMS['extract_stone_spec'](specs, '') == 'Đá 2x4'

    def test_extract_stone_spec_default(self):
        assert TRANSFORMS['extract_stone_spec']({}, '') == 'Đá 1x2'


class TestPipeFittingTransforms:
    """Tests for pipe fitting transforms."""

    def test_extract_pipe_fitting_material_from_specs(self):
        specs = {'material': 'Gang'}
        assert TRANSFORMS['extract_pipe_fitting_material'](specs, 'Tê Gang') == 'Gang'

    def test_extract_pipe_fitting_material_default(self):
        assert TRANSFORMS['extract_pipe_fitting_material']({}, 'tê thu') == 'HDPE'

    def test_extract_pipe_fitting_material_dau_bom(self):
        result = TRANSFORMS['extract_pipe_fitting_material']({}, 'Phụ kiện đầu bơm')
        assert result == 'Thép/Gang'

    def test_combine_pipe_fitting_specs(self):
        specs = {'diameter': 'D200', 'pressure': 'PN10'}
        result = TRANSFORMS['combine_pipe_fitting_specs'](specs, 'Tê HDPE D200 PN10')
        assert 'D200' in result
        assert 'PN10' in result

    def test_combine_pipe_fitting_specs_empty(self):
        assert TRANSFORMS['combine_pipe_fitting_specs']({}, 'Tê') == 'Theo thiết kế'

    def test_combine_pipe_fitting_specs_with_angle(self):
        specs = {'diameter': 'D110'}
        result = TRANSFORMS['combine_pipe_fitting_specs'](specs, 'Cút HDPE D110 90 độ')
        assert 'D110' in result
        # 90 is in fitting name, should not duplicate
        assert result.count('90') == 0 or 'Cút 90' not in result


class TestValveTransforms:
    """Tests for valve transforms."""

    def test_extract_valve_connection_from_specs(self):
        specs = {'connection': 'Bích'}
        assert TRANSFORMS['extract_valve_connection'](specs, '') == 'Bích'

    def test_extract_valve_connection_material_fallback(self):
        specs = {'material': 'Gang'}
        assert TRANSFORMS['extract_valve_connection'](specs, '') == 'Gang'

    def test_extract_valve_connection_empty(self):
        assert TRANSFORMS['extract_valve_connection']({}, '') == 'Theo thiết kế'

    def test_extract_valve_specs_with_diameter(self):
        specs = {'diameter': 'DN200'}
        result = TRANSFORMS['extract_valve_specs'](specs, 'Van cổng DN200')
        assert 'DN200' in result

    def test_extract_valve_specs_with_tay_gat(self):
        specs = {'diameter': 'DN50'}
        result = TRANSFORMS['extract_valve_specs'](specs, 'Van bi DN50 tay gạt')
        assert 'DN50' in result
        assert 'Tay gạt' in result

    def test_extract_valve_specs_van_khoa_no_duplicate_tay_gat(self):
        specs = {'diameter': 'DN100'}
        result = TRANSFORMS['extract_valve_specs'](specs, 'Van khóa tay gạt DN100')
        assert 'DN100' in result
        assert 'Tay gạt' not in result

    def test_extract_valve_specs_empty(self):
        assert TRANSFORMS['extract_valve_specs']({}, '') == 'Theo thiết kế'


class TestPumpTransforms:
    """Tests for pump transforms."""

    def test_extract_pump_type_dien(self):
        assert TRANSFORMS['extract_pump_type']({}, 'Bơm điện') == 'Điện'

    def test_extract_pump_type_diesel(self):
        assert TRANSFORMS['extract_pump_type']({}, 'Bơm diesel') == 'Diesel'

    def test_extract_pump_type_default(self):
        assert TRANSFORMS['extract_pump_type']({}, 'Bơm') == 'Điện'

    def test_combine_pump_specs(self):
        specs = {'flow_rate': 'Q=10m3/h', 'head': 'H=20m', 'power': 'P=5.5kW'}
        result = TRANSFORMS['combine_pump_specs'](specs, '')
        assert 'Q=10m3/h' in result
        assert 'H=20m' in result

    def test_combine_pump_specs_empty(self):
        assert TRANSFORMS['combine_pump_specs']({}, '') == 'Theo thiết kế'

    def test_combine_pressure_tank_specs(self):
        specs = {'volume': '200L', 'pressure': '10bar'}
        result = TRANSFORMS['combine_pressure_tank_specs'](specs, '')
        assert '200L' in result
        assert '10bar' in result


class TestPipeTransforms:
    """Tests for pipe transforms."""

    def test_determine_pipe_object_thep(self):
        assert TRANSFORMS['determine_pipe_object']({}, 'Ống thép DN200') == 'Ống thép'

    def test_determine_pipe_object_luon_day(self):
        assert TRANSFORMS['determine_pipe_object']({}, 'Ống luồn dây D50') == 'Ống luồn dây'

    def test_determine_pipe_object_gan_xoan(self):
        assert TRANSFORMS['determine_pipe_object']({}, 'Ống nhựa gân xoắn HDPE') == 'Ống luồn dây'

    def test_determine_pipe_object_default(self):
        assert TRANSFORMS['determine_pipe_object']({}, 'Ống HDPE D200') == 'Ống nhựa'

    def test_extract_pipe_material_ttk(self):
        result = TRANSFORMS['extract_pipe_material']({}, 'Ống thép tráng kẽm DN100')
        assert 'Tráng kẽm' in result

    def test_extract_pipe_material_hdpe(self):
        assert TRANSFORMS['extract_pipe_material']({}, 'Ống HDPE D315') == 'HDPE'

    def test_extract_pipe_material_hdpe_gan_xoan(self):
        result = TRANSFORMS['extract_pipe_material']({}, 'Ống nhựa HDPE gân xoắn D150')
        assert 'HDPE Gân xoắn' in result

    def test_extract_pipe_material_upvc(self):
        assert TRANSFORMS['extract_pipe_material']({}, 'Ống uPVC D110') == 'uPVC'

    def test_extract_pipe_material_pvc(self):
        assert TRANSFORMS['extract_pipe_material']({}, 'Ống PVC D75') == 'PVC'

    def test_extract_pipe_material_default(self):
        assert TRANSFORMS['extract_pipe_material']({}, 'Ống D200') == 'HDPE'

    def test_extract_pipe_material_thep_den(self):
        result = TRANSFORMS['extract_pipe_material']({}, 'Ống thép đen DN250')
        assert result == 'Đen'

    def test_combine_pipe_specs_diameter_pressure(self):
        specs = {'diameter': 'D315', 'pressure': 'PN10'}
        result = TRANSFORMS['combine_pipe_specs'](specs, 'Ống HDPE D315 PN10')
        assert 'D315' in result
        assert 'PN10' in result

    def test_combine_pipe_specs_empty(self):
        assert TRANSFORMS['combine_pipe_specs']({}, 'Ống') == 'Theo thiết kế'

    def test_combine_pipe_specs_diameter_from_original(self):
        result = TRANSFORMS['combine_pipe_specs']({}, 'Ống 195/150')
        assert 'D195/150' in result


class TestPrecastTransforms:
    """Tests for precast domain transforms."""

    def test_extract_cong_hop_specs_doi(self):
        result = TRANSFORMS['extract_cong_hop_specs']({}, 'Cống hộp đôi 2x2m')
        assert 'Đôi' in result

    def test_extract_cong_hop_specs_single(self):
        result = TRANSFORMS['extract_cong_hop_specs']({}, 'Cống hộp 1x1')
        assert '1x1' in result

    def test_extract_cong_hop_specs_empty(self):
        assert TRANSFORMS['extract_cong_hop_specs']({}, 'Cống hộp') == 'Theo thiết kế'

    def test_combine_cong_thoat_nuoc_specs(self):
        specs = {'diameter': 'D600'}
        result = TRANSFORMS['combine_cong_thoat_nuoc_specs'](specs, 'Cống thoát nước D600')
        assert 'D600' in result

    def test_extract_bo_via_specs_ha_he(self):
        result = TRANSFORMS['extract_bo_via_specs']({}, 'Bó vỉa hạ hè')
        assert 'Hạ hè' in result

    def test_extract_bo_via_specs_vuot_noi(self):
        result = TRANSFORMS['extract_bo_via_specs']({}, 'Bó vỉa vuốt nối')
        assert 'Vuốt nối' in result

    def test_extract_bo_via_specs_empty(self):
        assert TRANSFORMS['extract_bo_via_specs']({}, 'Bó vỉa') == 'Theo thiết kế'

    def test_convert_cm_to_mm(self):
        specs = {'dimensions': '50x50'}
        result = TRANSFORMS['convert_cm_to_mm_dimensions'](specs, '')
        assert result == '500x500'

    def test_convert_cm_to_mm_large_values(self):
        specs = {'dimensions': '300x500'}
        result = TRANSFORMS['convert_cm_to_mm_dimensions'](specs, '')
        # Values >= 200 are not converted
        assert result == '300x500'

    def test_convert_cm_to_mm_empty(self):
        assert TRANSFORMS['convert_cm_to_mm_dimensions']({}, '') == 'Theo thiết kế'


class TestMEPEquipmentTransforms:
    """Tests for MEP equipment transforms."""

    def test_extract_nap_ho_ga_specs_load(self):
        result = TRANSFORMS['extract_nap_ho_ga_specs']({}, 'Nắp hố ga 12.5 tấn')
        assert '12.5 tấn' in result

    def test_extract_nap_ho_ga_material_loai_2(self):
        result = TRANSFORMS['extract_nap_ho_ga_material']({}, 'Nắp hố ga loại 2')
        assert 'Composite/Gang' in result

    def test_extract_nap_ho_ga_material_default(self):
        assert TRANSFORMS['extract_nap_ho_ga_material']({}, 'Nắp hố ga') == 'Gang'

    def test_extract_song_chan_rac_specs(self):
        result = TRANSFORMS['extract_song_chan_rac_specs']({}, 'Song chắn rác 300x500 25kN')
        assert '300x500' in result
        assert '25kN' in result

    def test_extract_song_chan_rac_material_en124(self):
        result = TRANSFORMS['extract_song_chan_rac_material']({}, 'Song chắn rác EN124')
        assert 'EN124' in result

    def test_extract_cot_den_specs(self):
        specs = {'height': 'H=8m', 'arm_type': 'Cần đơn'}
        result = TRANSFORMS['extract_cot_den_specs'](specs, '')
        assert 'H=8m' in result
        assert 'Cần đơn' in result

    def test_extract_cot_den_specs_empty(self):
        assert TRANSFORMS['extract_cot_den_specs']({}, '') == 'Theo thiết kế'

    def test_extract_den_chieu_sang_fixture(self):
        specs = {'fixture_type': 'LED 100W'}
        assert TRANSFORMS['extract_den_chieu_sang_fixture'](specs, '') == 'LED 100W'

    def test_extract_den_chieu_sang_fixture_empty(self):
        assert TRANSFORMS['extract_den_chieu_sang_fixture']({}, '') == 'Theo thiết kế'

    def test_extract_hop_dong_ho_dims_from_specs(self):
        specs = {'dimensions': '350x140x140'}
        assert TRANSFORMS['extract_hop_dong_ho_dims'](specs, '') == '350x140x140'

    def test_extract_hop_dong_ho_dims_from_original(self):
        result = TRANSFORMS['extract_hop_dong_ho_dims']({}, 'Hộp đồng hồ KT350x140x140')
        assert '350x140x140' in result

    def test_extract_khung_mong_specs_bulong(self):
        result = TRANSFORMS['extract_khung_mong_specs']({}, 'Khung móng bulong M24')
        assert 'Bulong M24' in result
        assert 'Trọn bộ' in result


class TestFinishingTransforms:
    """Tests for finishing domain transforms."""

    def test_extract_trat_position_tiep_giap_cong(self):
        result = TRANSFORMS['extract_trat_position']({}, 'Trát tiếp giáp cống')
        assert result == 'Tiếp giáp cống'

    def test_extract_trat_position_thanh_ho_ga(self):
        result = TRANSFORMS['extract_trat_position']({}, 'Trát thành hố ga')
        assert result == 'Thành hố ga'

    def test_extract_trat_position_empty(self):
        assert TRANSFORMS['extract_trat_position']({}, 'Trát') == 'Theo thiết kế'

    def test_extract_trat_mortar_xi_mang(self):
        result = TRANSFORMS['extract_trat_mortar']({}, 'Trát xi măng')
        assert result == 'Xi măng'

    def test_extract_trat_mortar_from_specs(self):
        specs = {'mortar': 'M75'}
        result = TRANSFORMS['extract_trat_mortar'](specs, 'Trát vữa')
        assert result == 'M75'

    def test_extract_xay_gach_position_ho_ga(self):
        result = TRANSFORMS['extract_xay_gach_position']({}, 'Xây gạch hố ga')
        assert result == 'Hố ga'

    def test_extract_xay_tuong_type_chan(self):
        result = TRANSFORMS['extract_xay_tuong_type']({}, 'Xây tường chắn')
        assert result == 'Tường chắn'


class TestMiscTransforms:
    """Tests for miscellaneous transforms."""

    def test_extract_be_tu_purpose_phoi_quang(self):
        result = TRANSFORMS['extract_be_tu_purpose']({}, 'Bệ tủ phối quang')
        assert result == 'Tủ phối quang'

    def test_extract_lo_xo_purpose_bom_chua_chay(self):
        result = TRANSFORMS['extract_lo_xo_purpose']({}, 'Lò xo giảm chấn bơm chữa cháy')
        assert result == 'Bơm chữa cháy'

    def test_extract_lo_xo_purpose_bom(self):
        result = TRANSFORMS['extract_lo_xo_purpose']({}, 'Lò xo giảm chấn bơm')
        assert result == 'Bơm'

    def test_extract_nilon_type_tai_sinh(self):
        result = TRANSFORMS['extract_nilon_type']({}, 'Nilon tái sinh')
        assert result == 'Tái sinh'

    def test_extract_nilon_purpose_lot_mong(self):
        result = TRANSFORMS['extract_nilon_purpose']({}, 'Nilon lót móng')
        assert result == 'Lót móng'

    def test_extract_nilon_purpose_default(self):
        result = TRANSFORMS['extract_nilon_purpose']({}, 'Nilon')
        assert result == 'Lót móng'

    def test_extract_chi_phi_type_thi_nghiem(self):
        result = TRANSFORMS['extract_chi_phi_type']({}, 'Chi phí thí nghiệm')
        assert result == 'Thí nghiệm'

    def test_extract_chi_phi_type_kiem_dinh(self):
        result = TRANSFORMS['extract_chi_phi_type']({}, 'Chi phí kiểm định')
        assert result == 'Kiểm định'

    def test_extract_chi_phi_type_both(self):
        result = TRANSFORMS['extract_chi_phi_type']({}, 'Chi phí kiểm định/thí nghiệm')
        assert result == 'Kiểm định/Thí nghiệm'

    def test_extract_chi_phi_scope_dien_tro(self):
        result = TRANSFORMS['extract_chi_phi_scope']({}, 'Chi phí kiểm định điện trở nối đất')
        assert result == 'Điện trở nối đất'

    def test_extract_chi_phi_scope_default(self):
        result = TRANSFORMS['extract_chi_phi_scope']({}, 'Chi phí')
        assert result == 'Trọn gói'

    def test_extract_da_hoc_type_xep_khan(self):
        result = TRANSFORMS['extract_da_hoc_type']({}, 'Đá hộc xếp khan')
        assert result == 'Xếp khan'

    def test_extract_da_dam_purpose_dem(self):
        result = TRANSFORMS['extract_da_dam_purpose']({}, 'Đá dăm đệm móng')
        assert result == 'Đệm móng'

    def test_extract_mong_tru_purpose_chong_set(self):
        result = TRANSFORMS['extract_mong_tru_purpose']({}, 'Móng trụ chống sét')
        assert result == 'Chống sét'

    def test_extract_quan_trac_type_lun(self):
        result = TRANSFORMS['extract_quan_trac_type']({}, 'Bản quan trắc lún')
        assert result == 'Quan trắc lún'

    def test_extract_trong_co_position_mai(self):
        result = TRANSFORMS['extract_trong_co_position']({}, 'Trồng cỏ mái taluy')
        assert result == 'Mái taluy'

    def test_extract_trong_co_care(self):
        result = TRANSFORMS['extract_trong_co_care']({}, 'Trồng cỏ chăm sóc 12 tháng')
        assert result == 'Bao gồm chăm sóc'

    def test_extract_coc_tre_spec(self):
        specs = {'spec': 'L=2.5m D6-8cm'}
        result = TRANSFORMS['extract_coc_tre_spec'](specs, '')
        assert result == 'l=2.5m d6-8cm'

    def test_extract_rebar_size_from_specs(self):
        specs = {'rebar_diameter': 'D20'}
        result = TRANSFORMS['extract_rebar_size'](specs, '')
        assert result == 'D20'

    def test_extract_rebar_size_from_original(self):
        result = TRANSFORMS['extract_rebar_size']({}, 'Cốt thép ≤18mm')
        assert '≤18mm' in result

    def test_extract_rebar_size_empty(self):
        assert TRANSFORMS['extract_rebar_size']({}, 'Cốt thép') == 'Theo thiết kế'


class TestTrafficSignTransforms:
    """Tests for traffic sign transforms."""

    def test_extract_sign_type_tam_giac(self):
        assert TRANSFORMS['extract_sign_type']({}, 'Biển báo tam giác') == 'Tam giác'

    def test_extract_sign_type_tron(self):
        assert TRANSFORMS['extract_sign_type']({}, 'Biển báo tròn') == 'Tròn'

    def test_extract_sign_type_chi_huong(self):
        result = TRANSFORMS['extract_sign_type']({}, 'Biển chỉ hướng 414A')
        assert 'Chỉ hướng' in result
        assert '414A' in result

    def test_extract_sign_specs_size(self):
        result = TRANSFORMS['extract_sign_specs']({}, 'Biển báo A70cm cột sơn trắng đỏ')
        assert '70cm' in result
        assert 'Cột sơn trắng đỏ' in result

    def test_extract_sign_specs_empty(self):
        assert TRANSFORMS['extract_sign_specs']({}, 'Biển báo') == 'Theo thiết kế'


class TestValveAccessoryTransforms:
    """Tests for valve accessory transforms."""

    def test_extract_valve_type_rac_co_doi(self):
        result = TRANSFORMS['extract_valve_type_with_accessories']({}, 'Van bi rắc co đôi')
        assert 'rắc co đôi' in result

    def test_extract_valve_type_from_specs(self):
        specs = {'type': 'Bướm'}
        result = TRANSFORMS['extract_valve_type_with_accessories'](specs, 'Van')
        assert result == 'Bướm'

    def test_extract_valve_specs_with_handle_van_bi(self):
        specs = {'diameter': 'DN25'}
        result = TRANSFORMS['extract_valve_specs_with_handle'](specs, 'Van bi tay gạt DN25')
        assert 'DN25' in result
        assert 'Tay gạt' in result


class TestSteelPipeTransforms:
    """Tests for steel pipe transforms."""

    def test_extract_steel_pipe_material_trang_kem(self):
        result = TRANSFORMS['extract_steel_pipe_material']({}, 'Ống thép tráng kẽm DN50')
        assert 'Tráng kẽm' in result

    def test_extract_steel_pipe_material_ttk(self):
        result = TRANSFORMS['extract_steel_pipe_material']({}, 'Ống TTK DN200')
        assert 'Tráng kẽm' in result

    def test_extract_steel_pipe_material_den(self):
        result = TRANSFORMS['extract_steel_pipe_material']({}, 'Ống thép đen DN250')
        assert result == 'Đen'

    def test_extract_steel_pipe_material_default(self):
        result = TRANSFORMS['extract_steel_pipe_material']({}, 'Ống thép DN100')
        assert result == 'Đen'


class TestEdgeCases:
    """Edge cases: None values, empty dicts, special characters."""

    def test_all_transforms_handle_empty_specs(self):
        """Every transform should handle empty specs without raising."""
        for name, func in TRANSFORMS.items():
            try:
                result = func({}, '')
                assert isinstance(result, str), f"Transform '{name}' returned {type(result)}"
            except Exception as e:
                pytest.fail(f"Transform '{name}' raised {type(e).__name__}: {e}")

    def test_all_transforms_handle_none_values_in_specs(self):
        """Transforms should handle None values in spec keys."""
        specs_with_nones = {
            'diameter': None, 'grade': None, 'material': None,
            'position': None, 'pressure': None, 'thickness': None,
        }
        for name, func in TRANSFORMS.items():
            try:
                result = func(specs_with_nones, '')
                assert isinstance(result, str), f"Transform '{name}' returned {type(result)}"
            except Exception as e:
                pytest.fail(f"Transform '{name}' raised {type(e).__name__}: {e}")


class TestInstrumentTransforms:
    """Tests for instrument/metering transforms."""

    def test_extract_accuracy_class_with_0_5s(self):
        result = TRANSFORMS['extract_accuracy_class']({}, 'Đồng hồ đa năng 0.5S Modbus')
        assert result == 'Cấp 0.5S'

    def test_extract_accuracy_class_with_comma(self):
        result = TRANSFORMS['extract_accuracy_class']({}, 'Đồng hồ cấp chính xác 0,5S')
        assert result == 'Cấp 0.5S'

    def test_extract_accuracy_class_empty(self):
        assert TRANSFORMS['extract_accuracy_class']({}, 'Đồng hồ đa năng') == 'Theo thiết kế'

    def test_extract_protocol_modbus(self):
        assert TRANSFORMS['extract_protocol']({}, 'Đồng hồ Modbus') == 'Modbus'

    def test_extract_protocol_modbus_rtu(self):
        assert TRANSFORMS['extract_protocol']({}, 'Đồng hồ Modbus RTU') == 'Modbus RTU'

    def test_extract_protocol_rs485(self):
        assert TRANSFORMS['extract_protocol']({}, 'Đồng hồ RS485') == 'RS485'

    def test_extract_protocol_empty(self):
        assert TRANSFORMS['extract_protocol']({}, 'Đồng hồ đa năng') == 'Theo thiết kế'
