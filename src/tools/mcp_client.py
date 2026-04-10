class MCPClient:
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.connected = False

    def connect(self):
        """
        Connects to the MCP server.
        """
        print(f"Connecting to MCP server at {self.server_url}...")
        self.connected = True

    def call_tool(self, tool_name: str, arguments: dict):
        """
        Calls a tool on the MCP server.
        """
        if not self.connected:
            self.connect()
        
        print(f"Calling tool {tool_name} with args {arguments}")
        # In a real implementation, this would make an HTTP/JSON-RPC request
        return {"status": "success", "result": f"Mock result from {tool_name}"}

# Factory for specific MCP servers
def get_filesystem_client():
    return MCPClient("http://localhost:8001/filesystem")

def get_git_client():
    return MCPClient("http://localhost:8002/git")
