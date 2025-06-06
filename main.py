from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
import json
from agent.restaurant_agent import RestaurantAgent

app = FastAPI(title="Symmetrie Restaurant Agent", version="1.0.0")

# Initialize the restaurant agent
restaurant_agent = RestaurantAgent()

@app.get("/")
async def get():
    return FileResponse("home.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                
                if message.get("type") == "query":
                    user_message = message.get("message", "")
                    
                    # Process the query through the agent
                    response = await restaurant_agent.process_query(user_message)
                    
                    # Send response back to client
                    await websocket.send_text(json.dumps(response))
                
                else:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Invalid message type. Expected 'query'."
                    }))
                    
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format."
                }))
                
    except WebSocketDisconnect:
        print("WebSocket disconnected")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 