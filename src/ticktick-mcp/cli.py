#!/usr/bin/env python3
"""
Command-line interface for TickTick MCP server.
Používá access token z lib/tokens/ticktick-mcp.json.
"""

import sys
import os
import argparse
import logging
import json
from pathlib import Path

TOKEN_PATH = Path(__file__).parent.parent / "lib" / "tokens" / "ticktick_tokens.json"

def load_access_token():
    """Načte access token ze souboru."""
    if not TOKEN_PATH.exists():
        print(f"Soubor s tokenem neexistuje: {TOKEN_PATH}", file=sys.stderr)
        return None
    try:
        with open(TOKEN_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("access_token")
    except Exception as e:
        print(f"Chyba při načítání tokenu: {e}", file=sys.stderr)
        return None

def main():
    """Entry point for the CLI."""
    parser = argparse.ArgumentParser(description="TickTick MCP Server")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # 'run' command for running the server
    run_parser = subparsers.add_parser("run", help="Run the TickTick MCP server")
    run_parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug logging"
    )
    run_parser.add_argument(
        "--transport", 
        default="stdio", 
        choices=["stdio"], 
        help="Transport type (currently only stdio is supported)"
    )
    
    args = parser.parse_args()
    
    # Pokud není access token, nelze pokračovat
    access_token = load_access_token()
    if not access_token:
        print("""
╔════════════════════════════════════════════════╗
║      TickTick MCP Server - Authentication      ║
╚════════════════════════════════════════════════╝

Chybí access token!
Nejdříve proveďte OAuth autentizaci přes backend a uložte token do lib/tokens/ticktick_tokens.json.

""")
        sys.exit(1)
    
    # Run the appropriate command
    if args.command == "run" or not args.command:
        # Configure logging based on debug flag
        log_level = logging.DEBUG if args.debug else logging.INFO
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
        # Start the server, předávej access_token podle potřeby
        try:
            server_main(access_token)
        except KeyboardInterrupt:
            print("Server stopped by user", file=sys.stderr)
            sys.exit(0)
        except Exception as e:
            print(f"Error starting server: {e}", file=sys.stderr)
            sys.exit(1)

def server_main(access_token):
    # Zde použij access_token pro komunikaci s TickTick API
    print(f"Server běží s access tokenem: {access_token[:8]}...")

if __name__ == "__main__":
    main()