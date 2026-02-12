import re

# Test 1: xlpe_mica pattern for multi-layer cable
pattern_mica = r'[Cc]áp\s*(?:đồng|Cu)?((?:/[A-Za-z][-A-Za-z]*){3,})\s+(\d+)[xX](\d+)\s*(?:mm2?)?'
# Test 2: xlpe pattern for simple XLPE cable
pattern_xlpe = r'[Cc]áp\s*(?:đồng|Cu)?[/\s]*(?:XLPE)[/\s]*(PVC|PE|DSTA)?\s*(\d+)[xX](\d+)\s*(?:mm2?)?'

tests = {
    'Cáp Cu/MICA/XLPE/PVC/FR-PVC 4x300mm2': ('mica', '/MICA/XLPE/PVC/FR-PVC', '4', '300'),
    'Cáp Cu/XLPE/PVC 4x300mm2': ('xlpe', 'PVC', '4', '300'),
    'Cáp Cu/XLPE/DSTA 3x120mm2': ('xlpe', 'DSTA', '3', '120'),
    'Cáp Cu/XLPE/PVC/FR-PVC 2x10mm2': ('mica', '/XLPE/PVC/FR-PVC', '2', '10'),
}

print("REGEX TEST RESULTS:")
print("=" * 70)

for inp, expected in tests.items():
    m_mica = re.search(pattern_mica, inp, re.IGNORECASE)
    m_xlpe = re.search(pattern_xlpe, inp, re.IGNORECASE)

    if m_mica:
        layers = m_mica.group(1)
        cores = m_mica.group(2)
        size = m_mica.group(3)
        result = "Cáp Cu{} - {}x{}mm2".format(layers, cores, size)
        matched = "xlpe_mica"
    elif m_xlpe:
        jacket = m_xlpe.group(1) or 'PVC'
        cores = m_xlpe.group(2)
        size = m_xlpe.group(3)
        result = "Cáp Cu/XLPE/{} - {}x{}mm2".format(jacket, cores, size)
        matched = "xlpe"
    else:
        result = "NO MATCH"
        matched = "none"

    print("INPUT:    {}".format(inp))
    print("MATCHED:  {}".format(matched))
    print("RESULT:   {}".format(result))
    print()
