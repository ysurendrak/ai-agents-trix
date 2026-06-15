import json

# Docs: https://bored-api.appbrewery.com/

def get_bored_activity_by_type(type):
    """
    Fetch a random activity from the Bored API based on the specified type.

    Parameters:
    - type (str): The type of activity to fetch (e.g., "relaxation", "education", "recreational", "cooking", "social", "busywork", etc.).

    Returns:
    - dict: A dictionary containing the activity details, including the activity name, type, participants, price, and link.
    """
    import requests

    if isinstance(type, dict):
        type = type.get("type", "")
    else:
        return {"error": "Type parameter is required. Like {'type': 'relaxation'}, etc."}

    type=str(type).lower().strip()
    url = f"https://bored-api.appbrewery.com/filter?type={type}"
    response = requests.get(url)

    if response.status_code == 200:
        activities = response.json()
        if activities:
            return activities[0]  # Return the first activity from the list
        else:
            return {"error": "No activities found for the specified type."}
    else:
        return {"error": f"Failed to fetch activities. Status code: {response.status_code}"
}

# https://bored-api.appbrewery.com/filter?type=relaxation
tools_schema = [
    {
        "type": "function",
        "name": "get_bored_activity_by_type",
        "description": "A set of tools to interact with the Bored API, which provides activities to do when you're bored, including fetching random activities, filtering by type, and getting activity details.",
        "parameters": {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "description": "The type of activity to do when you're bored."
                    },
            },
            "required": ["type"],
        },
    },
]

tools = {
    "get_bored_activity_by_type": get_bored_activity_by_type
}
