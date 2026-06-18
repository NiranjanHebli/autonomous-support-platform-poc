import typer
from rich.console import Console
from rich.table import Table
from scripts.matrix_client import MatrixClient
from core.utils import ensure_env

app = typer.Typer(help="CLI tool to interact with Matrix.org (Element)")
console = Console()


def get_client() -> MatrixClient:
    try:
        access_token = ensure_env("ACCESS_TOKEN")
    except ValueError as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(code=1)
    return MatrixClient(access_token)


@app.command()
def list_rooms():
    """List joined rooms and their recent activity."""
    client = get_client()

    with console.status("Fetching rooms...", spinner="dots"):
        try:
            rooms = client.get_rooms()
            invites = client.get_invites()
        except Exception as e:
            console.print(f"[bold red]Failed to fetch rooms:[/] {e}")
            raise typer.Exit(code=1)

    if not rooms and not invites:
        console.print("[yellow]No joined or invited rooms found.[/]")
        return

    if rooms:
        table = Table(title="Joined Rooms")
        table.add_column("Room ID", style="cyan", no_wrap=True)
        table.add_column("Unread", justify="right", style="green")

        for room_id, room_data in rooms.items():
            unread_notifications = room_data.get("unread_notifications", {})
            notification_count = unread_notifications.get("notification_count", 0)
            table.add_row(room_id, str(notification_count))
        console.print(table)
        console.print()

    if invites:
        invite_table = Table(title="Pending Invites")
        invite_table.add_column("Room ID", style="magenta", no_wrap=True)
        invite_table.add_column("Status", style="yellow")

        for room_id, room_data in invites.items():
            invite_table.add_row(room_id, "Invited")
        console.print(invite_table)


@app.command()
def view(
    room_id: str, limit: int = typer.Option(20, help="Number of messages to view")
):
    """View recent messages in a specific room (auto-joins if needed)."""
    client = get_client()

    with console.status(
        f"Joining and fetching messages for {room_id}...", spinner="dots"
    ):
        try:
            # Always attempt to join first as requested
            client.join_room(room_id)
            messages = client.get_messages(room_id, limit=limit)
        except Exception as e:
            console.print(f"[bold red]Failed to fetch messages:[/] {e}")
            raise typer.Exit(code=1)

    if not messages:
        console.print("[yellow]No messages found in this room.[/]")
        return

    console.print(f"\n[bold underline]Messages in {room_id}[/]\n")
    for msg in messages:
        content = msg.get("content", {})
        sender = msg.get("sender", "Unknown")
        event_id = msg.get("event_id", "")

        if "body" in content:
            msgtype = content.get("msgtype", "")
            body = content["body"]
            if msgtype == "m.image":
                mxc_url = content.get("url", "")
                if mxc_url:
                    try:
                        local_path = client.download_media(mxc_url)
                        body = f"📸 Image: {body}\n   [green]Downloaded to:[/] {local_path}"
                    except Exception as e:
                        body = f"📸 Image: {body}\n   [red]Failed to download:[/] {e}"
            elif msgtype in ("m.file", "m.video", "m.audio"):
                mxc_url = content.get("url", "")
                if mxc_url:
                    try:
                        local_path = client.download_media(mxc_url)
                        body = (
                            f"📎 File: {body}\n   [green]Downloaded to:[/] {local_path}"
                        )
                    except Exception as e:
                        body = f"📎 File: {body}\n   [red]Failed to download:[/] {e}"
        else:
            body = f"[italic gray]<Event: {msg.get('type')}>[/]"

        console.print(f"[bold blue]{sender}[/] [dim]({event_id})[/]: {body}")
    console.print()


@app.command()
def reply(
    room_id: str,
    message: str,
    reply_to: str = typer.Option(
        None, "--reply-to", "-r", help="Event ID of the message to reply to"
    ),
):
    """Send a text reply to a specific room or message."""
    client = get_client()

    with console.status(f"Sending message to {room_id}...", spinner="dots"):
        try:
            response = client.send_message(room_id, message, reply_to_event_id=reply_to)
            event_id = response.get("event_id")
            console.print(
                f"[bold green]Message sent successfully![/] Event ID: {event_id}"
            )
        except Exception as e:
            console.print(f"[bold red]Failed to send message:[/] {e}")
            raise typer.Exit(code=1)


@app.command()
def join(room_id: str):
    """Join a Matrix room by its ID or alias."""
    client = get_client()

    with console.status(f"Joining {room_id}...", spinner="dots"):
        try:
            client.join_room(room_id)
            console.print(f"[bold green]Successfully joined {room_id}![/]")
        except Exception as e:
            console.print(f"[bold red]Failed to join room:[/] {e}")
            raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
