import asyncio
import json
from kasa_service import get_all_device_statuses
from database import save_statuses_to_db

async def main():
    print("Fetching current device statuses...\n")
    
    # 1. Get the data from the hardware
    statuses = await get_all_device_statuses()
    
    # 2. (Optional) Print the JSON payload for debugging
    print("JSON Payload:")
    print(json.dumps(statuses, indent=4))
    print()
    
    # 3. Send the data to the database
    save_statuses_to_db(statuses)

if __name__ == "__main__":
    asyncio.run(main())