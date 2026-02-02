"""
Test Work Code Generator với Real BOQ Data
"""
import sys
sys.path.insert(0, '/app')

from app.core.database import SessionLocal
from app.models.line_item import LineItem
from app.services.work_code_generator import WorkCodeGenerator
from collections import defaultdict

db = SessionLocal()
generator = WorkCodeGenerator(db)

print('\n' + '='*100)
print('TEST WORK CODE GENERATOR WITH REAL BOQ DATA')
print('='*100 + '\n')

# Get all line items
items = db.query(LineItem).filter(
    LineItem.description != '',
    LineItem.description.isnot(None)
).order_by(LineItem.sec_code, LineItem.description).all()

print(f'Total items to process: {len(items)}\n')

# Statistics
stats = {
    'total': 0,
    'with_grade': 0,
    'without_grade': 0,
    'by_sec': defaultdict(int),
    'by_grade': defaultdict(int),
    'grades_detected': []
}

# Process items and generate work codes
print('='*100)
print('GENERATED WORK CODES')
print('='*100)
print(f"{'Description':<50} {'SEC':<12} {'Work Code':<30} {'Grade':<8}")
print('-'*100)

results = []

for item in items[:50]:  # Process first 50 for display
    try:
        # Generate work code
        work_code = generator.generate_work_code(
            description=item.description,
            sec_code=item.sec_code or 'SEC-00',
            unit=item.unit,
            include_grade=True
        )

        # Extract grade
        grade = generator.extract_material_grade(item.description)

        # Update stats
        stats['total'] += 1
        stats['by_sec'][item.sec_code or 'NONE'] += 1

        if grade:
            stats['with_grade'] += 1
            stats['by_grade'][grade] += 1
            stats['grades_detected'].append(grade)
        else:
            stats['without_grade'] += 1

        # Store result
        results.append({
            'description': item.description,
            'sec_code': item.sec_code,
            'work_code': work_code,
            'grade': grade
        })

        # Display
        desc = (item.description[:47] + '...') if len(item.description) > 50 else item.description
        print(f"{desc:<50} {item.sec_code or 'N/A':<12} {work_code:<30} {grade or '-':<8}")

    except Exception as e:
        print(f"ERROR: {item.description[:30]}... - {e}")

# Statistics by SEC Code
print('\n\n' + '='*100)
print('STATISTICS BY SEC CODE')
print('='*100)
print(f"{'SEC Code':<15} {'Count':<10} {'Percentage':<15}")
print('-'*100)

for sec_code, count in sorted(stats['by_sec'].items()):
    percentage = (count / stats['total'] * 100) if stats['total'] > 0 else 0
    print(f"{sec_code:<15} {count:<10} {percentage:>6.1f}%")

# Material grades statistics
print('\n\n' + '='*100)
print('MATERIAL GRADES DETECTED')
print('='*100)

if stats['grades_detected']:
    unique_grades = set(stats['grades_detected'])
    print(f"Total items with grades: {stats['with_grade']}")
    print(f"Total items without grades: {stats['without_grade']}")
    print(f"Unique grades found: {len(unique_grades)}\n")

    print(f"{'Grade':<10} {'Count':<10} {'Percentage':<15}")
    print('-'*100)

    for grade, count in sorted(stats['by_grade'].items(), key=lambda x: x[1], reverse=True):
        percentage = (count / stats['with_grade'] * 100) if stats['with_grade'] > 0 else 0
        print(f"{grade:<10} {count:<10} {percentage:>6.1f}%")
else:
    print("No material grades detected in this dataset.")

# Find items that should have grades but don't
print('\n\n' + '='*100)
print('POTENTIAL ITEMS MISSING MATERIAL GRADES')
print('='*100)
print('(Items with keywords "bê tông", "vữa", "beton" but no grade detected)\n')

keywords_needing_grade = ['bê tông', 'beton', 'vữa', 'concrete', 'mortar']
missing_grade_items = []

for item in items[:100]:
    desc_lower = item.description.lower()
    has_keyword = any(kw in desc_lower for kw in keywords_needing_grade)
    grade = generator.extract_material_grade(item.description)

    if has_keyword and not grade:
        missing_grade_items.append(item.description)

if missing_grade_items:
    print(f"{'Description':<80}")
    print('-'*100)
    for desc in missing_grade_items[:20]:
        desc_display = (desc[:77] + '...') if len(desc) > 80 else desc
        print(f"{desc_display:<80}")

    if len(missing_grade_items) > 20:
        print(f"\n... and {len(missing_grade_items) - 20} more items")
else:
    print("✓ All concrete/mortar items have material grades specified!")

# Work code validation
print('\n\n' + '='*100)
print('WORK CODE VALIDATION')
print('='*100)

valid_count = 0
invalid_count = 0

for result in results:
    if generator.validate_work_code(result['work_code']):
        valid_count += 1
    else:
        invalid_count += 1
        print(f"INVALID: {result['work_code']} - {result['description'][:50]}")

print(f"\nValid codes: {valid_count}/{len(results)}")
print(f"Invalid codes: {invalid_count}/{len(results)}")

if invalid_count == 0:
    print("✓ All generated work codes are valid!")

# Sample work codes by category
print('\n\n' + '='*100)
print('SAMPLE WORK CODES BY CATEGORY')
print('='*100)

# Group by SEC code
by_sec = defaultdict(list)
for result in results:
    sec = result['sec_code'] or 'NONE'
    by_sec[sec].append(result)

for sec_code in sorted(by_sec.keys()):
    items_in_sec = by_sec[sec_code][:5]  # First 5 items per SEC
    print(f"\n{sec_code}:")
    for item in items_in_sec:
        desc = (item['description'][:45] + '...') if len(item['description']) > 48 else item['description']
        grade_info = f"(Grade: {item['grade']})" if item['grade'] else ""
        print(f"  {item['work_code']:<30} {desc:<48} {grade_info}")

# Summary
print('\n\n' + '='*100)
print('SUMMARY')
print('='*100)
print(f"""
Total items processed: {stats['total']}
Items with material grades: {stats['with_grade']} ({stats['with_grade']/stats['total']*100 if stats['total'] > 0 else 0:.1f}%)
Items without grades: {stats['without_grade']} ({stats['without_grade']/stats['total']*100 if stats['total'] > 0 else 0:.1f}%)

Validation:
✓ Valid codes: {valid_count}/{len(results)}
✗ Invalid codes: {invalid_count}/{len(results)}

Coverage by SEC Code:
""")

for sec_code, count in sorted(stats['by_sec'].items()):
    percentage = (count / stats['total'] * 100) if stats['total'] > 0 else 0
    print(f"  {sec_code}: {count} items ({percentage:.1f}%)")

print(f"""
Status: {'✓ READY FOR PRODUCTION' if invalid_count == 0 else '⚠ NEEDS REVIEW'}
""")

db.close()
