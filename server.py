from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
import os
import json
import httpx
import asyncio
import subprocess
import platform
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

# Import data collector
from mcp_data_collector import get_collector

app = FastAPI(title="Enhanced Developer's Toolkit")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get the data collector instance
data_collector = get_collector()

# Models for API requests
class DataCollectionSettings(BaseModel):
    enabled: bool

# Routes for the web interface
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/tools", response_class=HTMLResponse)
async def read_tools(request: Request):
    return templates.TemplateResponse("tools.html", {"request": request})

@app.get("/settings", response_class=HTMLResponse)
async def read_settings(request: Request):
    # Get data collection statistics
    statistics = data_collector.get_statistics()
    return templates.TemplateResponse(
        "settings.html", 
        {
            "request": request, 
            "data_collection_enabled": data_collector.enabled,
            "statistics": statistics
        }
    )

@app.get("/logs", response_class=HTMLResponse)
async def read_logs(request: Request):
    return templates.TemplateResponse("logs.html", {"request": request})

# API routes for data collection settings
@app.get("/api/settings/data-collection")
async def get_data_collection_status():
    """Get the current status of data collection."""
    try:
        statistics = data_collector.get_statistics()
        return {
            "status": "success",
            "enabled": data_collector.enabled,
            "statistics": statistics
        }
    except Exception as e:
        logger.error(f"Error getting data collection status: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

@app.post("/api/settings/data-collection")
async def set_data_collection_status(settings: DataCollectionSettings):
    """Update data collection settings."""
    try:
        data_collector.set_enabled(settings.enabled)
        return {
            "status": "success",
            "enabled": settings.enabled,
            "message": f"Data collection {'enabled' if settings.enabled else 'disabled'}"
        }
    except Exception as e:
        logger.error(f"Error updating data collection settings: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

@app.post("/api/settings/export-data")
async def export_collected_data():
    """Export the collected data."""
    try:
        output_dir = os.path.join("exported_data", f"export_{data_collector.session_id}")
        success = data_collector.export_data(output_dir)
        
        if success:
            return {
                "status": "success",
                "message": f"Data exported to {output_dir}",
                "output_dir": output_dir
            }
        else:
            return {
                "status": "error",
                "message": "Failed to export data"
            }
    except Exception as e:
        logger.error(f"Error exporting data: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

# MCP proxy routes
@app.post("/mcp/{path:path}")
async def proxy_mcp_request(path: str, request: Request):
    """
    Proxy requests to the MCP server.
    This also logs the MCP traffic for AI training if enabled.
    """
    try:
        # Get the MCP server URL from environment variable or use default
        mcp_url = os.environ.get("MCP_URL", "http://localhost:9999")
        
        # Read the request body
        body = await request.json()
        
        # Log the request if data collection is enabled
        request_id = ""
        if data_collector.enabled:
            try:
                request_id = data_collector.log_mcp_request(
                    tool_name=path,
                    params=body
                )
            except Exception as e:
                logger.error(f"Error logging MCP request: {e}")
        
        # Forward the request to the MCP server
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{mcp_url}/{path}", 
                json=body,
                timeout=60.0
            )
            
            result = response.json()
            
            # Log the response if data collection is enabled
            if data_collector.enabled and request_id:
                try:
                    data_collector.log_mcp_response(
                        request_id=request_id,
                        result=result,
                        status="success" if response.status_code == 200 else "error",
                        execution_time=response.elapsed.total_seconds()
                    )
                except Exception as e:
                    logger.error(f"Error logging MCP response: {e}")
            
            return result
    except Exception as e:
        logger.error(f"Error proxying MCP request: {e}")
        
        # Log the error response if data collection is enabled
        if data_collector.enabled and request_id:
            try:
                data_collector.log_mcp_response(
                    request_id=request_id,
                    result={"error": str(e)},
                    status="error",
                    execution_time=0
                )
            except Exception as log_e:
                logger.error(f"Error logging MCP error response: {log_e}")
        
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

# Main entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000) 