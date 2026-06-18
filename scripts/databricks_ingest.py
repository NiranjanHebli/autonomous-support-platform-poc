import os
import time
import json
import httpx
from core.utils import ensure_env

# --- Configuration ---
MATRIX_URL = "https://matrix.org"
# Defaulting to the room from previous commands, but can be overridden
ROOM_ID = (
    ensure_env("MATRIX_ROOM_ID", optional=True) or "!oDXwgLUCnHlmqpBgQc:matrix.org"
)
STATE_FILE = ".sync_state"


def get_media_url(mxc_url: str) -> str:
    """Converts an mxc:// URL to an authenticated Matrix download endpoint URL."""
    if not mxc_url.startswith("mxc://"):
        return ""
    server_and_media = mxc_url[6:]
    # This URL must be fetched with an Authorization header in downstream Databricks jobs
    return f"{MATRIX_URL}/_matrix/client/v1/media/download/{server_and_media}"


def load_state() -> str:
    """Loads the last next_batch token from the state file."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return f.read().strip()
    return ""


def save_state(next_batch: str):
    """Saves the next_batch token to the state file."""
    with open(STATE_FILE, "w") as f:
        f.write(next_batch)


def get_event_sender(client: httpx.Client, room_id: str, event_id: str) -> str:
    """Fetches a specific event from Matrix to determine who sent it."""
    url = f"{MATRIX_URL}/_matrix/client/v3/rooms/{room_id}/event/{event_id}"
    try:
        response = client.get(url)
        response.raise_for_status()
        return response.json().get("sender", "")
    except Exception as e:
        print(
            f"Warning: Could not fetch original event {event_id} to find recipient: {e}"
        )
        return ""


def ingest_messages(access_token: str, room_id: str):
    """
    Connects to Matrix, syncs from the last known state, extracts new messages
    for the specific room, and dumps them to a JSON file.
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    client = httpx.Client(headers=headers, timeout=30.0)

    since_token = load_state()
    print(
        f"Syncing messages since token: {since_token if since_token else 'BEGINNING'}"
    )

    # 1. Fetch new events
    params = {"timeout": 0}
    if since_token:
        params["since"] = since_token

    url = f"{MATRIX_URL}/_matrix/client/v3/sync"
    response = client.get(url, params=params)
    response.raise_for_status()
    sync_data = response.json()

    next_batch = sync_data.get("next_batch", "")

    # 2. Extract room events
    joined_rooms = sync_data.get("rooms", {}).get("join", {})
    if room_id not in joined_rooms:
        print(f"No new activity found for room {room_id}")
        if next_batch:
            save_state(next_batch)
        return

    room_data = joined_rooms[room_id]
    events = room_data.get("timeline", {}).get("events", [])

    extracted_data = []

    # 3. Process events
    for event in events:
        if event.get("type") == "m.room.message":
            sender = event.get("sender", "Unknown")
            content = event.get("content", {})
            msgtype = content.get("msgtype", "")
            body = content.get("body", "")

            attachment_url = ""
            if msgtype in ("m.image", "m.file", "m.video", "m.audio"):
                mxc_url = content.get("url", "")
                if mxc_url:
                    attachment_url = get_media_url(mxc_url)

            # Track who this message is sent to (if it's a reply to someone's message)
            recipient_username = ""
            reply_event_id = (
                content.get("m.relates_to", {}).get("m.in_reply_to", {}).get("event_id")
            )
            if reply_event_id:
                recipient_username = get_event_sender(client, room_id, reply_event_id)

            extracted_data.append(
                {
                    "username": sender,
                    "recipient_username": recipient_username,
                    "message": body,
                    "attachment_url": attachment_url,
                    "event_id": event.get("event_id", ""),
                    "reply_to_event_id": reply_event_id or "",
                    "timestamp": event.get("origin_server_ts", 0),
                }
            )

    # 4. Save extracted data to temporary JSON if any messages exist
    if extracted_data:
        timestamp = int(time.time())
        output_file = f"ingest_{timestamp}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(extracted_data, f, indent=2)
        print(f"Saved {len(extracted_data)} messages to {output_file}")
    else:
        print("No new text/media messages found in the recent activity.")

    # 5. Update state
    if next_batch:
        save_state(next_batch)
        print("Updated sync token state.")


if __name__ == "__main__":
    try:
        token = ensure_env("ACCESS_TOKEN")
    except ValueError as e:
        print(f"ERROR: {e}")
        exit(1)

    print(f"Starting ingestion for room {ROOM_ID}")
    ingest_messages(token, ROOM_ID)
