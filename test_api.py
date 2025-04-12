import requests
import json

def test_interaction():
    url = "http://localhost:8000/interact"
    headers = {"Content-Type": "application/json"}
    data = {"prompt": "Let's go for a long run in the park and then have some water and treats!"}
    
    try:
        print("Sending request to:", url)
        print("Request data:", json.dumps(data, indent=2))
        
        response = requests.post(url, headers=headers, json=data)
        print("Status Code:", response.status_code)
        
        if response.status_code == 200:
            print("Response:", json.dumps(response.json(), indent=2))
        else:
            print("Error Response:", response.text)
    except Exception as e:
        print("Error occurred:", str(e))

if __name__ == "__main__":
    test_interaction() 