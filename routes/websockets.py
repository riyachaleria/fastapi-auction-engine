"""
WebSocket endpoints for real-time bidding.
Maintains persistent connections to broadcast live bids to all active clients.
"""
from services.websockets_services import manager, is_bid_highest
from fastapi import Depends, status, APIRouter, WebSocket, WebSocketDisconnect
from database import get_session
from sqlmodel import Session
from jose import jwt, JWTError
from config import config
from models import Item, User
from sqlmodel import select
import json
from datetime import datetime, timezone

router = APIRouter(prefix="/bids", tags=["bids"])

@router.websocket('/{item_id}')
async def bid_an_item(token: str, item_id: int, websocket: WebSocket, session: Session = Depends(get_session)) -> None:
    """
    Establish a real-time WebSocket connection to place bids on a specific item.
    Requires token authentication via query parameter.

    Path Parameters:
        item_id : int — The ID of the auction item

    Query Parameters:
        token : str — A valid JWT access token

    WebSocket Messages (Incoming):
        float/str — The monetary bid amount (e.g., "50.50")

    WebSocket Messages (Outgoing JSON):
        Success: {"new highest bid": 50.50, "bidder": "username", "message": "..."}
        Error:   {"error": "Explanation of why bid failed"}
    """
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM]) 
        username = payload.get('sub')
        if username is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
    except JWTError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket, item_id)
    item_db = session.get(Item, item_id)
    try:
        while True:
            data = await websocket.receive_text()
            bid_amount = float(data)

            current_utc = datetime.now(timezone.utc).replace(tzinfo=None)
            if current_utc > item_db.end_time or not item_db.is_active:
                error_message = {"error": "This auction has completely ended! No more bids allowed."}

                await websocket.send_text(json.dumps(error_message))
                await websocket.close()
                return

            if not is_bid_highest(bid_amount, item_db.current_price):
                error_message = {
                    "error": f"Bid rejected. You must bid higher than the current price of ${item_db.current_price}"
                }

                await websocket.send_text(json.dumps(error_message))
                continue
            
            bidder = session.exec(select(User).where(User.username == username)).first()

            item_db.current_price = bid_amount
            item_db.higher_bidder_id = bidder.id
            session.commit()
            
            message = {
                "new highest bid": bid_amount,
                "bidder": username,
                "message" : f"New highest bid of ${bid_amount} placed by {username}"
            }
            await manager.broadcast(json.dumps(message), item_id)

    except WebSocketDisconnect:
        manager.disconnect(websocket, item_id)