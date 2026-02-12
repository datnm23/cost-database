#!/usr/bin/env python3
"""Test cable normalization for Cu/MICA/XLPE/PVC/FR-PVC pattern"""
import re

# Current xlpe pattern from mep_equipment_normalizer.py
xlpe_pattern = r'[Cc]áp\s*(?:đồng|Cu)?[/\s]*(?:XLPE)[/\s]*(PVC|PE|DSTA)?\s*(\d+)[xX](\d+)\s*(?:mm2?)?'

test_input = "Cáp Cu/MICA/XLPE/PVC/FR-PVC 4x300mm2"

print("=" * 60)
print(f"Input: {test_input}")
print("=" * 60)

# Test current pattern
match = re.search(xlpe_pattern, test_input, re.IGNORECASE)
if match:
    print(f"\n[xlpe] MATCHED: '{match.group(0)}'")
    print(f"  Groups: {match.groups()}")
    jacket = match.group(1) or 'PVC'
    cores = match.group(2)
    size = match.group(3)
    result = f"Cáp Cu/XLPE/{jacket} - {cores}x{size}mm2"
    print(f"  Normalized: {result}")
    print(f"\n  PROBLEM: Lost MICA layer and FR-PVC jacket info!")
    print(f"  Expected: Cáp Cu/MICA/XLPE/PVC/FR-PVC - 4x300mm2")
    print(f"  Got:      {result}")
else:
    print("\n[xlpe] NO MATCH")
    print("  The pattern cannot handle MICA layer between Cu and XLPE")

# Explain the regex issue
print("\n" + "=" * 60)
print("ANALYSIS:")
print("=" * 60)
print("""
The xlpe regex pattern:
  [Cc]áp\\s*(?:đồng|Cu)?[/\\s]*(?:XLPE)[/\\s]*(PVC|PE|DSTA)?\\s*(\\d+)[xX](\\d+)

Breaking down with input 'Cáp Cu/MICA/XLPE/PVC/FR-PVC 4x300mm2':
  - [Cc]áp       => matches 'Cáp'
  - \\s*           => matches ' '
  - (?:đồng|Cu)? => matches 'Cu'
  - [/\\s]*        => matches '/'  
  - (?:XLPE)     => FAILS because next text is 'MICA', NOT 'XLPE'

The pattern expects 'Cu' to be immediately followed by XLPE (with optional / separator).
But the input has 'Cu/MICA/XLPE' - there's a MICA layer in between.

PROBLEMS IDENTIFIED:
1. Pattern cannot match multi-layer cable insulation with MICA fire-barrier
2. Even if it did match, the jacket group (PVC|PE|DSTA) cannot capture 'FR-PVC'  
3. The full material chain Cu/MICA/XLPE/PVC/FR-PVC would be lost in normalization
""")

# Check what the actual normalizer does
print("=" * 60)
print("Testing with actual normalizer:")
print("=" * 60)
try:
    import sys
    sys.path.insert(0, 'backend')
    from app.services.mep_equipment_normalizer import MEPEquipmentNormalizer
    
    normalizer = MEPEquipmentNormalizer()
    result = normalizer.normalize(test_input)
    print(f"  Original:   {result.original}")
    print(f"  Normalized: {result.normalized}")
    print(f"  Type:       {result.equipment_type}")
    print(f"  Specs:      {result.specs}")
    print(f"  Confidence: {result.confidence}")
except Exception as e:
    print(f"  Error: {e}")
