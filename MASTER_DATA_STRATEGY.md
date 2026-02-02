# CHIẾN LƯỢC XÂY DỰNG BẢNG CHUẨN (MASTER DATA STRATEGY)

## 📋 MỤC TIÊU

Xây dựng **Bảng Công Tác Chuẩn (Master Work Items Database)** từ nhiều nguồn BOQ với mục tiêu:

1. **Deduplicate**: Loại bỏ trùng lặp từ nhiều BOQ
2. **Normalize**: Chuẩn hóa mô tả theo quy chuẩn
3. **Classify**: Phân loại chuẩn xác theo SEC codes
4. **Aggregate**: Tổng hợp giá tham chiếu từ nhiều nguồn
5. **Intelligence**: Tạo knowledge base cho pricing và estimating

---

## 🏗️ KIẾN TRÚC MASTER DATABASE

### Bảng `master_work_items`

```sql
CREATE TABLE master_work_items (
    -- Identification
    master_id INT PRIMARY KEY AUTO_INCREMENT,
    work_code VARCHAR(50) UNIQUE NOT NULL,          -- Mã công tác chuẩn
    description TEXT NOT NULL,                       -- Mô tả chuẩn hóa
    description_normalized VARCHAR(500),             -- Lowercase cho search

    -- Classification
    sec_code VARCHAR(20) NOT NULL,                   -- SEC code
    category VARCHAR(100),                           -- Chi tiết (VD: "Công tác cọc")

    -- Unit Standardization
    unit_standard VARCHAR(20) NOT NULL,              -- Đơn vị chuẩn
    unit_variants TEXT,                              -- JSON: các biến thể

    -- Reference Pricing (tổng hợp từ nhiều BOQ)
    ref_unit_price_min DECIMAL(15,2),               -- Giá thấp nhất
    ref_unit_price_max DECIMAL(15,2),               -- Giá cao nhất
    ref_unit_price_avg DECIMAL(15,2),               -- Giá trung bình

    -- Statistics & Traceability
    occurrence_count INT DEFAULT 1,                  -- Số lần xuất hiện
    source_files TEXT,                               -- JSON: [file_id1, file_id2]

    -- Quality Control
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,               -- Expert verified
    verified_by INT,
    verified_at TIMESTAMP,

    -- Metadata
    tags TEXT,                                       -- JSON: search tags
    notes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_sec_code (sec_code),
    INDEX idx_description (description_normalized),
    INDEX idx_unit (unit_standard),
    INDEX idx_active (is_active),
    FULLTEXT INDEX idx_description_ft (description)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## 🔄 PIPELINE XÂY DỰNG MASTER

### Phase 1: Data Ingestion

```
┌──────────────────────────────────────────────────────────┐
│ INPUT: line_items từ BOQ files                          │
└──────────────────────────────────────────────────────────┘

Filters:
├─> confidence_score >= min_confidence (default 60%)
├─> sec_code IS NOT NULL (or include unclassified)
└─> is_active = TRUE

Quality Gates:
├─> Description không empty
├─> Unit không NULL
├─> Price hợp lệ (> 0)
└─> Quantity > 0 (optional)

Output: Filtered line_items ready for processing
```

### Phase 2: Normalization

```
┌──────────────────────────────────────────────────────────┐
│ NORMALIZATION PIPELINE                                   │
└──────────────────────────────────────────────────────────┘

For each line_item:
    │
    ├─> Step 1: Identify Work Category
    │       │
    │       ├─> Earthworks & Piling
    │       ├─> Concrete & Rebar
    │       ├─> Finishing
    │       ├─> Steel & MEP
    │       └─> General
    │
    ├─> Step 2: Parse Components
    │       │
    │       ├─> Verb (Động từ): Đổ, Xây, Gia công
    │       ├─> Material (Vật liệu): bê tông, gạch, cốt thép
    │       ├─> Position (Vị trí): móng, cột, dầm, tường
    │       ├─> Grade (Mác): M300, CB400, D18
    │       ├─> Specs (Kích thước): 600x600, H400x200
    │       └─> Details: thương phẩm, đá 1x2, vữa M75
    │
    ├─> Step 3: Apply Category Template
    │       │
    │       ├─> Earthworks: [Action][Object][pos] - [Size] - [Soil]
    │       ├─> Concrete: [Action][Material][pos] - [Grade] - [Features]
    │       ├─> Finishing: [Verb][Material][pos] - [Specs] - [Color]
    │       └─> MEP: [Verb][System][pos] - [Specs] - [Method]
    │
    ├─> Step 4: Build Normalized Description
    │       │
    │       └─> Example:
    │           Input:  "Bê tông móng M200 thương phẩm"
    │           Output: "Đổ bê tông móng - M200 - thương phẩm"
    │
    └─> Step 5: Generate Search Index
            │
            └─> description_normalized = lowercase(description)
```

**Code Implementation:**

```python
from app.services.description_normalizer import DescriptionNormalizer

normalizer = DescriptionNormalizer()

# Normalize description
original = "Bê tông lót móng, chiều rộng <= 250 cm, M100"
normalized = normalizer.normalize(original)
# Output: "Đổ bê tông lót móng - M100 đá 4x6"

# For search indexing
normalized_lower = normalized.lower()
# Output: "đổ bê tông lót móng - m100 đá 4x6"
```

### Phase 3: Similarity Detection

```
┌──────────────────────────────────────────────────────────┐
│ SIMILARITY MATCHING                                      │
└──────────────────────────────────────────────────────────┘

Algorithm: Exact Match (Phase 1)
    │
    ├─> Match Criteria (ALL must match):
    │   1. description_normalized (exact, case-insensitive)
    │   2. sec_code (same classification)
    │   3. unit_standard (same unit)
    │
    └─> Example:
        Item A: "đổ bê tông móng - m200", SEC-02-01, m3
        Item B: "đổ bê tông móng - m200", SEC-02-01, m3
        → MATCH ✅

        Item C: "đổ bê tông móng - m300", SEC-02-01, m3
        → NO MATCH (different grade) ❌

Future: Fuzzy Match (Phase 2)
    │
    ├─> Levenshtein distance < 3
    ├─> Cosine similarity > 0.9
    ├─> Same category keywords
    └─> Manual review queue
```

**Code Implementation:**

```python
def find_similar_master(
    description_normalized: str,
    sec_code: str,
    unit: str
) -> Optional[MasterWorkItem]:
    """
    Find existing master item that matches criteria
    """
    return db.query(MasterWorkItem).filter(
        MasterWorkItem.description_normalized == description_normalized.lower(),
        MasterWorkItem.sec_code == sec_code,
        MasterWorkItem.unit_standard == unit,
        MasterWorkItem.is_active == True
    ).first()
```

### Phase 4: Merge Strategy

```
┌──────────────────────────────────────────────────────────┐
│ MERGE OR CREATE                                          │
└──────────────────────────────────────────────────────────┘

If MATCH found (existing master_item):
    │
    ├─> UPDATE Pricing
    │   │
    │   ├─> ref_unit_price_min = MIN(current_min, new_price)
    │   ├─> ref_unit_price_max = MAX(current_max, new_price)
    │   └─> ref_unit_price_avg = RECALCULATE
    │           │
    │           └─> Formula:
    │               total = current_avg * occurrence_count + new_price
    │               new_avg = total / (occurrence_count + 1)
    │
    ├─> UPDATE Statistics
    │   │
    │   ├─> occurrence_count += 1
    │   └─> source_files.append(new_file_id)
    │
    ├─> UPDATE Timestamp
    │   │
    │   └─> updated_at = NOW()
    │
    └─> Example:
        Before: avg=1,000,000, count=3, min=900k, max=1,100k
        New:    price=1,200,000
        After:  avg=1,050,000, count=4, min=900k, max=1,200k

If NO MATCH (new master_item):
    │
    ├─> GENERATE Work Code
    │   │
    │   └─> WorkCodeGenerator
    │       ├─> SEC prefix: S01, S02, S03, ...
    │       ├─> Category: CONC, REBAR, BRICK, ...
    │       ├─> Sub-category: BEAM, COL, WALL, ...
    │       ├─> Sequence: next available number
    │       └─> Format: S02-CONC-BEAM-0015
    │
    ├─> SET Initial Values
    │   │
    │   ├─> description = normalized
    │   ├─> description_normalized = lowercase
    │   ├─> sec_code = from classification
    │   ├─> unit_standard = standardized unit
    │   ├─> ref_unit_price_min/max/avg = price
    │   ├─> occurrence_count = 1
    │   ├─> source_files = [file_id]
    │   ├─> is_active = TRUE
    │   └─> is_verified = FALSE (pending review)
    │
    └─> INSERT into master_work_items
```

---

## 📊 PRICING INTELLIGENCE

### 1. Price Aggregation

**Statistical Analysis:**
```python
class PricingStats:
    ref_unit_price_min: Decimal     # Minimum observed
    ref_unit_price_max: Decimal     # Maximum observed
    ref_unit_price_avg: Decimal     # Mean
    ref_unit_price_median: Decimal  # Median (future)
    ref_unit_price_stddev: Decimal  # Std deviation (future)

    price_history: List[{
        'price': Decimal,
        'file_id': int,
        'project_id': int,
        'date': datetime,
        'location': str
    }]
```

**Outlier Detection (Future):**
```python
def detect_outliers(prices: List[Decimal]) -> List[bool]:
    """
    IQR method:
    - Q1 = 25th percentile
    - Q3 = 75th percentile
    - IQR = Q3 - Q1
    - Outlier if: price < Q1 - 1.5*IQR or price > Q3 + 1.5*IQR
    """
    q1 = percentile(prices, 25)
    q3 = percentile(prices, 75)
    iqr = q3 - q1

    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    return [p < lower_bound or p > upper_bound for p in prices]
```

### 2. Price Trends

**Time Series Analysis (Future):**
```sql
-- Price trend over time
SELECT
    DATE_FORMAT(created_at, '%Y-%m') as month,
    AVG(unit_price) as avg_price,
    MIN(unit_price) as min_price,
    MAX(unit_price) as max_price,
    COUNT(*) as sample_size
FROM line_items
WHERE sec_code = 'SEC-02-01'  -- Bê tông
GROUP BY month
ORDER BY month DESC
```

**Regional Variation (Future):**
```sql
-- Price by location
SELECT
    p.location,
    AVG(li.unit_price) as avg_price,
    COUNT(DISTINCT li.project_id) as project_count
FROM line_items li
JOIN projects p ON li.project_id = p.project_id
WHERE li.sec_code = 'SEC-02-01'
GROUP BY p.location
```

---

## 🎯 QUALITY CONTROL

### 1. Quality Tiers

**Gold Standard** ⭐⭐⭐
```python
criteria = {
    'is_verified': True,              # Expert verified
    'occurrence_count': >= 10,        # High frequency
    'confidence_score': >= 90%,       # High confidence
    'price_variance': <= 15%,         # Consistent pricing
    'source_diversity': >= 3          # Multiple projects
}
```

**Silver Standard** ⭐⭐
```python
criteria = {
    'occurrence_count': >= 5,
    'confidence_score': >= 80%,
    'price_variance': <= 25%,
}
```

**Bronze Standard** ⭐
```python
criteria = {
    'occurrence_count': >= 2,
    'confidence_score': >= 70%,
}
```

**Pending Review**
```python
criteria = {
    'occurrence_count': 1,
    'is_verified': False,
}
```

### 2. Verification Workflow

```
┌──────────────────────────────────────────────────────────┐
│ VERIFICATION PIPELINE                                    │
└──────────────────────────────────────────────────────────┘

Auto-generated Master Items
    │
    ├─> is_verified = FALSE (default)
    │
    └─> Review Queue (filtered by):
            ├─> High occurrence (>= 5)
            ├─> High value items (price > threshold)
            ├─> Ambiguous classification (confidence < 80%)
            └─> User flagged items

Expert Review:
    │
    ├─> Check Description
    │   ├─> Is normalization correct?
    │   ├─> Is template applied correctly?
    │   └─> Any missing information?
    │
    ├─> Verify Classification
    │   ├─> Is SEC code correct?
    │   ├─> Should it be reclassified?
    │   └─> Add to training data if wrong
    │
    ├─> Validate Pricing
    │   ├─> Are prices reasonable?
    │   ├─> Any outliers to remove?
    │   └─> Regional factors considered?
    │
    ├─> Standardize Unit
    │   ├─> Is unit correct?
    │   ├─> Add unit variants
    │   └─> Conversion factors
    │
    └─> Actions:
            ├─> Approve → is_verified = TRUE
            ├─> Edit → Update and approve
            ├─> Reject → is_active = FALSE
            └─> Split → Create multiple masters

Verified Master Items
    │
    ├─> is_verified = TRUE
    ├─> verified_by = user_id
    ├─> verified_at = timestamp
    └─> Quality Tier = Gold/Silver/Bronze
```

### 3. Data Quality Metrics

**Coverage Metrics:**
```python
total_line_items = COUNT(line_items)
matched_to_master = COUNT(line_items WHERE master_id IS NOT NULL)
coverage_rate = matched_to_master / total_line_items

# Target: > 80%
```

**Accuracy Metrics:**
```python
correct_classifications = COUNT(WHERE manual_review = auto_classification)
total_reviewed = COUNT(manual_reviews)
classification_accuracy = correct_classifications / total_reviewed

# Target: > 85%
```

**Deduplication Metrics:**
```python
unique_descriptions_before = COUNT(DISTINCT description FROM line_items)
unique_descriptions_after = COUNT(master_work_items)
deduplication_rate = 1 - (after / before)

# Target: > 70%
```

---

## 🔍 SEARCH & DISCOVERY

### 1. Search Strategies

**Full-Text Search:**
```sql
-- MySQL FULLTEXT search
SELECT *
FROM master_work_items
WHERE MATCH(description) AGAINST('bê tông móng' IN NATURAL LANGUAGE MODE)
  AND is_active = TRUE
ORDER BY occurrence_count DESC
LIMIT 20;
```

**Faceted Search:**
```sql
-- By SEC code + category
SELECT *
FROM master_work_items
WHERE sec_code LIKE 'SEC-02%'      -- Superstructure
  AND description_normalized LIKE '%bê tông%'
  AND unit_standard = 'm3'
  AND is_active = TRUE;
```

**Price Range Search:**
```sql
-- Find items within budget
SELECT *
FROM master_work_items
WHERE ref_unit_price_avg BETWEEN :min_price AND :max_price
  AND sec_code = :sec_code
  AND is_active = TRUE;
```

### 2. Similar Items Discovery

**Find Similar (Future - ML based):**
```python
def find_similar_items(master_id: int, top_k: int = 5):
    """
    Find similar master items using:
    1. Same SEC code (category)
    2. TF-IDF similarity on description
    3. Price similarity
    4. Unit similarity
    """
    target = get_master_item(master_id)

    candidates = get_masters_by_sec(target.sec_code)

    # Calculate TF-IDF similarity
    similarities = calculate_tfidf_similarity(
        target.description,
        [c.description for c in candidates]
    )

    # Sort by similarity
    ranked = sorted(zip(candidates, similarities),
                   key=lambda x: x[1],
                   reverse=True)

    return ranked[:top_k]
```

---

## 📈 ANALYTICS & REPORTING

### 1. Master Database Dashboard

**Key Metrics:**
```python
dashboard = {
    'total_masters': COUNT(master_work_items WHERE is_active=TRUE),
    'verified_masters': COUNT(WHERE is_verified=TRUE),
    'total_sources': COUNT(DISTINCT source_files),
    'coverage_rate': matched / total * 100,
    'avg_occurrence': AVG(occurrence_count),

    'by_sec_code': {
        'SEC-01': {count, verified, avg_price},
        'SEC-02': {count, verified, avg_price},
        ...
    },

    'quality_distribution': {
        'Gold': count_gold,
        'Silver': count_silver,
        'Bronze': count_bronze,
        'Pending': count_pending
    },

    'recent_additions': last_30_days,
    'price_updates': updated_last_week,
}
```

### 2. Comparison Reports

**Project Comparison:**
```sql
-- Compare master prices with project actual
SELECT
    m.work_code,
    m.description,
    m.ref_unit_price_avg as master_price,
    li.unit_price as project_price,
    (li.unit_price - m.ref_unit_price_avg) / m.ref_unit_price_avg * 100 as variance_pct
FROM master_work_items m
JOIN line_items li ON li.description_normalized = m.description_normalized
WHERE li.project_id = :project_id
  AND ABS(variance_pct) > 10  -- Significant variance
ORDER BY ABS(variance_pct) DESC;
```

**Market Intelligence:**
```sql
-- Price trends by category
SELECT
    sec_code,
    AVG(ref_unit_price_avg) as avg_price,
    STDDEV(ref_unit_price_avg) as price_stddev,
    COUNT(*) as item_count,
    SUM(occurrence_count) as total_occurrences
FROM master_work_items
WHERE is_active = TRUE
  AND occurrence_count >= 3  -- Reliable data only
GROUP BY sec_code
ORDER BY avg_price DESC;
```

---

## 🔄 MAINTENANCE STRATEGY

### 1. Regular Updates

**Daily:**
- Process new BOQ uploads
- Build masters from new files
- Update occurrence counts

**Weekly:**
- Review pending masters (high priority)
- Update pricing statistics
- Clean up duplicates

**Monthly:**
- Full quality audit
- Update SEC keywords
- Retrain classification model (future)
- Archive inactive items

**Quarterly:**
- Market analysis report
- Price trend analysis
- System performance review

### 2. Cleanup Operations

**Deactivate Low-Quality:**
```sql
-- Mark low-quality masters as inactive
UPDATE master_work_items
SET is_active = FALSE
WHERE occurrence_count = 1
  AND created_at < DATE_SUB(NOW(), INTERVAL 6 MONTH)
  AND is_verified = FALSE;
```

**Merge Duplicates:**
```sql
-- Find potential duplicates
SELECT
    description_normalized,
    COUNT(*) as dup_count,
    GROUP_CONCAT(master_id) as master_ids
FROM master_work_items
WHERE is_active = TRUE
GROUP BY description_normalized, sec_code, unit_standard
HAVING dup_count > 1;
```

### 3. Version Control

**Master Item History (Future):**
```sql
CREATE TABLE master_work_items_history (
    history_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    master_id INT NOT NULL,
    change_type ENUM('create', 'update', 'delete', 'verify'),
    field_changed VARCHAR(50),
    old_value TEXT,
    new_value TEXT,
    changed_by INT,
    changed_at TIMESTAMP,

    INDEX idx_master (master_id),
    INDEX idx_date (changed_at)
);
```

---

## 🚀 OPTIMIZATION

### 1. Database Optimization

**Indexes:**
```sql
-- Critical indexes for performance
CREATE INDEX idx_master_search ON master_work_items(
    sec_code,
    unit_standard,
    is_active
);

CREATE FULLTEXT INDEX idx_description_ft ON master_work_items(description);

CREATE INDEX idx_normalized ON master_work_items(description_normalized);
```

**Query Optimization:**
```sql
-- Use covering index for common queries
CREATE INDEX idx_master_summary ON master_work_items(
    master_id,
    work_code,
    description_normalized,
    sec_code,
    unit_standard,
    ref_unit_price_avg,
    occurrence_count,
    is_verified
);
```

### 2. Caching Strategy (Future)

**Redis Cache:**
```python
# Cache frequently accessed masters
cache_key = f"master:{master_id}"
cache.setex(cache_key, 3600, json.dumps(master_data))

# Cache search results
search_key = f"search:{hash(query_params)}"
cache.setex(search_key, 300, json.dumps(results))

# Cache statistics
stats_key = "dashboard:stats"
cache.setex(stats_key, 600, json.dumps(dashboard))
```

### 3. Batch Processing

**Bulk Build:**
```python
def build_master_bulk(file_ids: List[int], batch_size: int = 1000):
    """
    Process multiple files in batches
    """
    for file_id in file_ids:
        line_items = get_line_items(file_id)

        for batch in chunks(line_items, batch_size):
            # Process batch
            process_batch(batch)

            # Commit transaction
            db.commit()

            # Log progress
            logger.info(f"Processed {len(batch)} items from file {file_id}")
```

---

## 📚 BEST PRACTICES

### 1. Data Entry

✅ **DO:**
- Always normalize before storing
- Validate classification confidence
- Check for duplicates before insert
- Log all changes in audit trail
- Use transactions for consistency

❌ **DON'T:**
- Store raw unprocessed data in master
- Skip normalization step
- Accept low-confidence classifications
- Mix different units for same item
- Override verified data without review

### 2. Quality Assurance

✅ **DO:**
- Review high-value items manually
- Verify high-frequency items
- Check outlier prices
- Maintain audit trail
- Use version control

❌ **DON'T:**
- Auto-verify without human review
- Ignore price anomalies
- Delete data (mark inactive instead)
- Skip documentation
- Mix verified and unverified data

### 3. Performance

✅ **DO:**
- Use appropriate indexes
- Batch operations where possible
- Cache frequently accessed data
- Monitor query performance
- Optimize for common queries

❌ **DON'T:**
- Run full table scans
- Execute N+1 queries
- Fetch unnecessary data
- Skip pagination
- Ignore slow query logs

---

## 🎯 SUCCESS METRICS

### Target KPIs

```python
success_criteria = {
    # Data Quality
    'coverage_rate': {
        'target': '> 80%',
        'current': '~70%',
        'trend': 'improving'
    },

    'classification_accuracy': {
        'target': '> 85%',
        'current': '~75%',
        'trend': 'stable'
    },

    'deduplication_rate': {
        'target': '> 70%',
        'current': '~65%',
        'trend': 'improving'
    },

    # Verification
    'verified_rate': {
        'target': '> 50%',
        'current': '~20%',
        'trend': 'growing'
    },

    # Performance
    'build_time_per_1000_items': {
        'target': '< 60s',
        'current': '~45s',
        'trend': 'stable'
    },

    'search_response_time': {
        'target': '< 500ms',
        'current': '~300ms',
        'trend': 'good'
    },

    # Adoption
    'active_masters': {
        'target': '> 10,000',
        'current': '~2,000',
        'trend': 'growing'
    },

    'source_files_count': {
        'target': '> 100',
        'current': '~30',
        'trend': 'growing'
    }
}
```

---

## 📖 IMPLEMENTATION CHECKLIST

### Phase 1: Foundation ✅
- [x] Create master_work_items table
- [x] Implement MasterDataService
- [x] Build master from single file
- [x] Basic pricing aggregation
- [x] Work code generation

### Phase 2: Quality ✅
- [x] Description normalization (Phương án 5)
- [x] Category-specific templates
- [x] Duplicate detection (exact match)
- [x] Test suite

### Phase 3: Enhancement (Current)
- [ ] Fuzzy duplicate detection
- [ ] Outlier detection
- [ ] Verification workflow UI
- [ ] Quality tier classification
- [ ] Batch build operations

### Phase 4: Intelligence (Next)
- [ ] ML classification integration
- [ ] Price prediction
- [ ] Trend analysis
- [ ] Similar items recommendation
- [ ] Auto-correction suggestions

### Phase 5: Integration (Future)
- [ ] BIM synchronization
- [ ] Real-time collaboration
- [ ] API for external systems
- [ ] Mobile access
- [ ] Market intelligence dashboard

---

**Document Version:** 1.0
**Last Updated:** 2026-02-02
**Status:** Master Data Strategy Defined
**Next Review:** March 2026
