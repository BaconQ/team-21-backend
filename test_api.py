import requests
import json
import time
from typing import Dict, Any

def test_interaction(prompt: str) -> Dict[str, Any]:
    """
    Test a single interaction with the pet
    Returns the response data if successful, or None if failed
    """
    url = "http://localhost:8000/interact"
    headers = {"Content-Type": "application/json"}
    data = {"prompt": prompt}
    
    print(f"\nTesting interaction with prompt: '{prompt}'")
    print("-" * 50)
    
    try:
        print("Sending request...")
        response = requests.post(url, headers=headers, json=data, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print("\nResponse:")
            
            # Print each message in the conversation
            print("\nConversation:")
            print("-" * 30)
            for i, message in enumerate(response_data["messages"], 1):
                print(f"Pet: {message}")
            print("-" * 30)
            
            # Print status information
            print("\nStatus Information:")
            print(json.dumps({
                "status": response_data["status"],
                "status_change": response_data["status_change"],
                "changes": response_data["changes"]
            }, indent=2))
            
            return response_data
        else:
            print(f"Error Response: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to server. Make sure the server is running on localhost:8000")
        return None
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return None

def run_test_cases():
    """Run all test cases"""
    test_cases = [
        {
            "name": "Workout",
            "prompt": "I am going to the gym now."
        },
        {
            "name": "Rest and Recovery",
            "prompt": "I am exaushted after my workout."
        },
        {
            "name": "Work vs. Play",
            "prompt": "I don't want to do my homework. I want to play video games."
        },
        {
            "name": "Just Talking",
            "prompt": "Let's just chat about something interesting."
        }
    ]
    
    results = []
    
    print("Starting Pet API Tests")
    print("=" * 50)
    
    for test_case in test_cases:
        print(f"\n=== Test Case: {test_case['name']} ===")
        result = test_interaction(test_case['prompt'])
        results.append({
            "test_case": test_case['name'],
            "success": result is not None
        })
        time.sleep(2)  # Wait between requests
    
    # Print summary
    print("\nTest Summary")
    print("=" * 50)
    successful_tests = sum(1 for r in results if r['success'])
    print(f"Tests passed: {successful_tests}/{len(results)}")
    for result in results:
        status = "✅ Passed" if result['success'] else "❌ Failed"
        print(f"{status} - {result['test_case']}")

if __name__ == "__main__":
    run_test_cases() 