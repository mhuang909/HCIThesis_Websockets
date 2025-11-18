import logging
import os
from aiohttp import web

# Configure logging
logging.basicConfig(level=logging.INFO)
CONNECTED_CLIENTS = set()

async def websocket_handler(request):
    """
    Handles the WebSocket connection and relaying.
    """
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    client_id = id(ws)
    logging.info(f"Client connected: {client_id}")
    CONNECTED_CLIENTS.add(ws)

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                # Relay the message to all OTHER clients
                # logging.info(f"Relaying message from {client_id}") 
                for client in list(CONNECTED_CLIENTS):
                    if client != ws and not client.closed:
                        await client.send_str(msg.data)
            elif msg.type == web.WSMsgType.ERROR:
                logging.info(f"Connection closed with exception {ws.exception()}")

    finally:
        logging.info(f"Client disconnected: {client_id}")
        CONNECTED_CLIENTS.discard(ws)
    
    return ws

async def health_check(request):
    """
    Standard HTTP health check.
    aiohttp handles GET and HEAD requests automatically.
    """
    return web.Response(text="OK")

async def init_app():
    app = web.Application()
    # Render sends health checks to /healthz
    app.add_routes([web.get('/healthz', health_check),
                    web.get('/', websocket_handler)])
    return app

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8765))
    logging.info(f"--- Starting aiohttp Signaling Server on port {port} ---")
    web.run_app(init_app(), port=port)