import pytest
from unittest.mock import patch, mock_open, MagicMock, AsyncMock
from pathlib import Path
import json
from fastapi.testclient import TestClient
from app.services.mcp_service import mcp_service


@pytest.fixture
def mock_config():
    """Mock MCP configuration for testing"""
    return {
        "mcpServers": {
            "test-server": {
                "transport": "stdio",
                "command": "python",
                "args": ["tests/mocks/mock_mcp_server.py"]
            }
        }
    }


@pytest.fixture(autouse=True)
async def reset_mcp_service():
    """Reset MCP service state before each test"""
    # Reset the service state
    await mcp_service.shutdown()
    mcp_service._initialized = False
    mcp_service.tools = []
    mcp_service.client = None
    mcp_service._config = None
    yield
    # Clean up after test
    await mcp_service.shutdown()


class TestMCPInitialization:
    """Test MCP service initialization in main.py"""
    
    @pytest.mark.asyncio
    async def test_mcp_initialization_success(self, mock_config):
        """Test successful MCP initialization with config file"""
        # Mock file operations
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=json.dumps(mock_config))), \
             patch('app.services.mcp_service.Client') as mock_client_class:
            
            # Setup mock client
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            
            # Mock tools returned by list_tools
            mock_tool = MagicMock()
            mock_tool.name = "test_tool"
            mock_tool.description = "A test tool"
            mock_tool.inputSchema = {"type": "object", "properties": {}}
            mock_client.list_tools.return_value = [mock_tool]
            
            mock_client_class.return_value = mock_client
            
            # Initialize the service
            await mcp_service.initialize()
            
            # Verify initialization
            assert mcp_service._initialized is True
            assert mcp_service.is_available is True
            assert len(mcp_service.get_tools()) == 1
            assert mcp_service.get_tools()[0]["name"] == "test_tool"
    
    @pytest.mark.asyncio
    async def test_mcp_initialization_no_config(self):
        """Test MCP initialization when config file doesn't exist"""
        # Mock file not existing
        with patch('pathlib.Path.exists', return_value=False):
            # Initialize the service
            await mcp_service.initialize()
            
            # Verify initialization with no tools
            assert mcp_service._initialized is True
            assert mcp_service.is_available is False
            assert len(mcp_service.get_tools()) == 0
            assert mcp_service.client is None
    
    @pytest.mark.asyncio
    async def test_mcp_initialization_invalid_config(self):
        """Test MCP initialization with invalid config file"""
        # Mock file operations with invalid JSON
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data="invalid json")):
            
            # Initialize the service
            await mcp_service.initialize()
            
            # Verify initialization failed gracefully
            assert mcp_service._initialized is True
            assert mcp_service.is_available is False
            assert len(mcp_service.get_tools()) == 0
    
    @pytest.mark.asyncio
    async def test_mcp_initialization_client_error(self, mock_config):
        """Test MCP initialization when client fails to connect"""
        # Mock file operations
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=json.dumps(mock_config))), \
             patch('app.services.mcp_service.Client') as mock_client_class:
            
            # Setup mock client that fails
            mock_client = AsyncMock()
            mock_client.__aenter__.side_effect = Exception("Connection failed")
            mock_client_class.return_value = mock_client
            
            # Initialize the service
            await mcp_service.initialize()
            
            # Verify initialization failed gracefully
            assert mcp_service._initialized is True
            assert mcp_service.is_available is False
            assert len(mcp_service.get_tools()) == 0
    
    @pytest.mark.asyncio
    async def test_mcp_shutdown(self, mock_config):
        """Test MCP service shutdown"""
        # Mock file operations
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=json.dumps(mock_config))), \
             patch('app.services.mcp_service.Client') as mock_client_class:
            
            # Setup mock client
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.list_tools.return_value = []
            mock_client_class.return_value = mock_client
            
            # Initialize and then shutdown
            await mcp_service.initialize()
            assert mcp_service._initialized is True
            
            await mcp_service.shutdown()
            
            # Verify shutdown
            assert mcp_service.client is None
            assert len(mcp_service.tools) == 0
            assert mcp_service._initialized is False
            
            # Verify __aexit__ was called (twice - once from initialize, once from shutdown)
            assert mock_client.__aexit__.call_count == 2
    
    @pytest.mark.asyncio
    async def test_app_startup_with_mcp(self):
        """Test FastAPI app startup initializes MCP"""
        with patch('app.services.mcp_service.mcp_service.initialize') as mock_init, \
             patch('app.services.mcp_service.mcp_service.shutdown') as mock_shutdown, \
             patch('app.services.mcp_service.mcp_service.tools', [{"name": "test"}]):
            
            # Import main to get the app with lifespan
            from main import app
            
            # Create test client which triggers lifespan events
            with TestClient(app):
                # Verify MCP was initialized during startup
                mock_init.assert_called_once()
            
            # Verify MCP was shutdown when app stopped
            mock_shutdown.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_multiple_initialization_calls(self):
        """Test that multiple initialization calls don't re-initialize"""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=json.dumps({"mcpServers": {}}))), \
             patch('app.services.mcp_service.Client') as mock_client_class:
            
            # Setup mock client
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.list_tools.return_value = []
            mock_client_class.return_value = mock_client
            
            # Initialize multiple times
            await mcp_service.initialize()
            await mcp_service.initialize()
            await mcp_service.initialize()
            
            # Verify Client was only created once
            mock_client_class.assert_called_once()