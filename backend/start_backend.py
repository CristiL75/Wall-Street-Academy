import subprocess
import os
import sys
import requests
import time
from dotenv import load_dotenv

def check_blockchain_available():
    """Verifică dacă blockchain-ul rulează înainte de a porni backend-ul"""
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            print(f"Verificăm dacă blockchain-ul rulează (încercarea {attempt+1}/{max_attempts})...")
            response = requests.post("http://localhost:8545", 
                                   json={"jsonrpc":"2.0", "method":"eth_blockNumber", "params":[], "id":1},
                                   timeout=2)
            if response.status_code == 200:
                print("✅ Blockchain node este activ!")
                return True
        except Exception as e:
            print(f"⚠️ Blockchain nu răspunde: {e}")
        
        time.sleep(1)
    
    print("⚠️ Blockchain-ul nu este disponibil. Asigură-te că ai rulat mai întâi scriptul start_blockchain.py")
    print("Continui oricum? (y/n)")
    choice = input().lower()
    return choice == 'y'

def start_mongodb():
    """Pornește MongoDB server"""
    print("🍃 Verificăm dacă MongoDB rulează...")
    try:
        # Verifică dacă MongoDB rulează deja
        result = subprocess.run("mongod --version", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ MongoDB este instalat")
            
            # Pornește MongoDB
            print("🍃 Pornim MongoDB server...")
            # Rulăm în background
            if os.name == 'nt':  # Windows
                subprocess.Popen("start mongod", shell=True)
            else:  # Linux/Mac
                subprocess.Popen("mongod &", shell=True)
            
            # Așteaptă puțin să pornească MongoDB
            time.sleep(2)
            return True
    except Exception as e:
        print(f"⚠️ Eroare la pornirea MongoDB: {e}")
        print("Continui oricum? (y/n)")
        choice = input().lower()
        return choice == 'y'

def start_backend():
    """Pornește FastAPI backend"""
    print("✨ Pornim backend-ul FastAPI...")
    
    # Încarcă variabilele de mediu
    load_dotenv(dotenv_path="./app/.env")
    
    # Verifică variabilele de mediu necesare
    required_env_vars = {
        "PRIVATE_KEY": "Cheia privată pentru contul admin",
        "BLOCKCHAIN_URL": "URL-ul către blockchain (probabil http://localhost:8545)",
        "NFT_CONTRACT_ADDRESS": "Adresa contractului NFT"
    }

    missing_vars = []
    for var, description in required_env_vars.items():
        value = os.environ.get(var)
        if not value:
            missing_vars.append(var)
            print(f"⚠️ Warning: {var} lipsește din .env ({description})")

    if missing_vars:
        print("\n⚠️ Există variabile de mediu lipsă. Continui? (y/n)")
        choice = input().lower()
        if choice != 'y':
            print("Oprim aplicația...")
            return False

    print("\n✅ Pornesc backend-ul API...")
    
    # Rulează backend-ul (acest proces va bloca până când este închis)
    subprocess.run("uvicorn main:app --reload", cwd="./app", shell=True)
    return True

def main():
    # Verifică dacă blockchain-ul rulează
    if not check_blockchain_available():
        return
        
    # Pornește MongoDB dacă e necesar
    start_mongodb()
    
    # Pornește backend-ul
    start_backend()

if __name__ == "__main__":
    main()