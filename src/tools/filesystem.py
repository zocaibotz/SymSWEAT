import os
from typing import Dict, Any, List

class LocalFileSystemTool:
    def __init__(self, root_dir: str = "."):
        self.root_dir = os.path.abspath(root_dir)

    def _get_path(self, path: str) -> str:
        full_path = os.path.abspath(os.path.join(self.root_dir, path))
        try:
            if os.path.commonpath([self.root_dir, full_path]) != self.root_dir:
                raise ValueError(f"Access denied: {path} is outside root {self.root_dir}")
        except ValueError:
            # Different drives/invalid paths are denied by default
            raise ValueError(f"Access denied: {path} is outside root {self.root_dir}")
        return full_path

    def read_file(self, path: str) -> str:
        try:
            with open(self._get_path(path), "r") as f:
                return f.read()
        except FileNotFoundError:
            return f"Error: File not found: {path}"
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def write_file(self, path: str, content: str) -> str:
        try:
            full_path = self._get_path(path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w") as f:
                f.write(content)
            return f"Successfully wrote to {path}"
        except Exception as e:
            return f"Error writing file: {str(e)}"

    def list_directory(self, path: str = ".") -> List[str]:
        try:
            return os.listdir(self._get_path(path))
        except Exception as e:
            return [f"Error listing directory: {str(e)}"]

class MockMCPClient:
    """
    Simulates an MCP client connecting to a local tool implementation.
    """
    def __init__(self, tool_impl: Any):
        self.tool = tool_impl
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name == "read_file":
            result = self.tool.read_file(arguments.get("path"))
        elif tool_name == "write_file":
            result = self.tool.write_file(arguments.get("path"), arguments.get("content"))
        elif tool_name == "list_directory":
            result = self.tool.list_directory(arguments.get("path", "."))
        else:
            return {"status": "error", "message": f"Unknown tool: {tool_name}"}
            
        return {"status": "success", "result": result}
    
    def list_directory(self, path: str = ".") -> List[str]:
        """Direct access for internal agents."""
        return self.tool.list_directory(path)

# Singleton for the workspace
_fs_client = None

def get_filesystem_client(root_dir: str = ".") -> MockMCPClient:
    global _fs_client
    if _fs_client is None:
        _fs_client = MockMCPClient(LocalFileSystemTool(root_dir))
    return _fs_client
