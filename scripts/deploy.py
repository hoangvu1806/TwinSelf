"""
Deployment script for CD pipeline
"""
import os
import sys
import time
import subprocess
import psutil
from pathlib import Path

def stop_port(port):
    """Stop process on given port"""
    print(f"Stopping process on port {port}...")
    for conn in psutil.net_connections():
        if conn.laddr.port == port and conn.status == 'LISTEN':
            try:
                process = psutil.Process(conn.pid)
                process.terminate()
                process.wait(timeout=5)
                print(f"✓ Stopped process on port {port}")
                return True
            except:
                pass
    print(f"No process on port {port}")
    return False

def pull_code():
    """Pull latest code"""
    print("Pulling latest code...")
    os.chdir(r"D:\HOANGVU\VPS\TwinSelf")
    subprocess.run(["git", "fetch", "origin"], check=True)
    subprocess.run(["git", "reset", "--hard", "origin/main"], check=True)
    subprocess.run(["git", "clean", "-fd"], check=True)
    print("✓ Code updated")

def rebuild_data():
    """Rebuild data"""
    print("Rebuilding data...")
    os.chdir(r"D:\HOANGVU\VPS\TwinSelf")
    subprocess.run(["python", "scripts/smart_rebuild.py", "--create-version"], check=True)
    print("✓ Data rebuilt")

def start_mlflow():
    """Start MLflow server"""
    print("Starting MLflow server...")
    os.chdir(r"D:\HOANGVU\VPS\TwinSelf")
    
    subprocess.Popen(
        ["mlflow", "server", "--host", "0.0.0.0", "--port", "5000"],
        creationflags=subprocess.CREATE_NEW_CONSOLE | subprocess.CREATE_NO_WINDOW
    )
    time.sleep(10)
    print("✓ MLflow started")

def start_portfolio():
    """Start portfolio server"""
    print("Starting portfolio server...")
    os.chdir(r"D:\HOANGVU\VPS\TwinSelf")
    
    subprocess.Popen(
        ["uvicorn", "portfolio_server:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"],
        creationflags=subprocess.CREATE_NEW_CONSOLE | subprocess.CREATE_NO_WINDOW
    )
    time.sleep(30)
    print("✓ Portfolio started")

def health_check():
    """Check server health"""
    print("Checking server health...")
    import requests
    
    for i in range(30):
        try:
            response = requests.get("http://localhost:8080/chatbot/api/health", timeout=2)
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Server healthy: {data.get('bot_name')}")
                return True
        except:
            time.sleep(2)
    
    print("✗ Health check failed")
    return False

def main():
    """Main deployment flow"""
    try:
        # Stop services
        stop_port(8080)
        time.sleep(3)
        stop_port(5000)
        time.sleep(3)
        
        # Update code
        pull_code()
        
        # Rebuild data
        rebuild_data()
        
        # Start services
        start_mlflow()
        start_portfolio()
        
        # Health check
        if health_check():
            print("\n✓ Deployment SUCCESS")
            return 0
        else:
            print("\n✗ Deployment FAILED")
            return 1
            
    except Exception as e:
        print(f"\n✗ Deployment ERROR: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
