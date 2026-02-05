"""
Model Performance Checker
Checks if the current LLM model is working properly and suggests fixes
"""
import requests
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_URL = "http://localhost:8000/agent/query"

# Simple test query
SIMPLE_TEST = {
    "query": "Lấy danh sách khách hàng",
    "execute": False
}

# Medium complexity test
MEDIUM_TEST = {
    "query": "Lấy họ tên khách hàng có số giấy tờ định danh cá nhân = 001201015338",
    "execute": False
}


def check_api_health():
    """Check if API is running"""
    try:
        response = requests.get("http://localhost:8000/docs", timeout=5)
        if response.status_code == 200:
            logger.info("✅ API is running")
            return True
        else:
            logger.error(f"❌ API returned status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Cannot connect to API: {e}")
        logger.error("Make sure API is running: python main_mcp.py")
        return False


def test_simple_query():
    """Test simple query"""
    logger.info("\n" + "="*60)
    logger.info("TEST 1: Simple Query")
    logger.info("="*60)
    
    try:
        response = requests.post(API_URL, json=SIMPLE_TEST, timeout=30)
        result = response.json()
        
        sql = result.get("sql", "")
        success = result.get("success", False)
        
        logger.info(f"Success: {success}")
        logger.info(f"SQL: {sql}")
        
        if not success or not sql:
            logger.error("❌ FAILED: Simple query failed")
            logger.error(f"Response: {json.dumps(result, indent=2)}")
            return False
        
        logger.info("✅ PASSED: Simple query works")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False


def test_medium_query():
    """Test medium complexity query"""
    logger.info("\n" + "="*60)
    logger.info("TEST 2: Medium Query (with WHERE clause)")
    logger.info("="*60)
    
    try:
        response = requests.post(API_URL, json=MEDIUM_TEST, timeout=30)
        result = response.json()
        
        sql = result.get("sql", "")
        success = result.get("success", False)
        
        logger.info(f"Success: {success}")
        logger.info(f"SQL: {sql}")
        
        if not success or not sql:
            logger.error("❌ FAILED: Medium query failed")
            logger.error(f"Response: {json.dumps(result, indent=2)}")
            return False
        
        # Check for schema prefix
        if "." not in sql:
            logger.warning("⚠️  WARNING: SQL missing schema prefix (e.g., DATA.TABLE)")
        
        # Check for WHERE clause
        if "WHERE" not in sql.upper():
            logger.warning("⚠️  WARNING: SQL missing WHERE clause")
        
        logger.info("✅ PASSED: Medium query works")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False


def suggest_fixes():
    """Suggest fixes based on common issues"""
    logger.info("\n" + "="*60)
    logger.info("SUGGESTIONS FOR HAIKU & SMALL MODELS")
    logger.info("="*60)
    
    suggestions = [
        "1. Lower temperature: Set LLM_TEMPERATURE=0.1 in .env",
        "2. Increase max_tokens: Set LLM_MAX_TOKENS=2048 in .env",
        "3. Try different model:",
        "   - For Ollama: OLLAMA_MODEL=qwen2.5:14b or mistral-nemo",
        "   - For ChatGPT: CHATGPT_MODEL=gpt-4 or gpt-3.5-turbo",
        "4. Check if model supports JSON mode:",
        "   - Claude Haiku: Works but needs simple prompts",
        "   - GPT models: Use JSON mode with response_format",
        "5. Verify database metadata is loaded correctly",
        "6. Check DATAMODEL_PATH points to valid JSON file",
    ]
    
    for suggestion in suggestions:
        logger.info(suggestion)
    
    logger.info("\nExample .env settings for Haiku:")
    logger.info("LLM_PROVIDER=chatgpt")
    logger.info("CHATGPT_MODEL=claude-3-haiku-20240307")
    logger.info("LLM_TEMPERATURE=0.1")
    logger.info("LLM_MAX_TOKENS=2048")


def main():
    """Run all checks"""
    logger.info("Model Performance Checker")
    logger.info("="*60)
    
    # Check 1: API Health
    if not check_api_health():
        return
    
    # Check 2: Simple Query
    simple_ok = test_simple_query()
    
    # Check 3: Medium Query
    medium_ok = test_medium_query()
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("SUMMARY")
    logger.info("="*60)
    
    if simple_ok and medium_ok:
        logger.info("✅ All tests PASSED - Model is working well!")
    elif simple_ok:
        logger.info("⚠️  Simple queries work, but complex queries fail")
        logger.info("Model may need better prompts or different settings")
        suggest_fixes()
    else:
        logger.error("❌ Model is NOT working properly")
        logger.error("Basic queries are failing")
        suggest_fixes()


if __name__ == "__main__":
    main()
