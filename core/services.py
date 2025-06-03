import requests
from decouple import config
from core.models import GHLAuthCredentials

BATCHSERVICE_TOKEN = config("BATCHSERVICE_TOKEN")
API_BASE = "https://services.leadconnectorhq.com"
TOKEN = "your_actual_bearer_token_here"  # Replace with real token
LOCATION_ID = "HBMH06bPfTaKkZx49Y4x"
PHONE_QUERY = "2188332406"
NEW_TAGS = ["interested", "follow-up"]

def verify_phone_numbers(phone_numbers):
    print("phone number in verify: ", phone_numbers)
    url = "https://api.batchdata.com/api/v1/phone/verification"
    headers = {
        "Accept": "application/json, application/xml",
        "Authorization": f"Bearer {BATCHSERVICE_TOKEN}",  # Define this token in your environment
        "Content-Type": "application/json"
    }
    payload = {
        "requests": phone_numbers
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

        results = data.get("results", {}).get("phoneNumbers", [])
        output = []

        for result in results:
            number = result.get("number")
            meta = result.get("meta", {})
            not_found = result.get("notFound", True)
            matched = meta.get("matched", False)
            error = meta.get("error", True)
            type = result.get("type")

            is_valid = not error and matched and not not_found

            output.append({
                "number": number,
                "is_valid": is_valid,
                "type":type,
                "details": result  # optional: include full detail if needed
            })

        return output

    except requests.exceptions.RequestException as e:
        print("Request failed:", e)
        return None


def check_and_update_contact(contact_id,new_tags):
    print("new tags: ", new_tags)
    # === HEADERS ===
    print("contactL: ", contact_id)

    token = GHLAuthCredentials.objects.filter(location_id = LOCATION_ID).first()
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token.access_token}",
        "Version": "2021-07-28"
    }

    # === STEP 1: Fetch contact by phone ===
    search_url = f"{API_BASE}/contacts/{contact_id}"
    search_response = requests.get(search_url, headers=headers)
    search_data = search_response.json()

    if search_data.get("contact"):

        print(f"Found contact ID: {contact_id}")

        # === STEP 2: Update tags ===
        update_url = f"{API_BASE}/contacts/{contact_id}"
        update_payload = {
            "tags": new_tags
        }

        update_headers = headers.copy()
        update_headers["Content-Type"] = "application/json"

        update_response = requests.put(update_url, headers=update_headers, json=update_payload)

        if update_response.status_code == 200:
            print("Tags updated successfully.")
        else:
            print(f"Failed to update tags. Status: {update_response.status_code}")
            print(update_response.text)
    else:
        print("Contact not found.")