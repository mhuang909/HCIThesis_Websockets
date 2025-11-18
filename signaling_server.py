import asyncio
import websockets
import logging
import os
import http

# Configure logging
logging.basicConfig(level=logging.INFO)
CONNECTED_CLIENTS = set()

# --- Health Check Hook (Modern 'websockets' API) ---
# This function runs for EVERY connection request.
# If it returns a response, the WebSocket handshake is skipped (good for health checks).
# If it returns None, the WebSocket handshake proceeds (good for your app).
async def health_check(connection, request):
    if request.path == "/healthz":
        return connection.respond(http.HTTPStatus.OK, "OK\n")
    # If path is NOT /healthz, return None to let the WebSocket connect

async def handler(websocket):
    """
    Handle a new WebSocket connection.
    """
    # 'remote_address' might not be available behind Render's load balancer, 
    # so we use a safe fallback for logging
    client_id = str(websocket.id) 
    logging.info(f"Client connected: {client_id}")
    CONNECTED_CLIENTS.add(websocket)
    
    try:
        async for message in websocket:
            # Relay message to all OTHER clients
            # logging.info(f"Relaying message...") # Uncomment to debug
            recipients = [client for client in CONNECTED_CLIENTS if client != websocket]
            if recipients:
                await asyncio.gather(*[client.send(message) for client in recipients])

    except websockets.exceptions.ConnectionClosed:
        logging.info(f"Client disconnected: {client_id}")
    finally:
        CONNECTED_CLIENTS.remove(websocket)

async def main():
    # Render provides the port in the environment variable
    port = int(os.environ.get("PORT", 8765))
    logging.info(f"--- Starting WebSocket Server on port {port} ---")
    
    # pass the health_check function to process_request
    async with websockets.serve(handler, "0.0.0.0", port, process_request=health_check):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())