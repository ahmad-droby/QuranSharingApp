# Fetch Quran API data
import requests
import json
import os

def fetch_and_save(endpoint, filename):
    """Fetches data from the API endpoint and saves it to a JSON file."""
    try:
        print(f"Fetching data from: {endpoint}")
        response = requests.get(endpoint)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

        # Parse the JSON response
        data = response.json()

        # Check if the expected structure is present (adjust based on actual API response)
        if isinstance(data, dict) and 'data' in data:
            output_path = f"quran_video_app/data/{filename}"
            # Ensure the directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data['data'], f, indent=2, ensure_ascii=False)
            print(f"Successfully saved data to {output_path}")
        else:
            print(f"Error: Unexpected data structure in response from {endpoint}. Received keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred during request to {endpoint}: {e}")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from response: {response.text[:500]}...") # Print first 500 chars
    except Exception as e:
        print(f"An unexpected error occurred while processing {endpoint}: {e}")

# Create data directory if it doesn't exist
data_dir = "quran_video_app/data"
if not os.path.exists(data_dir):
    os.makedirs(data_dir)
    print(f"Created directory: {data_dir}")

# Fetch available editions
fetch_and_save('http://api.alquran.cloud/v1/edition', 'editions.json')

# Fetch metadata (includes Surah names)
fetch_and_save('http://api.alquran.cloud/v1/meta', 'meta.json')

print("Finished fetching initial data.")

