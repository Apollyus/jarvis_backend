"""
Test Redis Session Management
Rychlý test zda sessions fungují správně s Redis
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE = "http://localhost:8000"
API_KEY = os.getenv("API_KEY")

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def test_health():
    """Test health check s Redis statusem"""
    print("🏥 Test: Health Check")
    resp = requests.get(f"{API_BASE}/health")
    data = resp.json()
    print(f"   Status: {data['status']}")
    print(f"   Redis: {data['redis']}")
    assert data['redis'] == 'connected', "Redis není připojen!"
    print("   ✅ PASS\n")

def test_auto_session_creation():
    """Test automatického vytváření session ID"""
    print("🆕 Test: Auto Session Creation")
    
    # První zpráva BEZ session_id
    resp = requests.post(
        f"{API_BASE}/api/chat",
        headers=headers,
        json={"message": "Ahoj, toto je test"}
    )
    data = resp.json()
    
    session_id = data.get("session_id")
    print(f"   Backend vytvořil session: {session_id}")
    assert session_id is not None, "Backend nevytvořil session_id!"
    assert session_id.startswith("sess_"), "Neplatný formát session_id!"
    print("   ✅ PASS\n")
    
    return session_id

def test_session_persistence(session_id):
    """Test že session si pamatuje kontext"""
    print("💾 Test: Session Persistence")
    
    # Další zpráva SE STEJNÝM session_id
    resp = requests.post(
        f"{API_BASE}/api/chat",
        headers=headers,
        json={
            "message": "Pamatuješ si co jsem řekl?",
            "session_id": session_id
        }
    )
    data = resp.json()
    
    print(f"   Odpověď: {data['response'][:100]}...")
    print("   ✅ PASS\n")

def test_session_info(session_id):
    """Test získání info o session"""
    print("ℹ️  Test: Session Info")
    
    resp = requests.get(
        f"{API_BASE}/api/sessions/{session_id}",
        headers=headers
    )
    data = resp.json()
    
    print(f"   Session ID: {data['session_id']}")
    print(f"   Počet zpráv: {data['message_count']}")
    print(f"   Poslední aktivita: {data['updated_at']}")
    print(f"   Vyprší za: {data.get('expires_in_seconds', 'N/A')} sekund")
    assert data['message_count'] >= 2, "Session by měla mít alespoň 2 zprávy!"
    print("   ✅ PASS\n")

def test_session_history(session_id):
    """Test načtení historie"""
    print("📜 Test: Session History")
    
    resp = requests.get(
        f"{API_BASE}/api/sessions/{session_id}/history",
        headers=headers
    )
    data = resp.json()
    
    print(f"   Celkem zpráv: {data['message_count']}")
    for i, msg in enumerate(data['history'][:4], 1):
        role = msg['role'].upper()
        content = msg['content'][:50]
        print(f"   {i}. {role}: {content}...")
    
    print("   ✅ PASS\n")

def test_list_sessions():
    """Test listování sessions"""
    print("📋 Test: List Sessions")
    
    resp = requests.get(
        f"{API_BASE}/api/sessions",
        headers=headers
    )
    data = resp.json()
    
    print(f"   Celkem aktivních sessions: {data['count']}")
    for session in data['sessions'][:5]:
        print(f"   - {session}")
    
    print("   ✅ PASS\n")
    return data['sessions']

def test_new_session_endpoint():
    """Test vytvoření nové session přes endpoint"""
    print("🎯 Test: New Session Endpoint")
    
    resp = requests.post(
        f"{API_BASE}/api/sessions/new",
        headers=headers
    )
    data = resp.json()
    
    print(f"   Vytvořeno: {data['session_id']}")
    print(f"   Message: {data['message']}")
    assert data['session_id'].startswith("sess_"), "Neplatný formát!"
    print("   ✅ PASS\n")
    
    return data['session_id']

def test_delete_session(session_id):
    """Test smazání session"""
    print("🗑️  Test: Delete Session")
    
    resp = requests.delete(
        f"{API_BASE}/api/sessions/{session_id}",
        headers=headers
    )
    data = resp.json()
    
    print(f"   {data['message']}")
    
    # Ověř že session neexistuje
    resp = requests.get(
        f"{API_BASE}/api/sessions/{session_id}",
        headers=headers
    )
    assert resp.status_code == 404, "Session by měla být smazaná!"
    print("   ✅ PASS\n")

def main():
    print("=" * 60)
    print("  REDIS SESSION MANAGEMENT TESTS")
    print("=" * 60 + "\n")
    
    try:
        # 1. Health check
        test_health()
        
        # 2. Auto session creation
        session1 = test_auto_session_creation()
        
        # 3. Session persistence
        test_session_persistence(session1)
        
        # 4. Session info
        test_session_info(session1)
        
        # 5. Session history
        test_session_history(session1)
        
        # 6. List sessions
        all_sessions = test_list_sessions()
        
        # 7. New session endpoint
        session2 = test_new_session_endpoint()
        
        # 8. Delete session
        test_delete_session(session2)
        
        print("=" * 60)
        print("  ✅ VŠECHNY TESTY PROŠLY!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ TEST SELHAL: {e}")
    except requests.exceptions.ConnectionError:
        print("\n❌ CHYBA: Nelze se připojit k API na http://localhost:8000")
        print("   Ujisti se, že server běží: python main.py")
    except Exception as e:
        print(f"\n❌ NEOČEKÁVANÁ CHYBA: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
