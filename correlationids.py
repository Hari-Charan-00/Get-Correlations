import requests
import time
import pandas as pd

# Base URL and credentials
URL = ""
CLIENT_ID = ""
CLIENT_SECRET = ""

def token_generation():
    try:
        token_url = URL + "auth/oauth/token"
        auth_data = {
            'client_secret': CLIENT_SECRET,
            'grant_type': 'client_credentials',
            'client_id': CLIENT_ID
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        response = requests.post(token_url, data=auth_data, headers=headers, verify=True)

        if response.status_code == 200:
            access_token = response.json().get('access_token')
            if access_token:
                return access_token
            else:
                print("Error: No access token returned in the response.")
        else:
            print(f"Failed to obtain access token: {response.status_code} - {response.text}")
    except Exception as e:
        print("Error during token generation:", str(e))
    return None

def handle_retry(response, retry_count=3):
    retry_attempts = 0
    while retry_attempts < retry_count:
        if response.status_code in [401, 407] or "invalid_token" in response.text.lower():
            print("Attempting token regeneration...")
            new_token = token_generation()
            if new_token:
                return new_token
        retry_attempts += 1
        time.sleep(2)
    return None

def fetch_clients(access_token, partner_id, base_url):
    clients = {}
    page = 1

    while True:
        try:
            headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
            url = f"{base_url}api/v2/tenants/{partner_id}/clients/search?pageNo={page}&pageSize=100"

            response = requests.get(url, headers=headers, verify=True)

            if response.status_code in [401, 407] or "invalid_token" in response.text.lower():
                print("Token invalid or expired. Generating a new token...")
                access_token = handle_retry(response)
                if not access_token:
                    print("Unable to generate new token.")
                    break
                continue

            elif response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                for client in results:
                    client_id = client.get("uniqueId", "NA")
                    client_name = client.get("name", "NA")
                    if client_id != "NA" and client_name != "NA":
                        clients[client_id] = client_name

                total_pages = data.get('totalPages', 1)
                if page >= total_pages:
                    break
                page += 1
            else:
                print(f"Failed to get clients: {response.status_code}")
                break
        except Exception as e:
            print("Error fetching clients:", str(e))
            break

    print(f"Total clients fetched: {len(clients)}")
    return clients

def correlation_policies(access_token, client_id):
    policies = {
        "policy_ids": [],
        "policy_name": [],
        "enabled": [],
        "enabledMode": [],
        "tenantScope": [],
        "MLStatus": []
    }

    page = 1

    while True:
        try:
            url = f"{URL}api/v2/tenants/{client_id}/policies/alertCorrelation?pageNo={page}&pageSize=100"
            headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}

            response = requests.get(url, headers=headers, verify=True)

            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                for policy in results:
                    policies["policy_ids"].append(policy.get('id'))
                    policies["policy_name"].append(policy.get('name'))
                    policies["enabled"].append(policy.get('enabled'))
                    policies["enabledMode"].append(policy.get('enabledMode'))
                    policies["tenantScope"].append(policy.get('tenantScope'))
                    policies["MLStatus"].append(policy.get('mlStatus'))

                total_pages = data.get('totalPages', 1)
                if page >= total_pages:
                    break
                page += 1

            elif response.status_code == 500 and "Clients those doesn’t have Event Management bundle access" in response.text:
                print("Client does not have Event Management bundle access.")
                break

            elif response.status_code in [401, 407] or "invalid_token" in response.text.lower():
                print("Token invalid or expired. Regenerating...")
                access_token = handle_retry(response)
                if not access_token:
                    print("Unable to generate new token.")
                    return None
            else:
                print(f"Unexpected error while fetching policies: {response.status_code} - {response.text}")
                break

        except Exception as e:
            print("Error while fetching correlation policies:", str(e))
            return None

    return policies if policies["policy_ids"] else None

def main():
    access_token = token_generation()
    if not access_token:
        print("Access token generation failed. Exiting.")
        return

    # Replace with actual partner IDs and names
    partners = {
        #"b5c94cda-23bb-b843-6be3-3f929e37e191" : "Tri-Valley"
        "b46ba025-0c99-416d-955d-10129cf4ed15": "Helixstorm",
        #"19a0e399-0a1f-343b-0fc1-bfb092f30289": "KMEU",
        "9384a74d-5370-573a-0608-9a14a25b234e": "All Covered",
        "fee7887c-1c4e-90aa-b4bc-e6870ac060fc": "Agiliti",
        "70d37846-efe6-bc75-2907-8ca6e0a9c1f5": "Trace3",
        "a828cf1c-a23c-4e31-97a5-8005a92fc193": "American Digital",
        "2af587e3-f7e6-46eb-5b81-f93734209a3b": "Alternative Technology Group",
        #"305a90cf-6dd1-cae3-fccf-207fe1c11545": "Synclear",
        "dfba9027-c33d-aa51-5664-3be27e385f99": "Weidenhammer",
        "1ea490e8-4115-96fb-a3ec-6e88085e9d2f": "UDT",
        #"df436d26-0f29-a7b9-827c-40e529037060": "CDI",
        "2f4ac3aa-e30f-b5ea-c273-1fea30e5643a": "CynexLink",
        "87416916-cee4-71a0-5321-2a9f2e5f2c94": "DataVox",
        "12010f7a-7695-eb06-436f-d01d89e03054": "Fordham University",
        "654da5fc-25b4-602b-8055-7635670d21e6": "SymQuest",
        "da5104c0-f140-8f7d-e779-050f0046dec4": "Xerillion Corporation"
        
    }

    all_policies_data = []

    for partner_id, partner_name in partners.items():
        print(f"\nProcessing partner: {partner_name}")
        clients = fetch_clients(access_token, partner_id, URL)

        for client_id, client_name in clients.items():
            print(f"\n  → Processing client: {client_name}")
            policy_data = correlation_policies(access_token, client_id)

            if policy_data:
                print(f"    Policies found: {len(policy_data['policy_ids'])}")
                for i in range(len(policy_data["policy_ids"])):
                    all_policies_data.append({
                        "Partner Name": partner_name,
                        "Client Name": client_name,
                        "Policy ID": policy_data["policy_ids"][i],
                        "Policy Name": policy_data["policy_name"][i],
                        "Enabled": policy_data["enabled"][i],
                        "Enabled Mode": policy_data["enabledMode"][i],
                        "Tenant Scope": policy_data["tenantScope"][i],
                        "ML Status": policy_data["MLStatus"][i],
                    })
            else:
                print("    No policies found or error occurred.")

    if all_policies_data:
        df = pd.DataFrame(all_policies_data)
        df.to_excel("correlation_policies_AllPartners.xlsx", index=False)
        print("\nAll policy data exported to 'correlation_policies.xlsx'")
    else:
        print("\nNo policy data to export.")

if __name__ == "__main__":
    main()
