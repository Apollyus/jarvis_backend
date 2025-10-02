#!/usr/bin/env python3
"""
MCP Agent API Server - Main Entry Point

This script starts the FastAPI server for the MCP Agent API.

Usage:
    python main.py                          # Run with default settings (localhost:8000)
    python main.py --host 0.0.0.0 --port 8080  # Custom host and port
    python main.py --reload                 # Enable auto-reload for development

Environment Variables:
    API_HOST: Server host address (default: 0.0.0.0)
    API_PORT: Server port number (default: 8000)
    RELOAD: Enable auto-reload mode (default: false)
    LOG_LEVEL: Logging level (default: info)
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add src directory to Python path to ensure imports work correctly
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="MCP Agent API Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default=os.getenv("API_HOST", "0.0.0.0"),
        help="Host address to bind to (default: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("API_PORT", "8000")),
        help="Port number to listen on (default: 8000)"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        default=os.getenv("RELOAD", "").lower() in ("true", "1", "yes"),
        help="Enable auto-reload mode for development"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        default=os.getenv("LOG_LEVEL", "info"),
        choices=["debug", "info", "warning", "error", "critical"],
        help="Set logging level (default: info)"
    )
    
    return parser.parse_args()


def check_requirements():
    """Check if required dependencies are installed."""
    try:
        import fastapi
        import uvicorn
        logger.info("✓ Required dependencies found")
        return True
    except ImportError as e:
        logger.error(f"✗ Missing required dependency: {e.name}")
        logger.error("Please install requirements: pip install -r requirements.txt")
        return False


def main():
    """Main entry point for the API server."""
    try:
        # Parse command-line arguments
        args = parse_arguments()
        
        # Set logging level
        log_level = getattr(logging, args.log_level.upper())
        logging.getLogger().setLevel(log_level)
        
        # Check requirements
        if not check_requirements():
            sys.exit(1)
        
        # Import after adding to path
        from api import app
        import uvicorn
        
        # Display startup information
        logger.info("=" * 60)
        logger.info("Starting MCP Agent API Server")
        logger.info("=" * 60)
        logger.info(f"Host: {args.host}")
        logger.info(f"Port: {args.port}")
        logger.info(f"Reload: {args.reload}")
        logger.info(f"Log Level: {args.log_level}")
        logger.info("=" * 60)
        logger.info(f"API Documentation: http://{args.host if args.host != '0.0.0.0' else 'localhost'}:{args.port}/docs")
        logger.info(f"Health Check: http://{args.host if args.host != '0.0.0.0' else 'localhost'}:{args.port}/health")
        logger.info("=" * 60)
        logger.info("Available Endpoints:")
        logger.info("  GET  /              - Root endpoint")
        logger.info("  GET  /health        - Health check")
        logger.info("  POST /api/chat      - REST chat endpoint")
        logger.info("  WS   /ws/chat       - WebSocket chat endpoint")
        logger.info("  GET  /api/chat/stream - Server-Sent Events chat")
        logger.info("=" * 60)
        logger.info("Press CTRL+C to stop the server")
        logger.info("=" * 60)
        
        # Run the server
        uvicorn.run(
            "api:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level=args.log_level,
            access_log=True
        )
        
    except KeyboardInterrupt:
        logger.info("\n" + "=" * 60)
        logger.info("Server stopped by user")
        logger.info("=" * 60)
        sys.exit(0)
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"Failed to start server: {e}", exc_info=True)
        logger.error("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()