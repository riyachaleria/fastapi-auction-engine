"""
WebSocket connection management.
Handles active connections and broadcasting messages to connected clients.
"""
from fastapi import WebSocket

class ConnectionManager():
    """
    Manages active WebSocket connections for live bidding.
    Groups connections by the item ID being bidded on.
    """
    def __init__(self) -> None:
        self.active_connections: dict[int, list[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, item_id: int) -> None:
        """
        Accepts a new WebSocket connection and adds it to the active list for the given item.
        
        Args:
            websocket (WebSocket): The client WebSocket connection.
            item_id (int): The ID of the item being viewed.
        """
        await websocket.accept()

        if item_id not in self.active_connections:
            self.active_connections[item_id] = []

        self.active_connections[item_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, item_id: int) -> None:
        """
        Removes a WebSocket connection from the active list.
        
        Args:
            websocket (WebSocket): The client WebSocket connection.
            item_id (int): The ID of the item.
        """
        if item_id in self.active_connections:
            self.active_connections[item_id].remove(websocket)
        
    async def broadcast(self, message: str, item_id: int) -> None:
        """
        Sends a text message to all active WebSocket connections for a specific item.
        
        Args:
            message (str): The JSON string to broadcast.
            item_id (int): The ID of the item.
        """
        if item_id in self.active_connections:
            for connection in self.active_connections[item_id]:
                await connection.send_text(message)

manager = ConnectionManager()

def is_bid_highest(bid_amount: float, current_bid: float) -> bool:
    """
    Determines if a new bid amount is strictly higher than the current bid.
    
    Args:
        bid_amount (float): The new bid placed by the user.
        current_bid (float): The current highest bid in the database.
        
    Returns:
        bool: True if the bid is valid, False otherwise.
    """
    return bid_amount > current_bid