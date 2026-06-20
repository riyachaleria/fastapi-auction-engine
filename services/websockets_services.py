from fastapi import WebSocket

class ConnectionManager():
    def __init__(self):
        self.active_connections: dict[int,list[WebSocket]] = {}
    
    async def connect(self,websocket: WebSocket,item_id: int):
        await websocket.accept()

        if item_id not in self.active_connections:
            # active_connections is a dict not a list
            self.active_connections[item_id] = []

        self.active_connections[item_id].append(websocket)
    
    def disconnect(self,websocket: WebSocket,item_id: int):
        if item_id in self.active_connections:
            self.active_connections[item_id].remove(websocket)
        
    async def broadcast(self,message: str,item_id: int):
        if item_id in self.active_connections:
            # self.active_connections[item_id] is an key and it contains a list
            # {self.active_connections[item_id]: [------]}
            for connection in self.active_connections[item_id]:
                await connection.send_text(message)

manager = ConnectionManager()

def is_bid_highest(bid_amount: float,current_bid: int) -> bool:
    return bid_amount > current_bid