#!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv
from mcp.server import Server
from mcp.types import Tool

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "config.env"))

BOL_CLIENT_ID = os.getenv("BOL_CLIENT_ID")
BOL_CLIENT_SECRET = os.getenv("BOL_CLIENT_SECRET")

TOKEN_URL = "https://login.bol.com/token?grant_type=client_credentials"
ORDERS_URL = "https://api.bol.com/retailer/orders"

server = Server(name="bol-api-server", version="1.0.0")

def bol_token():
    """Get Bol.com OAuth token."""
    resp = requests.post(
        TOKEN_URL,
        auth=(BOL_CLIENT_ID, BOL_CLIENT_SECRET),
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    resp.raise_for_status()
    return resp.json()["access_token"]

@server.tool(
    Tool(
        name="fetch_bol_orders",
        description="Retrieve all open Bol.com orders.",
        input_schema={"type": "object", "properties": {}}
    )
)
def fetch_bol_orders(_):
    token = bol_token()
    resp = requests.get(
        ORDERS_URL,
        headers={"Authorization": f"Bearer {token}"}
    )
    resp.raise_for_status()
    return resp.json()

# Add additional tools later:
# - classify_orders
# - generate_excel_batch
# - upload_to_ftp
# - send_email_report
# - process_status_callbacks

if __name__ == "__main__":
    server.run()