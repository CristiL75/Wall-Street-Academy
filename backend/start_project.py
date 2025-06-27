import subprocess
import time
import os
import signal
import sys

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

def start_blockchain():
    print("🚀 Pornim blockchain-ul și deployăm contractele...")
    if os.name == 'nt':  # Windows
        blockchain_process = run_command("start cmd /k python start_blockchain.py", wait=False)
    else:  # Linux/Mac
        blockchain_process = run_command("python start_blockchain.py &", wait=False)
    
    # Așteaptă puțin să se inițializeze blockchain-ul
    print("⏳ Așteptăm inițializarea blockchain-ului (15 secunde)...")
    time.sleep(15)
    return blockchain_process

def start_backend():
    print("✨ Pornim backend-ul FastAPI...")
    if os.name == 'nt':  # Windows
        backend_process = run_command("start cmd /k python start_backend.py", wait=False)
    else:  # Linux/Mac
        backend_process = run_command("python start_backend.py &", wait=False)
    return backend_process

# Main flow
def main():
    # Înregistrăm handler pentru CTRL+C
    signal.signal(signal.SIGINT, cleanup_handler)
    signal.signal(signal.SIGTERM, cleanup_handler)
    
    # Verifică dacă există scripturile necesare
    if not os.path.exists("start_blockchain.py"):
        print("❌ Eroare: Fișierul start_blockchain.py nu există!")
        return
    
    if not os.path.exists("start_backend.py"):
        print("❌ Eroare: Fișierul start_backend.py nu există!")
        return
    
    # Pornește blockchain-ul și contractele
    blockchain_process = start_blockchain()
    
    # Pornește backend-ul
    backend_process = start_backend()
    
    print("\n🚀 Aplicația Wall Street Academy rulează!")
    print("- Blockchain: http://localhost:8545")
    print("- Backend API: http://localhost:8000")
    print("- Frontend (dacă este pornit separat): http://localhost:3000")
    print("\nPentru a opri toate serviciile, apasă CTRL+C în această fereastră")
    
    # Menține procesul principal în execuție pentru a putea opri subprocesele la CTRL+C
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup_handler(None, None)

if __name__ == "__main__":
    main()