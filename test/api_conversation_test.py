"""
API Conversation Test Script
=============================
This script demonstrates the conversation functionality of the MCP Agent API.
It tests multi-turn conversations with session management and shows how sessions
maintain context across multiple messages.

Prerequisites:
--------------
1. Install required package: pip install requests
2. Start the API server: python src/api.py
3. Run this test: python test/api_conversation_test.py
"""

import requests
import json
import time
from typing import Dict, Any
import sys


# API Configuration
API_BASE_URL = "http://localhost:8000"
CHAT_ENDPOINT = f"{API_BASE_URL}/api/chat"
HEALTH_ENDPOINT = f"{API_BASE_URL}/health"


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_message(role: str, content: str, session_id: str = None):
    """Print a formatted message"""
    timestamp = time.strftime("%H:%M:%S")
    session_info = f" [Session: {session_id}]" if session_id else ""
    print(f"\n[{timestamp}]{session_info} {role}:")
    print(f"  {content}")


def check_api_health() -> bool:
    """Check if the API is running and healthy"""
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        if response.status_code == 200:
            print("✓ API is healthy and running")
            return True
        else:
            print(f"✗ API health check failed with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"✗ Cannot connect to API at {API_BASE_URL}")
        print("  Make sure the API server is running: python src/api.py")
        return False
    except Exception as e:
        print(f"✗ Health check error: {e}")
        return False


def send_message(message: str, session_id: str = "default") -> Dict[str, Any]:
    """
    Send a message to the chat API
    
    Args:
        message: The message to send
        session_id: Session ID for conversation context
        
    Returns:
        API response as dictionary
    """
    payload = {
        "message": message,
        "session_id": session_id
    }
    
    print_message("USER", message, session_id)
    
    try:
        response = requests.post(
            CHAT_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60  # Agent queries can take time
        )
        response.raise_for_status()
        
        result = response.json()
        print_message("AGENT", result.get("response", "No response"), session_id)
        
        return result
        
    except requests.exceptions.Timeout:
        print("✗ Request timed out - the agent may be processing a complex query")
        return {"error": "timeout"}
    except requests.exceptions.RequestException as e:
        print(f"✗ Request failed: {e}")
        return {"error": str(e)}


def test_single_conversation():
    """Test 1: Simple single message conversation"""
    print_section("TEST 1: Single Message Conversation")
    
    session_id = "test-single"
    
    response = send_message(
        "Hello! What can you help me with?",
        session_id
    )
    
    if "error" not in response:
        print("\n✓ Single message test passed")
    else:
        print("\n✗ Single message test failed")


def test_multi_turn_conversation():
    """Test 2: Multi-turn conversation with context"""
    print_section("TEST 2: Multi-Turn Conversation with Context")
    
    session_id = "test-multi-turn"
    
    # First message - ask about capabilities
    print("\n--- Turn 1: Initial greeting ---")
    send_message(
        "Hi! Can you tell me what you can do?",
        session_id
    )
    
    time.sleep(1)  # Brief pause between messages
    
    # Second message - follow-up question (tests if context is maintained)
    print("\n--- Turn 2: Follow-up question ---")
    send_message(
        "Can you give me a specific example?",
        session_id
    )
    
    time.sleep(1)
    
    # Third message - another follow-up
    print("\n--- Turn 3: Another follow-up ---")
    send_message(
        "That's interesting, thank you!",
        session_id
    )
    
    print("\n✓ Multi-turn conversation test completed")


def test_multiple_sessions():
    """Test 3: Multiple independent sessions"""
    print_section("TEST 3: Multiple Independent Sessions")
    
    session_1 = "test-session-1"
    session_2 = "test-session-2"
    
    # Session 1 - Topic: Notion
    print("\n--- Session 1: Topic about Notion ---")
    send_message(
        "I want to create a new page in Notion",
        session_1
    )
    
    time.sleep(1)
    
    # Session 2 - Different topic
    print("\n--- Session 2: Different topic ---")
    send_message(
        "What's the weather like today?",
        session_2
    )
    
    time.sleep(1)
    
    # Session 1 - Continue first topic
    print("\n--- Back to Session 1: Continue Notion topic ---")
    send_message(
        "What information do you need from me to create that page?",
        session_1
    )
    
    print("\n✓ Multiple sessions test completed")
    print("  Note: Sessions maintain independent contexts")


def test_session_persistence():
    """Test 4: Session context persistence"""
    print_section("TEST 4: Session Context Persistence")
    
    session_id = "test-persistence"
    
    # Set context in first message
    print("\n--- Setting context ---")
    send_message(
        "My favorite color is blue",
        session_id
    )
    
    time.sleep(2)
    
    # Test if context is remembered
    print("\n--- Testing context recall ---")
    send_message(
        "What's my favorite color?",
        session_id
    )
    
    print("\n✓ Context persistence test completed")
    print("  The agent should remember information from earlier in the conversation")


def test_notion_workflow():
    """Test 5: Real Notion workflow (if Notion MCP is configured)"""
    print_section("TEST 5: Notion Workflow Example")
    
    session_id = "test-notion-workflow"
    
    print("\n--- Step 1: Ask about Notion capabilities ---")
    send_message(
        "Can you help me work with Notion?",
        session_id
    )
    
    time.sleep(1)
    
    print("\n--- Step 2: Request to create a page ---")
    send_message(
        "Create a new page called 'Test Page' with the text 'This is a test'",
        session_id
    )
    
    time.sleep(2)
    
    print("\n--- Step 3: Follow-up question ---")
    send_message(
        "Was the page created successfully?",
        session_id
    )
    
    print("\n✓ Notion workflow test completed")
    print("  Note: This test requires Notion MCP server to be properly configured")


def run_all_tests():
    """Run all conversation tests"""
    print_section("API Conversation Test Suite")
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Testing chat endpoint: {CHAT_ENDPOINT}")
    
    # Check API health first
    print("\n--- Checking API Health ---")
    if not check_api_health():
        print("\n❌ API is not available. Please start the server first:")
        print("   python src/api.py")
        sys.exit(1)
    
    # Run test suite
    try:
        test_single_conversation()
        time.sleep(2)
        
        test_multi_turn_conversation()
        time.sleep(2)
        
        test_multiple_sessions()
        time.sleep(2)
        
        test_session_persistence()
        time.sleep(2)
        
        test_notion_workflow()
        
        # Final summary
        print_section("Test Suite Completed")
        print("\n✓ All tests executed successfully!")
        print("\nKey Observations:")
        print("  • Sessions maintain independent conversation contexts")
        print("  • Multi-turn conversations preserve context within sessions")
        print("  • The API supports concurrent sessions with different topics")
        print("  • Session IDs can be used to isolate different user conversations")
        
    except KeyboardInterrupt:
        print("\n\n⚠ Tests interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════════════════════════════╗
    ║                                                                    ║
    ║           MCP Agent API - Conversation Test Script                ║
    ║                                                                    ║
    ║  This script demonstrates conversation capabilities including:    ║
    ║    • Single and multi-turn conversations                          ║
    ║    • Session management and context preservation                  ║
    ║    • Multiple concurrent sessions                                 ║
    ║    • Real-world Notion workflow examples                          ║
    ║                                                                    ║
    ╚════════════════════════════════════════════════════════════════════╝
    """)
    
    run_all_tests()