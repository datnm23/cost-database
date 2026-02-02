"""
Test with items that have valid SEC codes
"""
import sys
sys.path.insert(0, '/app')

from app.core.database import SessionLocal
from app.models.line_item import LineItem
from app.services.work_code_generator import WorkCodeGenerator
from collections import defaultdict

db = SessionLocal()
generator = WorkCodeGenerator(db)

print('='*100)
print('TEST WITH ITEMS THAT HAVE SEC CODES')
print('='*100)

# Get items with valid SEC codes
items = db.query(LineItem).filter(
    LineItem.sec_code.isnot(None)
).order_by(LineItem.sec_code).all()

print(f'\nTotal items with SEC codes: {len(items)}')

# Analyze SEC code distribution
sec_distribution = defaultdict(int)
for item in items:
    sec_distribution[item.sec_code] += 1

print(f'\nSEC Code Distribution:')
for sec, count in sorted(sec_distribution.items()):
    print(f'  {sec}: {count} items')

stats = {
    'total': 0,
    'with_grade': 0,
    'by_sec': defaultdict(int),
    'by_grade': defaultdict(int),
    'examples': defaultdict(list)
}

print(f'\n{"Description":<55} {"SEC":<12} {"Work Code":<32} {"Grade":<8}')
print('-'*110)

for item in items:
    if not item.description:
        continue

    work_code = generator.generate_work_code(
        description=item.description,
        sec_code=item.sec_code,
        unit=item.unit,
        include_grade=True
    )

    grade = generator.extract_material_grade(item.description)

    stats['total'] += 1
    stats['by_sec'][item.sec_code] += 1

    if grade:
        stats['with_grade'] += 1
        stats['by_grade'][grade] += 1

    # Store examples
    if len(stats['examples'][item.sec_code]) < 3:
        stats['examples'][item.sec_code].append({
            'desc': item.description,
            'code': work_code,
            'grade': grade
        })

    # Display first 40
    if stats['total'] <= 40:
        desc = (item.description[:52] + '...') if len(item.description) > 55 else item.description
        print(f"{desc:<55} {item.sec_code:<12} {work_code:<32} {grade or '-':<8}")

if stats['total'] > 40:
    print(f'\n... and {stats["total"] - 40} more items')

print('\n' + '='*100)
print('STATISTICS')
print('='*100)
print(f"Total processed: {stats['total']}")
print(f"With grades: {stats['with_grade']} ({stats['with_grade']/stats['total']*100 if stats['total'] > 0 else 0:.1f}%)")
print(f"Without grades: {stats['total'] - stats['with_grade']}")

print(f"\nBy SEC Code:")
for sec, count in sorted(stats['by_sec'].items()):
    pct = count / stats['total'] * 100 if stats['total'] > 0 else 0
    print(f"  {sec}: {count} items ({pct:.1f}%)")

if stats['by_grade']:
    print(f"\nMaterial Grades Detected:")
    for grade, count in sorted(stats['by_grade'].items()):
        pct = count / stats['with_grade'] * 100 if stats['with_grade'] > 0 else 0
        print(f"  {grade}: {count} items ({pct:.1f}%)")

print('\n' + '='*100)
print('EXAMPLES BY SEC CODE')
print('='*100)

for sec in sorted(stats['examples'].keys()):
    print(f'\n{sec}:')
    for ex in stats['examples'][sec]:
        desc_short = (ex['desc'][:50] + '...') if len(ex['desc']) > 53 else ex['desc']
        grade_info = f"[Grade: {ex['grade']}]" if ex['grade'] else ""
        print(f"  {ex['code']:<32} {desc_short:<53} {grade_info}")

# Check for items that might need grades
print('\n' + '='*100)
print('ITEMS THAT MIGHT NEED MATERIAL GRADES')
print('='*100)

keywords = ['bê tông', 'beton', 'vữa', 'concrete', 'mortar', 'b25', 'b30']
needs_grade = []

for item in items:
    if not item.description:
        continue
    desc_lower = item.description.lower()
    has_keyword = any(kw in desc_lower for kw in keywords)
    grade = generator.extract_material_grade(item.description)

    if has_keyword and not grade:
        needs_grade.append(item.description)

if needs_grade:
    print(f'\nFound {len(needs_grade)} items with concrete/mortar keywords but no grade:\n')
    for i, desc in enumerate(needs_grade[:15], 1):
        print(f"{i}. {desc}")
    if len(needs_grade) > 15:
        print(f'\n... and {len(needs_grade) - 15} more')
else:
    print('\n✓ All concrete/mortar items have material grades!')

db.close()
