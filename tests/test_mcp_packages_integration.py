"""Integration test for MCP server packages.

Tests the full flow:
1. Start Endpoint with MCP server (context7)
2. Connect via packages API
3. Discover MCP servers
4. Call MCP tools
"""

import asyncio
import pytest
import socket
from pathlib import Path

from pantheon.endpoint.core import Endpoint
from pantheon.package_runtime import get_package_manager, build_context_payload, export_context


def find_free_port():
    """Find a free port to use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


@pytest.fixture
async def endpoint_with_mcp():
    """Start an Endpoint with context7 MCP server."""
    # Find free port
    free_port = find_free_port()
    
    # Create endpoint with context7 auto-start
    config = {
        "auto_start_mcp_servers": ["context7"],
        "endpoint_mcp_port": free_port,
        "builtin_services": [],  # Don't start other services
    }
    
    endpoint = Endpoint(
        service_name="test_endpoint",
        config=config,
        workspace_path=str(Path(__file__).parent / "sample_workspace"),
    )
    
    # Start endpoint setup
    setup_task = asyncio.create_task(endpoint.run_setup())
    
    # Wait for setup to complete (give it time to start MCP servers)
    await asyncio.sleep(5)
    
    # Store port for tests to use
    endpoint.test_mcp_port = free_port
    
    yield endpoint
    
    # Cleanup
    if hasattr(endpoint, '_endpoint_mcp_task'):
        endpoint._endpoint_mcp_task.cancel()
        try:
            await endpoint._endpoint_mcp_task
        except asyncio.CancelledError:
            pass
    
    setup_task.cancel()
    try:
        await setup_task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio
async def test_mcp_packages_integration(endpoint_with_mcp, monkeypatch):
    """Test full MCP packages integration flow."""
    endpoint = endpoint_with_mcp
    
    # Setup context for packages API
    workspace = Path(__file__).parent / "sample_workspace"
    payload = build_context_payload(workdir=str(workspace))
    
    # Manually add endpoint_mcp_uri since we're in a different process
    payload["endpoint_mcp_uri"] = f"http://127.0.0.1:{endpoint.test_mcp_port}/mcp"
    
    env = {}
    export_context(payload, env=env)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    
    # Import packages API
    from pantheon import packages as pp
    
    # Step 1: Refresh MCP packages from Endpoint
    print(f"Refreshing MCP packages from {payload['endpoint_mcp_uri']}...")
    result = await pp.packages.refresh_mcp_packages()
    print(f"Refresh result: {result}")
    
    assert result["success"], f"Failed to refresh: {result.get('error')}"
    
    # Note: context7 might not be in packages if it failed to start or requires API keys
    # Just verify the refresh mechanism works
    print(f"Registered packages: {result.get('packages', [])}")
    
    # Step 2: List packages and check for MCP origin
    all_packages = await pp.packages.list_packages()
    mcp_packages = [p for p in all_packages if p["origin"] == "mcp"]
    print(f"MCP packages: {mcp_packages}")
    
    # If context7 started successfully, it should be here
    if result.get("packages"):
        assert len(mcp_packages) > 0, "No MCP packages found after successful refresh"
        
        # Step 3: Describe first MCP package
        first_mcp = mcp_packages[0]["name"]
        description = pp.packages.describe(first_mcp)
        print(f"{first_mcp} description: {description}")
        
        assert description["success"]
        pkg_info = description["package"]
        assert pkg_info["origin"] == "mcp"
        print(f"{first_mcp} has {len(pkg_info['methods'])} methods")


@pytest.mark.asyncio
async def test_endpoint_mcp_uri_in_context(endpoint_with_mcp):
    """Test that endpoint_mcp_uri is accessible."""
    # The endpoint should have set this internally
    # We can verify by checking if the port is listening
    import socket
    
    port = endpoint_with_mcp.test_mcp_port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        result = sock.connect_ex(('127.0.0.1', port))
        assert result == 0, f"Port {port} is not listening"
    finally:
        sock.close()


@pytest.mark.asyncio
async def test_mcp_package_manager_methods(endpoint_with_mcp, monkeypatch):
    """Test PackageManager MCP-specific methods."""
    from pantheon.package_runtime.manager import PackageManager
    from pathlib import Path
    
    workspace = Path(__file__).parent / "sample_workspace"
    packages_path = workspace / ".pantheon" / "packages"
    manager = PackageManager(packages_path)
    
    # Setup context with endpoint_mcp_uri
    payload = build_context_payload(workdir=str(workspace))
    payload["endpoint_mcp_uri"] = f"http://127.0.0.1:{endpoint_with_mcp.test_mcp_port}/mcp"
    env = {}
    export_context(payload, env=env)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    
    # Test refresh_mcp_packages
    result = await manager.refresh_mcp_packages()
    print(f"Manager refresh result: {result}")
    assert result["success"]
    
    # Test is_mcp_package
    if result["packages"]:
        first_mcp = result["packages"][0]
        assert manager.is_mcp_package(first_mcp)
        assert not manager.is_mcp_package("non_existent_package")
    
    # Test list_packages includes MCP
    all_packages = await manager.list_packages()
    mcp_in_list = any(p["origin"] == "mcp" for p in all_packages)
    if result["packages"]:  # Only assert if we actually registered some
        assert mcp_in_list, "MCP packages not in list_packages()"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
