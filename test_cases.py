"""
Test Cases for RAG SQL Pipeline
Tests various scenarios to ensure robust SQL generation
"""
import json
import logging
from typing import List, Dict
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API endpoint
API_URL = "http://localhost:8000/agent/query"

# Test cases covering various scenarios
TEST_CASES = [
    {
        "name": "Simple WHERE with exact value",
        "query": "Lấy danh sách khách hàng có số giấy tờ định danh cá nhân = 001201015338",
        "expected_keywords": ["SELECT", "FROM", "WHERE", "IDENTN_DOC_NBR", "001201015338"],
        "should_contain_schema": True
    },
    {
        "name": "SELECT specific columns",
        "query": "Lấy họ tên và địa chỉ khách hàng có mã khách hàng = KH001",
        "expected_keywords": ["SELECT", "FROM", "WHERE"],
        "should_contain_schema": True
    },
    {
        "name": "Simple SELECT all",
        "query": "Lấy tất cả thông tin khách hàng",
        "expected_keywords": ["SELECT", "FROM"],
        "should_contain_schema": True
    },
    {
        "name": "COUNT query",
        "query": "Đếm số lượng khách hàng",
        "expected_keywords": ["SELECT", "COUNT", "FROM"],
        "should_contain_schema": True
    },
    {
        "name": "JOIN query",
        "query": "Lấy danh sách khách hàng và thông tin tài khoản của họ",
        "expected_keywords": ["SELECT", "FROM", "JOIN"],
        "should_contain_schema": True
    },
    {
        "name": "ORDER BY query",
        "query": "Lấy danh sách khách hàng sắp xếp theo tên",
        "expected_keywords": ["SELECT", "FROM", "ORDER BY"],
        "should_contain_schema": True
    },
    {
        "name": "LIMIT query",
        "query": "Lấy 10 khách hàng đầu tiên",
        "expected_keywords": ["SELECT", "FROM", "LIMIT"],
        "should_contain_schema": True
    },
]


def run_test_case(test_case: Dict) -> Dict:
    """Run a single test case"""
    logger.info(f"\n{'='*80}")
    logger.info(f"TEST: {test_case['name']}")
    logger.info(f"Query: {test_case['query']}")
    logger.info(f"{'='*80}")
    
    try:
        response = requests.post(
            API_URL,
            headers={"Content-Type": "application/json"},
            json={"query": test_case["query"], "execute": False},
            timeout=30
        )
        
        if response.status_code != 200:
            logger.error(f"❌ HTTP Error: {response.status_code}")
            return {
                "name": test_case["name"],
                "status": "FAILED",
                "error": f"HTTP {response.status_code}",
                "sql": None
            }
        
        result = response.json()
        
        # Check if SQL was generated
        sql = result.get("sql", "")
        if not sql:
            logger.error(f"❌ No SQL generated")
            logger.error(f"Response: {json.dumps(result, indent=2)}")
            return {
                "name": test_case["name"],
                "status": "FAILED",
                "error": "No SQL generated",
                "sql": None,
                "response": result
            }
        
        logger.info(f"✅ SQL Generated:\n{sql}")
        
        # Validate SQL contains expected keywords
        sql_upper = sql.upper()
        missing_keywords = []
        for keyword in test_case.get("expected_keywords", []):
            if keyword.upper() not in sql_upper:
                missing_keywords.append(keyword)
        
        # Check schema prefix
        has_schema = "." in sql and any(
            schema in sql.upper() 
            for schema in ["DATA.", "RPT.", "SCHEMA."]
        )
        
        if test_case.get("should_contain_schema") and not has_schema:
            logger.warning(f"⚠️  Missing schema prefix in SQL")
        
        if missing_keywords:
            logger.warning(f"⚠️  Missing expected keywords: {missing_keywords}")
            return {
                "name": test_case["name"],
                "status": "PARTIAL",
                "sql": sql,
                "missing_keywords": missing_keywords,
                "has_schema": has_schema
            }
        
        logger.info(f"✅ All validations passed")
        return {
            "name": test_case["name"],
            "status": "PASSED",
            "sql": sql,
            "has_schema": has_schema
        }
        
    except requests.Timeout:
        logger.error(f"❌ Request timeout")
        return {
            "name": test_case["name"],
            "status": "FAILED",
            "error": "Timeout",
            "sql": None
        }
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return {
            "name": test_case["name"],
            "status": "FAILED",
            "error": str(e),
            "sql": None
        }


def run_all_tests():
    """Run all test cases"""
    logger.info("\n" + "="*80)
    logger.info("STARTING TEST SUITE")
    logger.info("="*80 + "\n")
    
    results = []
    for test_case in TEST_CASES:
        result = run_test_case(test_case)
        results.append(result)
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("TEST SUMMARY")
    logger.info("="*80)
    
    passed = sum(1 for r in results if r["status"] == "PASSED")
    partial = sum(1 for r in results if r["status"] == "PARTIAL")
    failed = sum(1 for r in results if r["status"] == "FAILED")
    total = len(results)
    
    logger.info(f"Total: {total}")
    logger.info(f"✅ Passed: {passed}")
    logger.info(f"⚠️  Partial: {partial}")
    logger.info(f"❌ Failed: {failed}")
    logger.info(f"Success Rate: {(passed/total)*100:.1f}%")
    
    # Detailed failures
    if failed > 0 or partial > 0:
        logger.info("\nFailed/Partial Tests:")
        for r in results:
            if r["status"] in ["FAILED", "PARTIAL"]:
                logger.info(f"  - {r['name']}: {r.get('error', r.get('missing_keywords', 'Unknown'))}")
    
    return results


if __name__ == "__main__":
    results = run_all_tests()
    
    # Save results to file
    with open("test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\nResults saved to test_results.json")
