"""
Test přihlašovacího endpointu
Testuje funkčnost /api/auth/login pro získání API klíče
"""
import requests
import json
import os
from dotenv import load_dotenv

# Načíst proměnné prostředí
load_dotenv()

BASE_URL = "http://localhost:8000"
USERNAME = os.getenv("USERNAME", "admin")
PASSWORD = os.getenv("PASSWORD", "your_secure_password_here")

print("=" * 60)
print("Test přihlašovacího endpointu")
print("=" * 60)
print(f"Base URL: {BASE_URL}")
print(f"Username: {USERNAME}")
print("=" * 60)

def test_login_with_valid_credentials():
    """Test přihlášení s platnými údaji"""
    print("\n[TEST 1] Přihlášení s platnými údaji")
    print("-" * 60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "username": USERNAME,
                "password": PASSWORD
            }
        )
        print(f"Status kód: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Odpověď: {json.dumps(data, indent=2, ensure_ascii=False)}")
            api_key = data.get("api_key")
            if api_key:
                print(f"\n✅ ÚSPĚCH: Získán API klíč: {api_key[:20]}...")
                return api_key
            else:
                print("❌ CHYBA: Odpověď neobsahuje API klíč")
                return None
        else:
            print(f"Odpověď: {response.text}")
            print("❌ SELHALO: Přihlášení by mělo vrátit 200 s platnými údaji")
            return None
    except Exception as e:
        print(f"❌ CHYBA: {str(e)}")
        return None


def test_login_with_invalid_credentials():
    """Test přihlášení s neplatnými údaji"""
    print("\n[TEST 2] Přihlášení s neplatnými údaji")
    print("-" * 60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "username": "spatny_uzivatel",
                "password": "spatne_heslo"
            }
        )
        print(f"Status kód: {response.status_code}")
        print(f"Odpověď: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 401:
            print("✅ ÚSPĚCH: Správně zamítnuto neplatné přihlašovací údaje")
            return True
        else:
            print("❌ SELHALO: Mělo by vrátit 401 pro neplatné údaje")
            return False
    except Exception as e:
        print(f"❌ CHYBA: {str(e)}")
        return False


def test_api_access_with_generated_key(api_key):
    """Test přístupu k API s vygenerovaným klíčem"""
    print("\n[TEST 3] Přístup k chráněnému endpointu s vygenerovaným klíčem")
    print("-" * 60)
    
    if not api_key:
        print("⚠️ PŘESKOČENO: Žádný API klíč k testování")
        return False
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
            headers={"X-API-Key": api_key},
            json={"message": "Test zpráva", "session_id": "test"}
        )
        print(f"Status kód: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ ÚSPĚCH: Přístup k API s vygenerovaným klíčem funguje")
            return True
        else:
            print(f"Odpověď: {response.text[:200]}")
            print("❌ SELHALO: Přístup by měl být povolen s platným klíčem")
            return False
    except Exception as e:
        print(f"❌ CHYBA: {str(e)}")
        return False


def test_login_missing_credentials():
    """Test přihlášení s chybějícími údaji"""
    print("\n[TEST 4] Přihlášení s chybějícími údaji")
    print("-" * 60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": USERNAME}  # Chybí heslo
        )
        print(f"Status kód: {response.status_code}")
        print(f"Odpověď: {response.text[:200]}")
        
        if response.status_code == 422:  # Validation error
            print("✅ ÚSPĚCH: Správně zamítnuto chybějící pole")
            return True
        else:
            print("❌ SELHALO: Mělo by vrátit 422 pro chybějící pole")
            return False
    except Exception as e:
        print(f"❌ CHYBA: {str(e)}")
        return False


def run_all_tests():
    """Spustit všechny testy"""
    print("\n" + "=" * 60)
    print("Spouštění testů přihlášení...")
    print("=" * 60)
    
    # Test 1: Přihlášení s platnými údaji
    api_key = test_login_with_valid_credentials()
    
    # Test 2: Přihlášení s neplatnými údaji
    test_login_with_invalid_credentials()
    
    # Test 3: Přístup k API s vygenerovaným klíčem
    test_api_access_with_generated_key(api_key)
    
    # Test 4: Chybějící údaje
    test_login_missing_credentials()
    
    print("\n" + "=" * 60)
    print("Testy dokončeny")
    print("=" * 60)


if __name__ == "__main__":
    try:
        # Zkontrolovat, zda server běží
        print("\nKontrola, zda server běží...")
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        print("✅ Server běží\n")
    except requests.exceptions.ConnectionError:
        print("❌ CHYBA: Server neběží!")
        print("Spusťte server nejprve: python main.py")
        exit(1)
    except Exception as e:
        print(f"❌ CHYBA: {str(e)}")
        exit(1)
    
    # Spustit testy
    run_all_tests()