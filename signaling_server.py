import asyncio
import websockets
import logging
import os  # Import os to get the port

logging.basicConfig(level=logging.INFO)
CONNECTED_CLIENTS = set()

# --- Health Check Function ---
# This is a simple HTTP server that runs in parallel
# to answer Render's "are you alive?" pings.
async def health_check(path, request_headers):
    if path == "/healthz":
        return websockets.http.Response(
            status_code=200,
            headers={"Content-Type": "text/plain"},
            body="OK"
        )

async def handler(websocket):
    logging.info(f"Client connected: {websocket.remote_address}")
    CONNECTED_CLIENTS.add(websocket)
    try:
        async for message in websocket:
            logging.info(f"Relaying message to {len(CONNECTED_CLIENTS) - 1} clients")
            recipients = [client for client in CONNECTED_CLIENTS if client != websocket]
            await asyncio.gather(*[client.send(message) for client in recipients])
    except websockets.exceptions.ConnectionClosed:
        logging.info(f"Client disconnected: {websocket.remote_address}")
    finally:
        CONNECTED_CLIENTS.remove(websocket)

async def main():
    # Get the port from the environment variable Render provides
    port = int(os.environ.get("PORT", 8765))
    logging.info(f"--- Starting WebSocket Server on port {port} ---")
    
    # We add `health_check` to the serve() call
    async with websockets.serve(handler, "0.0.0.0", port, process_request=health_check):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())