import requests

try:
    # Check the OpenAPI docs to see all routes
    response = requests.get("http://localhost:8000/openapi.json")
    if response.status_code == 200:
        openapi_data = response.json()
        paths = openapi_data.get("paths", {})
        
        print("Available request-related routes:")
        for path, methods in paths.items():
            if "/requests" in path:
                print(f"  {path}: {list(methods.keys())}")
                
    else:
        print(f"Failed to get OpenAPI docs: {response.status_code}")
        
except Exception as e:
    print(f"Error: {e}")