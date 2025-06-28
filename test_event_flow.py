#!/usr/bin/env python3
"""
Test script to demonstrate the full event sourcing flow
"""

import asyncio

import httpx

# Sample Salesforce CDC event
SAMPLE_EVENT = {
    "detail": {
        "payload": {
            "ChangeEventHeader": {
                "entityName": "Account",
                "changeType": "CREATE",
                "changedFields": ["Name", "ParentId", "Status__c"],
                "recordIds": ["001xx000003DIloAAG"],
            },
            "Id": "001xx000003DIloAAG",
            "Name": "Acme Corporation",
            "ParentId": None,
            "Status__c": "Active",
            "CreatedDate": "2024-01-15T10:30:00.000+0000",
            "LastModifiedDate": "2024-01-15T10:30:00.000+0000",
        }
    },
    "source": "aws.partner/salesforce.com/123456789/Account/ChangeEvent",
    "detail-type": "AccountChangeEvent",
    "time": "2024-01-15T10:30:00.000Z",
}

BASE_URL = "http://localhost:8000"


async def test_full_flow():
    """Test the complete event sourcing flow"""
    async with httpx.AsyncClient() as client:
        print("🚀 Testing Full Event Sourcing Flow")
        print("=" * 50)

        # 1. Check health
        print("\n1️⃣ Checking API health...")
        response = await client.get(f"{BASE_URL}/ht/")
        print(f"   Health check: {response.json()}")

        # 2. Post Salesforce event
        print("\n2️⃣ Posting Salesforce CDC event...")
        response = await client.post(
            f"{BASE_URL}/events/salesforce", json=SAMPLE_EVENT
        )
        print(f"   Event processing result: {response.json()}")

        # 3. Wait a moment for processing
        print("\n3️⃣ Waiting for event processing...")
        await asyncio.sleep(2)

        # 4. Check events in event store
        print("\n4️⃣ Checking events in event store...")
        response = await client.get(f"{BASE_URL}/events/events?limit=5")
        events_result = response.json()
        print(f"   Events found: {events_result['count']}")
        for event in events_result["events"]:
            print(f"   - {event['event_type']}: {event['aggregate_id']}")

        # 5. Check clients in read model
        print("\n5️⃣ Checking clients in read model...")
        response = await client.get(f"{BASE_URL}/events/clients")
        clients_result = response.json()
        print(f"   Clients found: {clients_result['count']}")
        for client in clients_result["clients"]:
            print(f"   - {client['name']} ({client['status']})")

        print("\n✅ Full flow test completed!")


if __name__ == "__main__":
    print("Starting Event Sourcing Flow Test...")
    print("Make sure the API is running on http://localhost:8000")
    print("Run: python src/event_sourcing/run.py")
    print()

    try:
        asyncio.run(test_full_flow())
    except httpx.ConnectError:
        print(
            "❌ Could not connect to API. Make sure it's running on http://localhost:8000"
        )
    except Exception as e:
        print(f"❌ Error: {e}")
