"""Draft the Chat Room routes and the fields each route sends back."""

from fastapi import APIRouter, HTTPException, Response

from app.schemas.chat_room import (
    ChatInvitationOut,
    ChatMessageCreate,
    ChatMessageOut,
    ChatRoomCreate,
    ChatRoomOut,
)

router = APIRouter(prefix="/chat", tags=["chat"])


def _chat_not_connected() -> HTTPException:
    # Connect the database and M1 login before adding this router to the app.
    return HTTPException(status_code=501, detail="Chat Room is not connected yet.")


# Get the Chat Rooms the logged-in user is part of.
@router.get("/rooms", response_model=list[ChatRoomOut])
def list_rooms():
    """Return the rooms the current user has joined."""
    raise _chat_not_connected()


# Create a Chat Room and send an invitation to each selected user.
@router.post("/rooms", response_model=ChatRoomOut, status_code=201)
def create_room(request: ChatRoomCreate):
    """Create a pending room from the selected account IDs."""
    raise _chat_not_connected()


# Get a Chat Room when a member opens it.
@router.get("/rooms/{room_id}", response_model=ChatRoomOut)
def get_room(room_id: int):
    """Return the room's status and joined members."""
    raise _chat_not_connected()


# Have the logged-in member exit the Chat Room.
@router.post("/rooms/{room_id}/leave", status_code=204, response_class=Response)
def leave_room(room_id: int):
    """Remove the current member and update the room status."""
    raise _chat_not_connected()


# Get the invitations sent to the logged-in user.
@router.get("/invitations", response_model=list[ChatInvitationOut])
def list_invitations():
    """Return the current user's pending invitations."""
    raise _chat_not_connected()


# Accept an invitation and join the Chat Room.
@router.post("/invitations/{invitation_id}/accept", response_model=ChatRoomOut)
def accept_invitation(invitation_id: int):
    """Accept the current user's invitation and return the updated room."""
    raise _chat_not_connected()


# Decline an invitation without joining the Chat Room.
@router.post(
    "/invitations/{invitation_id}/decline", status_code=204, response_class=Response
)
def decline_invitation(invitation_id: int):
    """Decline the current user's invitation."""
    raise _chat_not_connected()


# Get the messages a member can see in the Chat Room.
@router.get("/rooms/{room_id}/messages", response_model=list[ChatMessageOut])
def list_messages(room_id: int):
    """Return message history for a current member, even if the room is inactive."""
    raise _chat_not_connected()


# Send a message in an active Chat Room.
@router.post(
    "/rooms/{room_id}/messages", response_model=ChatMessageOut, status_code=201
)
def send_message(room_id: int, request: ChatMessageCreate):
    """Save the text with the signed-in sender and return the saved message."""
    raise _chat_not_connected()
