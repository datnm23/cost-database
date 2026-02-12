#!/usr/bin/env python3
"""Test cable normalization after fix"""
import sys, os
os.chdir('/home/datnm/projects/cost-database')
sys.path.insert(0, 'backend')
from app.services.mep_equipment_normalizer import MEPEquipmentNormalizer

normalizer = MEPEquipmentNormalizer()

test_cases = [
    "Cáp Cu/MICA/XLPE/PVC/FR-PVC 4x300mm2",
    "Cáp Cu/XLPE/PVC 4x300mm2",
    "Cáp Cu/XLPE/DSTA 3x120mm2",
    "Cáp Cu/XLPE/PVC/FR-PVC 2x10mm2",
    "Dây điện 1x2.5mm2",
    "Cáp đồng bọc PVC 1x6mm2",
]

results = []
for inp in test_cases:
    r = normalizer.normalize(inp)
    results.append("{} | {} | {} | {}".format(
        r.equipment_type, r.normalized, r.confidence, r.specs))

with open("/home/datnm/projects/cost-database/cable_test_output.txt", "w", encoding="utf-8") as f:
    for i, inp in enumerate(test_cases):
        f.write("IN:  " + inp + "\n")
        f.write("OUT: " + results[i] + "\n\n")
