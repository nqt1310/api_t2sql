# SQL Generation Fix Summary

## Issues Fixed

### 1. **JSON Output Format Enforcement** ✅
**Problem**: LLM was returning raw SQL instead of JSON format
```
❌ Before: SELECT * FROM PRIM_PARTY WHERE IDENTN_DOC_NBR = '001201015338';
✅ After: {"cau_lenh_sql_theo_yeu_cau_nghiep_vu": "SELECT * FROM DATA.PRIM_PARTY WHERE IDENTN_DOC_NBR = '001201015338';"}
```

**Solution Implemented**:
- Updated [base/rag_core.py](base/rag_core.py) `generate_sql_query()` method (lines 103-125)
- Changed from direct `invoke()` to **piped chain pattern**: `prompt | llm | parser`
- Added dual fallback strategy:
  1. Try piped chain first (better JSON enforcement)
  2. Fall back to direct invoke if chain fails

### 2. **Schema Prefix Enforcement** ✅
**Problem**: SQL queries missing schema prefix (e.g., `PRIM_PARTY` instead of `DATA.PRIM_PARTY`)

**Solution Implemented**:
- Enhanced [base/prompt_temp.py](base/prompt_temp.py) lines 40-95 with:
  - CRITICAL requirements section (lines 54-59)
  - Explicit schema prefix rules: "ALWAYS prefix table names with schema"
  - Example output with schema prefixes: `DATA.PRIM_PARTY`, `RPT.RPT_CUST_IDENT_DLY`
  - Clear JSON format requirement with `get_format_instructions()`

- Added schema metadata to [data/datamodel.json](data/datamodel.json):
  - Each table now has `"schema"` field (DATA or RPT)
  - Each table now has `"full_name"` field (e.g., "DATA.PRIM_PARTY")

## Updated Components

### 1. **base/rag_core.py** (Lines 103-125)
```python
# Use piped chain: prompt | llm | parser for better JSON parsing
try:
    chain = prompt | self.llm | self.parser_output
    parsed = chain.invoke({})
    logging.info("[GENERATED SQL] %s", parsed.get("cau_lenh_sql_theo_yeu_cau_nghiep_vu", ""))   
    return parsed.get("cau_lenh_sql_theo_yeu_cau_nghiep_vu", "")
except Exception as e:
    logging.error("[SQL CHAIN PARSE ERROR] %s", e)
    # Fallback: try direct invoke
    try:
        raw_sql = self.llm.invoke(prompt)
        parsed = self.parser_output.parse(raw_sql)
        return parsed.get("cau_lenh_sql_theo_yeu_cau_nghiep_vu", "")
    except Exception as e2:
        logging.error("[SQL FALLBACK PARSE ERROR] %s", e2)
        logging.error(raw_sql)
        return raw_sql
```

### 2. **base/prompt_temp.py** (Lines 54-64)
```
====================
CRITICAL REQUIREMENTS
====================
1. You MUST return ONLY valid JSON format
2. Use ONLY the tables and columns from the datamodel provided above
3. ALWAYS prefix table names with schema (e.g., DATA.PRIM_PARTY, RPT.RPT_CUST_IDENT_DLY)
4. Never use table names without schema prefix
5. Write SQL that is executable on the specified database
6. Do NOT provide any explanation, only the JSON response
```

### 3. **data/datamodel.json** (All 5 tables updated)
Each table now includes schema metadata:
```json
{
  "PRIM_PARTY": {
    "schema": "DATA",
    "full_name": "DATA.PRIM_PARTY",
    "description": "...",
    "columns": {...}
  },
  "RPT_CUST_IDENT_DLY": {
    "schema": "RPT", 
    "full_name": "RPT.RPT_CUST_IDENT_DLY",
    "description": "...",
    "columns": {...}
  }
}
```

## Expected Behavior After Fix

### Input Query:
```
"Lấy danh sách khách hàng có số giấy tờ định danh cá nhân = 001201015338"
```

### Expected Output:
```json
{
  "cau_lenh_sql_theo_yeu_cau_nghiep_vu": "SELECT * FROM DATA.PRIM_PARTY WHERE IDENTN_DOC_NBR = '001201015338';"
}
```

### Key Improvements:
1. ✅ Valid JSON format (key `cau_lenh_sql_theo_yeu_cau_nghiep_vu` present)
2. ✅ Schema prefix included (DATA.PRIM_PARTY)
3. ✅ No markdown code blocks
4. ✅ Proper LangChain chain processing

## Technical Architecture

```
User Query
    ↓
get_related_table_metadata() → Retrieve table schemas
    ↓
generate_sql_query()
    ├─ Format prompt with context
    ├─ Piped Chain: prompt | llm | parser
    │   ├─ Success: Return parsed JSON with SQL ✓
    │   └─ Fail: Try direct invoke
    │       ├─ Success: Return parsed JSON ✓
    │       └─ Fail: Return raw SQL (fallback)
    ↓
Output: {"cau_lenh_sql_theo_yeu_cau_nghiep_vu": "SELECT * FROM DATA.table..."}
```

## Files Modified
- ✅ [base/rag_core.py](base/rag_core.py) - Updated JSON parsing with piped chain
- ✅ [base/prompt_temp.py](base/prompt_temp.py) - Strengthened schema requirements
- ✅ [data/datamodel.json](data/datamodel.json) - Added schema metadata to all tables

## Testing
Run test with:
```bash
python test_sql_gen.py
```

The test validates:
1. LLM initialization with selected provider (Ollama/ChatGPT/vLLM)
2. Schema prefix presence in generated SQL
3. JSON format compliance
4. Proper fallback behavior
