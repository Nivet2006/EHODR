#!/usr/bin/env alias python
"""
UAMS Model Context Protocol (MCP) Standard Stdin/Stdout JSON-RPC Server.
Integrates UAMS memory capabilities directly as system tools for Claude and other MCP clients.
No external dependencies required; communicates via raw JSON-RPC 2.0 over standard I/O.
"""

import os
import sys
import json
import asyncio
import traceback
from typing import Dict, Any

# Ensure parent directory is in path to import agents.memory_client
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.memory_client import UniversalMemoryClient

# Setup diagnostics channel to stderr (stdout is strictly reserved for JSON-RPC messages)
def log_diagnostic(msg: str):
    sys.stderr.write(f"[UAMS MCP SERVER] {msg}\n")
    sys.stderr.flush()

class MCPServer:
    """
    JSON-RPC 2.0 Model Context Protocol Server wrapper.
    Exposes memory_save and memory_recall tools over standard inputs and outputs.
    """
    def __init__(self):
        # Retrieve UAMS configurations from environment
        gateway_url = os.environ.get("MEMORY_GATEWAY_URL", "http://localhost:8000")
        api_key = os.environ.get("MEMORY_API_KEY")
        project_id = os.environ.get("MEMORY_PROJECT_ID")
        
        if not api_key or not project_id:
            log_diagnostic(
                "WARNING: MEMORY_API_KEY or MEMORY_PROJECT_ID missing in env. "
                "Client will fail if these are not loaded before tool calls."
            )
            
        self.memory_client = UniversalMemoryClient(
            gateway_url=gateway_url,
            api_key=api_key,
            project_id=project_id,
            agent_id="mcp-server"
        )

    def get_tool_definitions(self) -> Dict[str, Any]:
        """
        Defines the MCP tools schemas to expose to the LLM agent.
        """
        return {
            "tools": [
                {
                    "name": "memory_recall",
                    "description": "Retrieve semantically relevant long-term memories for a task query.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "What you need semantic context about (e.g. 'coding standards', 'database choice')"
                            },
                            "namespace": {
                                "type": "string",
                                "default": "general",
                                "description": "Specific memory namespace filter (e.g. 'architecture', 'decisions')"
                            },
                            "top_k": {
                                "type": "integer",
                                "default": 5,
                                "description": "Maximum relevant memories to fetch"
                            }
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "memory_save",
                    "description": "Persist an important insight, decision, project standard, or fact for future sessions.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "The distilled knowledge/insight to persist (min 10 characters)."
                            },
                            "memory_type": {
                                "type": "string",
                                "enum": [
                                    "architecture_decision",
                                    "deployment_note",
                                    "coding_standard",
                                    "api_contract",
                                    "workflow_state",
                                    "debug_resolution",
                                    "research_summary",
                                    "project_preference",
                                    "long_term_task",
                                    "general_knowledge"
                                ],
                                "description": "Categorization matching universal memory schema rules"
                            },
                            "namespace": {
                                "type": "string",
                                "default": "general",
                                "description": "Sub-category directory isolation inside the project"
                            },
                            "importance_score": {
                                "type": "number",
                                "minimum": 0.0,
                                "maximum": 1.0,
                                "default": 0.5,
                                "description": "Significance: 0.0 (low) to 1.0 (critical, e.g. production credentials standards)"
                            },
                            "source_context": {
                                "type": "string",
                                "description": "Brief explanation of why this was saved"
                            }
                        },
                        "required": ["content", "memory_type"]
                    }
                },
                {
                    "name": "validate_architecture_spec",
                    "description": "Run the automated OpenSpec validator to check if the current codebase configuration and API routes conform exactly to openspec/design/system_architecture.md blueprint.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                }
            ]
        }

    async def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Routes the tool call parameters to the UAMS Gateway APIs.
        """
        log_diagnostic(f"Tool call request: '{name}' with arguments: {arguments}")
        
        try:
            if name == "memory_recall":
                query = arguments.get("query")
                namespace = arguments.get("namespace", "general")
                top_k = int(arguments.get("top_k", 5))
                
                context = await self.memory_client.recall(
                    query=query,
                    namespace=namespace,
                    top_k=top_k
                )
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": context
                        }
                    ]
                }
                
            elif name == "memory_save":
                content = arguments.get("content")
                memory_type = arguments.get("memory_type")
                namespace = arguments.get("namespace", "general")
                importance = float(arguments.get("importance_score", 0.5))
                source = arguments.get("source_context")
                
                memory_id = await self.memory_client.save(
                    content=content,
                    memory_type=memory_type,
                    namespace=namespace,
                    importance_score=importance,
                    source_context=source
                )
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Successfully persisted unique semantic memory entry. ID: {memory_id}"
                        }
                    ]
                }
            elif name == "validate_architecture_spec":
                from scripts.validate_spec import run_all_validation
                # Run the synchronous validation function in an async-friendly executor
                loop = asyncio.get_event_loop()
                conforms = await loop.run_in_executor(None, run_all_validation)
                
                if conforms:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": "SUCCESS: Codebase configuration, ports, and API endpoints are 100% compliant with openspec/design/system_architecture.md blueprint."
                            }
                        ]
                    }
                else:
                    return {
                        "isError": True,
                        "content": [
                            {
                                "type": "text",
                                "text": "CRITICAL CONFORMANCE FAILURE: Codebase has drifted from the system_architecture.md spec. Check gateway logs or run 'python scripts/validate_spec.py' for details."
                            }
                        ]
                    }
            else:
                return {
                    "isError": True,
                    "content": [
                        {
                            "type": "text",
                            "text": f"Tool '{name}' is not supported by UAMS MCP."
                        }
                    ]
                }
        except Exception as e:
            log_diagnostic(f"Tool execution exception: {e}")
            return {
                "isError": True,
                "content": [
                    {
                        "type": "text",
                        "text": f"Error during tool call execution: {str(e)}"
                    }
                ]
            }

    async def start(self):
        """
        Runs the async stdin processing loop, parsing inbound JSON-RPC commands.
        """
        log_diagnostic("MCP standard input/output server successfully initialized.")
        
        loop = asyncio.get_event_loop()
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)
        
        while True:
            try:
                line_bytes = await reader.readline()
                if not line_bytes:
                    break
                    
                line = line_bytes.decode("utf-8").strip()
                if not line:
                    continue
                    
                # Parse JSON-RPC packet
                request = json.loads(line)
                
                # Check protocol validity
                if request.get("jsonrpc") != "2.0":
                    continue
                    
                req_id = request.get("id")
                method = request.get("method")
                params = request.get("params", {})
                
                # Handle MCP initialized lifecycle handshake
                if method == "initialize":
                    response = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {
                                "tools": {}
                            },
                            "serverInfo": {
                                "name": "uams-mcp-server",
                                "version": "2.0.0"
                            }
                        }
                    }
                elif method == "tools/list":
                    response = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": self.get_tool_definitions()
                    }
                elif method == "tools/call":
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})
                    
                    # Process call asynchronously
                    result = await self.handle_tool_call(tool_name, arguments)
                    
                    response = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": result
                    }
                else:
                    # Echo standard JSON-RPC method not found response
                    response = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {
                            "code": -32601,
                            "message": f"Method '{method}' not found."
                        }
                    }
                    
                # Output formatted packet to standard output
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                log_diagnostic(f"JSON-RPC parsing error: {e}")
                log_diagnostic(traceback.format_exc())

if __name__ == "__main__":
    try:
        asyncio.run(MCPServer().start())
    except KeyboardInterrupt:
        log_diagnostic("MCP Server process terminated via key interrupt.")
