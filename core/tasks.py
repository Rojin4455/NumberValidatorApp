import requests
from celery import shared_task
from core.services import verify_phone_numbers, check_and_update_contact
from core.models import GHLAuthCredentials
from decouple import config

@shared_task
def make_api_call():
    credentials = GHLAuthCredentials.objects.first()
    
    print("credentials tokenL", credentials)
    refresh_token = credentials.refresh_token

    
    response = requests.post('https://services.leadconnectorhq.com/oauth/token', data={
        'grant_type': 'refresh_token',
        'client_id': config("GHL_CLIENT_ID"),
        'client_secret': config("GHL_CLIENT_SECRET"),
        'refresh_token': refresh_token
    })
    
    new_tokens = response.json()

    
    obj, created = GHLAuthCredentials.objects.update_or_create(
            location_id= new_tokens.get("locationId"),
            defaults={
                "access_token": new_tokens.get("access_token"),
                "refresh_token": new_tokens.get("refresh_token"),
                "expires_in": new_tokens.get("expires_in"),
                "scope": new_tokens.get("scope"),
                "user_type": new_tokens.get("userType"),
                "company_id": new_tokens.get("companyId"),
                "user_id":new_tokens.get("userId"),

            }
        )
@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def handle_webhook_event(self, data):
    phone = data.get("phone")
    contact_id=data.get("contact_id")
    print("Phone:", phone)
    results = verify_phone_numbers([phone[2:] if phone[:2] == "+1" else phone])
    for res in results:
        print(f"Number: {res['number']} | Valid: {res['is_valid']} | Type: {res["type"]}")
        new_tags = ["Valid" if res['is_valid'] else "Invalid"]
        if res["type"]:
            new_tags.append(res["type"])
        check_and_update_contact(contact_id,new_tags)

    # print("responsel :", response)

