import subprocess
import time
import os
import signal
import requests
import sys
from dotenv import load_dotenv

# Liste pentru a ține evidența proceselor pornite
running_processes = []

# Functie ca sa rulezi comenzi
def run_command(command, cwd=None, wait=True):
    process = subprocess.Popen(command, cwd=cwd, shell=True)
    if not wait:
        running_processes.append(process)
    else:
        process.communicate()
    return process

def start_mongodb():
    print("🍃 Pornim MongoDB server...")
    return run_command("mongod", wait=False)

# Functie sa pornim Hardhat node-ul
def start_blockchain_node():
    print("\U0001F680 Pornim Hardhat node...")
    node_process = run_command("npx hardhat node", cwd="./app/blockchain", wait=False)
    return node_process

# Verificare dacă blockchain-ul rulează
def check_blockchain_node():
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            print(f"Verificăm dacă blockchain-ul rulează (încercarea {attempt+1}/{max_attempts})...")
            response = requests.post("http://localhost:8545", 
                                    json={"jsonrpc":"2.0", "method":"eth_blockNumber", "params":[], "id":1},
                                    timeout=2)
            if response.status_code == 200:
                print("✅ Blockchain node este activ!")
                return True
        except:
            pass
        
        time.sleep(1)
    
    print("❌ Blockchain node nu răspunde! Verificați dacă portul 8545 este disponibil.")
    return False

# Functie sa deployam smart contractele
def deploy_contracts():
    print("\U0001F6E0 Deployăm contractele...")
    try:
        # Verifică dacă există fișierele de contract
        if not os.path.exists("./app/blockchain/contracts/UserAchievementNFT.sol"):
            print("⚠️ Warning: Contract file UserAchievementNFT.sol missing!")
            
        # Deploy pentru primul contract
        deploy_process = subprocess.run("npx hardhat run scripts/deploy.js --network localhost", 
                                        cwd="./app/blockchain", 
                                        shell=True,
                                        capture_output=True,
                                        text=True)
        if deploy_process.returncode != 0:
            print(f"❌ Eroare la deploy contract principal: {deploy_process.stderr}")
        else:
            print("✅ Contract principal deployed!")
            print(deploy_process.stdout)
            
        # Deploy pentru NFT
        nft_process = subprocess.run("npx hardhat run scripts/deploy_nft.js --network localhost", 
                                     cwd="./app/blockchain", 
                                     shell=True,
                                     capture_output=True, 
                                     text=True)
        if nft_process.returncode != 0:
            print(f"❌ Eroare la deploy NFT: {nft_process.stderr}")
        else:
            print("✅ NFT contract deployed!")
            print(nft_process.stdout)
            
            # Extrage adresa NFT din output și actualizează .env
            import re
            match = re.search(r'NFT contract deployed to: (0x[a-fA-F0-9]{40})', nft_process.stdout)
            if match:
                nft_address = match.group(1)
                print(f"📋 Detected NFT address: {nft_address}")
                
                # Actualizează .env cu adresa NFT
                env_path = "./app/.env"
                with open(env_path, 'r') as f:
                    env_content = f.read()
                
                if "NFT_CONTRACT_ADDRESS=" in env_content:
                    env_content = re.sub(r'NFT_CONTRACT_ADDRESS=.*', f'NFT_CONTRACT_ADDRESS={nft_address}', env_content)
                else:
                    env_content += f'\nNFT_CONTRACT_ADDRESS={nft_address}'
                
                with open(env_path, 'w') as f:
                    f.write(env_content)
                
                print("✅ .env updatat cu adresa NFT!")
            
    except Exception as e:
        print(f"❌ Eroare la deploy: {e}")

# Functie sa porneasca FastAPI backend
def start_backend():
    print("✨ Pornim backend-ul FastAPI...")
    run_command("uvicorn main:app --reload", cwd="./app", wait=True)

# Handler pentru cleanup la închidere
def cleanup_handler(signum, frame):
    print("\n🧹 Cleanup... Oprim toate procesele...")
    for process in running_processes:
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            process.kill()
    sys.exit(0)

# Main flow
def main():
    # Înregistrăm handler pentru CTRL+C
    signal.signal(signal.SIGINT, cleanup_handler)
    signal.signal(signal.SIGTERM, cleanup_handler)
    
    # Pornim blockchain-ul
    node_process = start_blockchain_node()

    # Asteptam și verificăm că blockchain-ul rulează
    if not check_blockchain_node():
        print("Nu putem continua fără blockchain!")
        cleanup_handler(None, None)
        return

    # Deployam contractele
    deploy_contracts()

    # Incarcam .env ca sa vedem daca avem chei corect
    load_dotenv(dotenv_path="./app/.env")

    required_env_vars = {
        "PRIVATE_KEY": "Cheia privată pentru contul admin",
        "BLOCKCHAIN_URL": "URL-ul către blockchain (probabil http://localhost:8545)",
        "NFT_CONTRACT_ADDRESS": "Adresa contractului NFT (ar trebui actualizată automat)"
    }

    missing_vars = []
    for var, description in required_env_vars.items():
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
            print(f"⚠️ Warning: {var} lipsește din .env ({description})")

    if missing_vars:
        print("\n⚠️ Există variabile de mediu lipsă. Continuați? (y/n)")
        choice = input().lower()
        if choice != 'y':
            print("Oprim aplicația...")
            cleanup_handler(None, None)
            return

    # Pornim backend-ul
    print("\n✅ Toate pregătirile sunt gata. Pornesc backend-ul...")
    start_backend()

if __name__ == "__main__":
    main()