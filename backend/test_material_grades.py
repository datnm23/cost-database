"""
Test material grades (mác bê tông, mác vữa)
"""
import sys
sys.path.insert(0, '/app')

from app.services.work_code_generator import WorkCodeGenerator
from app.core.database import SessionLocal

db = SessionLocal()
generator = WorkCodeGenerator(db)

print('\n' + '='*80)
print('TEST: MATERIAL GRADES (Mác Bê Tông, Mác Vữa)')
print('='*80 + '\n')

# Test material grade extraction
print('1. TEST EXTRACT MATERIAL GRADE')
print('-'*80)

test_extractions = [
    "Bê tông M200",
    "Bê tông M250",
    "Bê tông M300",
    "Bê tông mác 200",
    "Bê tông mác 250",
    "Concrete grade 300",
    "Vữa trát M75",
    "Vữa trát M100",
    "Vữa xây M50",
    "Tường gạch vữa M75",
    "Bê tông cột",  # Không có mác
    "Trát tường",   # Không có mác
]

print(f"{'Description':<40} {'Extracted Grade':<15}")
print('-'*80)

for desc in test_extractions:
    grade = generator.extract_material_grade(desc)
    print(f"{desc:<40} {grade or 'None':<15}")

# Test work code generation with grades
print('\n\n2. TEST WORK CODE GENERATION WITH GRADES')
print('-'*80)

test_cases = [
    # Bê tông với mác khác nhau
    ("Bê tông M200 dầm", "SEC-02"),
    ("Bê tông M250 cột", "SEC-02"),
    ("Bê tông M300 sàn", "SEC-02"),
    ("Bê tông mác 200 móng", "SEC-01-03"),

    # Vữa với mác khác nhau
    ("Vữa trát M75", "SEC-03"),
    ("Vữa trát M100", "SEC-03"),
    ("Tường gạch vữa M50", "SEC-03"),
    ("Tường gạch vữa M75", "SEC-03"),
    ("Xây block vữa M100", "SEC-03"),

    # Công tác không có mác (để so sánh)
    ("Bê tông dầm", "SEC-02"),
    ("Tường gạch", "SEC-03"),
    ("Trát tường", "SEC-03"),
]

print(f"{'Description':<35} {'SEC':<10} {'Work Code':<30} {'Valid':<6}")
print('-'*80)

for desc, sec in test_cases:
    code = generator.generate_work_code(desc, sec, include_grade=True)
    is_valid = generator.validate_work_code(code)
    print(f"{desc:<35} {sec:<10} {code:<30} {is_valid}")

# Test with and without grade
print('\n\n3. TEST WITH/WITHOUT GRADE OPTION')
print('-'*80)

test_desc = "Bê tông M200 dầm"
sec = "SEC-02"

code_with_grade = generator.generate_work_code(test_desc, sec, include_grade=True)
code_without_grade = generator.generate_work_code(test_desc, sec, include_grade=False)

print(f"Description: {test_desc}")
print(f"SEC Code: {sec}")
print(f"\nWith grade:    {code_with_grade}")
print(f"Without grade: {code_without_grade}")
print(f"\nExplanation:")
print(f"  - With grade: Material grade M200 is included in code")
print(f"  - Without grade: Uses sub-category or just category")

# Test parsing codes with grades
print('\n\n4. TEST PARSE WORK CODES WITH GRADES')
print('-'*80)

test_codes = [
    "S02-CONC-M200-0001",
    "S02-CONC-M250-0001",
    "S03-PLAST-M75-0001",
    "S03-WALL-BRICK-0001",
]

print(f"{'Work Code':<30} {'Parsed Components':<50}")
print('-'*80)

for code in test_codes:
    parsed = generator.parse_work_code(code)
    if parsed:
        components = f"SEC={parsed['sec_prefix']}, CAT={parsed['category']}, SUB={parsed.get('sub_category') or 'None'}, SEQ={parsed['sequence']}"
        print(f"{code:<30} {components:<50}")
    else:
        print(f"{code:<30} INVALID")

# Summary
print('\n\n' + '='*80)
print('SUMMARY')
print('='*80)
print("""
Material grades are now supported in the work code system:

1. Auto-detection of material grades from description:
   - "Bê tông M200" → M200
   - "Vữa trát M75" → M75
   - "mác 250" → M250

2. Work code formats:
   - With grade: S02-CONC-M200-0001
   - Without grade: S02-CONC-BEAM-0001

3. Benefits:
   ✓ Easy search by material grade
   ✓ Clear differentiation between different grades
   ✓ Still maintains hierarchy: SEC → Category → Grade/Sub → Sequence

4. Search examples:
   - All M200 concrete: WHERE work_code LIKE '%-M200-%'
   - All concrete: WHERE work_code LIKE 'S02-CONC-%'
   - Specific grade concrete: WHERE work_code LIKE 'S02-CONC-M200-%'
""")

db.close()
