# Phase 10B: Google Docs MCP Appender

This phase is responsible for combining the results of the Weekly Pulse (Phase 5) and the Fee Explainer (Phase 10A) into a single JSON schema and gracefully appending it to an ongoing Google Doc. It leverages the Model Context Protocol (MCP) to standardize external tool calling.

## Features

- **Standardized Append Schema:** Combines `weekly_pulse.json` and `fee_explanation.json` strictly to the required archive structure.
- **MCP Standards-Based Tooling:** Instead of building a bespoke Google API client, we use the `mcp-gdocs` MCP server.
- **Graceful Failure Defaults:** If the Google Document is unavailable, the user credentials are not configured, or if `npx` fails to invoke the MCP server, the system will log warnings and degrade gracefully, allowing the main pipeline to finish seamlessly.
- **Secure configuration:** Relies on `.env` configuration mapping the proper credentials.

## Setup Requirements

1. Make sure you have the `mcp-gdocs` package correctly set in your `.env`:
   ```env
   GOOGLE_DOC_ID=your_google_doc_id_here
   MCP_GOOGLE_DOCS_SERVER_CMD=npx
   MCP_GOOGLE_DOCS_SERVER_ARGS=-y mcp-gdocs
   GOOGLE_DOCS_CREDENTIALS="path/to/your/service_account_credentials.json"
   ```
2. You must have Node.js (`npx`) installed on the system to invoke the server, along with Python's `mcp>=1.0.0`.

## Scripts

- `json_combiner.py`: Loads the JSONs from `data/` and builds the final schema.
- `gdocs_appender.py`: Initiates standard IO MCP streams to `mcp-gdocs` and executes the `append_document` tool.
