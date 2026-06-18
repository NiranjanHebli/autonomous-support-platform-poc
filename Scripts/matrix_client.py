import os
import time
import httpx
from typing import List, Dict, Any

class MatrixClient:
    def __init__(self, access_token: str, base_url: str = "https://matrix.org"):
        self.access_token = access_token
        self.base_url = base_url
        self.client = httpx.Client(
            base_url=f"{self.base_url}/_matrix/client/v3",
            headers={"Authorization": f"Bearer {self.access_token}"}
        )

    def sync(self) -> Dict[str, Any]:
        """Performs a sync to get the latest state and events."""
        response = self.client.get("/sync")
        response.raise_for_status()
        return response.json()

    def get_rooms(self) -> Dict[str, Any]:
        """Returns a dictionary of joined rooms and their data."""
        sync_data = self.sync()
        return sync_data.get("rooms", {}).get("join", {})

    def get_invites(self) -> Dict[str, Any]:
        """Returns a dictionary of invited rooms (pending invites)."""
        sync_data = self.sync()
        return sync_data.get("rooms", {}).get("invite", {})

    def get_messages(self, room_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetches recent messages for a specific room."""
        # 'dir': 'b' means backward (from the latest message backwards)
        response = self.client.get(f"/rooms/{room_id}/messages", params={"dir": "b", "limit": limit})
        response.raise_for_status()
        data = response.json()
        
        # The chunk contains the events, but they are returned in reverse chronological order.
        # We'll reverse it so the newest is at the bottom.
        chunk = data.get("chunk", [])
        chunk.reverse()
        return chunk

    def download_media(self, mxc_url: str, output_dir: str = "downloads") -> str:
        """Downloads authenticated media and returns the local file path."""
        if not mxc_url.startswith("mxc://"):
            return ""
            
        server_and_media = mxc_url[6:]
        os.makedirs(output_dir, exist_ok=True)
        
        media_id = server_and_media.split("/")[-1]
        
        # Matrix 1.11+ requires authenticated media downloads
        url = f"{self.base_url}/_matrix/client/v1/media/download/{server_and_media}"
        
        response = self.client.get(url)
        response.raise_for_status()
        
        content_type = response.headers.get("Content-Type", "")
        import mimetypes
        ext = mimetypes.guess_extension(content_type) or ""
        
        # Prefer the original filename if we can parse it from Content-Disposition, but media_id is safer
        local_path = os.path.join(output_dir, f"{media_id}{ext}")
        with open(local_path, "wb") as f:
            f.write(response.content)
            
        return os.path.abspath(local_path)

    def send_message(self, room_id: str, text: str, reply_to_event_id: str = None) -> Dict[str, Any]:
        """Sends a text message to a specific room, optionally replying to an event."""
        txn_id = str(int(time.time() * 1000))
        url = f"/rooms/{room_id}/send/m.room.message/{txn_id}"
        payload = {
            "msgtype": "m.text",
            "body": text
        }
        
        if reply_to_event_id:
            payload["m.relates_to"] = {
                "m.in_reply_to": {
                    "event_id": reply_to_event_id
                }
            }
            
        # Note: the matrix spec uses PUT for sending events with a transaction ID
        response = self.client.put(url, json=payload)
        response.raise_for_status()
        return response.json()

    def join_room(self, room_id_or_alias: str) -> Dict[str, Any]:
        """Joins a specific room by its ID or alias."""
        # URL encode the room ID/alias in case it has special characters
        import urllib.parse
        encoded_room = urllib.parse.quote(room_id_or_alias)
        response = self.client.post(f"/join/{encoded_room}")
        response.raise_for_status()
        return response.json()
