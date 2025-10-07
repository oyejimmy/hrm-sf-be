import subprocess
import time
import sys

try:
    # Kill any existing server process
    subprocess.run(["taskkill", "/f", "/im", "python.exe"], capture_output=True)
    time.sleep(2)
    
    print("Starting server...")
    # Start the server
    subprocess.Popen([sys.executable, "run.py"])
    time.sleep(5)
    
    print("Server should be running now")
    
except Exception as e:
    print(f"Error: {e}")