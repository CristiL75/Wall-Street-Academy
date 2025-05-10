import subprocess
import time
import os
from dotenv import load_dotenv

# Functie ca sa rulezi comenzi

def run_command(command, cwd=None, wait=True):
    process = subprocess.Popen(command, cwd=cwd, shell=True)
    if wait:
        process.communicate()
    return process

# Functie sa pornim Hardhat node-ul

def start_blockchain_node():
    print("\U0001F680 Pornim Hardhat node...")
    return run_command("npx hardhat node", cwd="./app/blockchain", wait=False)

# Functie sa deployam smart contractele

def deploy_contracts():
    print("\U0001F6E0 Deployăm contractele...")
    run_command("npx hardhat run scripts/deploy.js --network localhost", cwd="./app/blockchain")
    run_command("npx hardhat run scripts/deploy_nft.js --network localhost", cwd="./app/blockchain")

# Functie sa porneasca FastAPI backend

def start_backend():
    print("✨ Pornim backend-ul FastAPI...")
    run_command("uvicorn main:app --reload", cwd="./app", wait=True)

# Main flow

def main():
    # Pornim blockchain-ul
    node_process = start_blockchain_node()

    # Asteptam un pic sa porneasca node-ul
    time.sleep(3)

    # Deployam contractele
    try:
        deploy_contracts()
    except Exception as e:
        print(f"❌ Eroare la deploy: {e}")

    # Incarcam .env ca sa vedem daca avem chei corect
    load_dotenv(dotenv_path="./app/.env")

    if not os.getenv("PRIVATE_KEY"):
        print("⚠️ Warning: PRIVATE_KEY lipseste in .env")

    if not os.getenv("CONTRACT_ADDRESS"):
        print("⚠️ Warning: CONTRACT_ADDRESS lipseste in .env")

    # Pornim backend-ul
    start_backend()

if __name__ == "__main__":
    main()
