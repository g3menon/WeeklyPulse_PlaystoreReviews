import asyncio
import json
import logging
import os
import sys

# We check if mcp is installed 
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    StdioServerParameters = None

from phase1_setup.config import COMBINED_PULSE_PATH

logger = logging.getLogger("phase10b_mcp_appender")

async def run_mcp_appender_async():
    logger.info("Initializing MCP Google Docs appender...")
    
    if not StdioServerParameters:
        logger.error("The 'mcp' Python package is not installed. Please run: pip install mcp")
        return

    if not os.path.exists(COMBINED_PULSE_PATH):
        logger.error("combined_pulse.json does not exist. Skipping MCP append.")
        return
        
    with open(COMBINED_PULSE_PATH, "r", encoding="utf-8") as f:
        combined_data = json.load(f)
        
    doc_id = os.environ.get("GOOGLE_DOC_ID")
    mcp_credentials = os.environ.get("GOOGLE_DOCS_CREDENTIALS", "")
    
    if not doc_id:
        logger.warning("GOOGLE_DOC_ID is not set in environment. Skipping GCP MCP invocation.")
        return
        
    # Use MCP SDK over Stdio instead of direct API
    cmd = os.environ.get("MCP_GOOGLE_DOCS_SERVER_CMD", "npx")
    args_str = os.environ.get("MCP_GOOGLE_DOCS_SERVER_ARGS", "-y @anthropic/mcp-google-docs")
    args = args_str.split() if args_str else []
    
    logger.info(f"Configuring MCP StdioServerParameters for {cmd} {' '.join(args)}...")
    
    # We pass the active environment + the credentials path 
    env_vars = os.environ.copy()
    env_vars["GOOGLE_DOCS_CREDENTIALS"] = mcp_credentials
    
    server_params = StdioServerParameters(
        command=cmd,
        args=args, 
        env=env_vars
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                logger.info("Initializing MCP session with the Google Docs server...")
                await session.initialize()
                
                # Format the text to append
                text_content = f"\n\n=== Weekly Pulse ({combined_data.get('date')}) ===\n"
                text_content += json.dumps(combined_data, indent=2)

                logger.info(f"Calling tool 'append_document' on MCP Server for doc {doc_id}...")
                
                # Call the MCP server's append tool
                result = await session.call_tool("append_document", {
                    "document_id": doc_id,
                    "text": text_content
                })
                
                logger.info(f"MCP Server response successful. Data appended to Google Doc via MCP.")
                
    except Exception as e:
        logger.error(f"MCP invocation failed. Ensure 'npx' is accessible and the MCP server package exists. Error: {e}")
        logger.warning("Graceful degradation: pipeline continues without appending.")


def run_mcp_appender():
    asyncio.run(run_mcp_appender_async())

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_mcp_appender()
