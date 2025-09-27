"""Custom exceptions for the supervisor agent system."""

from typing import Any, Dict, Optional


class SupervisorAgentError(Exception):
    """Base exception for all supervisor agent related errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the exception.

        Args:
            message: Error message
            error_code: Optional error code for categorization
            details: Optional additional error details
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

    def __str__(self) -> str:
        """Return string representation of the error."""
        error_str = self.message
        if self.error_code:
            error_str = f"[{self.error_code}] {error_str}"
        return error_str


class ConfigurationError(SupervisorAgentError):
    """Exception raised for configuration-related errors."""

    def __init__(self, message: str, config_key: Optional[str] = None):
        """Initialize the configuration error.

        Args:
            message: Error message
            config_key: The configuration key that caused the error
        """
        super().__init__(message, "CONFIG_ERROR", {"config_key": config_key})
        self.config_key = config_key


class AgentCreationError(SupervisorAgentError):
    """Exception raised when agent creation fails."""

    def __init__(
        self,
        message: str,
        agent_name: Optional[str] = None,
        agent_type: Optional[str] = None,
    ):
        """Initialize the agent creation error.

        Args:
            message: Error message
            agent_name: Name of the agent that failed to create
            agent_type: Type of the agent that failed to create
        """
        super().__init__(
            message,
            "AGENT_CREATION_ERROR",
            {"agent_name": agent_name, "agent_type": agent_type},
        )
        self.agent_name = agent_name
        self.agent_type = agent_type


class MCPConnectionError(SupervisorAgentError):
    """Exception raised when MCP server connection fails."""

    def __init__(
        self,
        message: str,
        server_name: Optional[str] = None,
        server_url: Optional[str] = None,
    ):
        """Initialize the MCP connection error.

        Args:
            message: Error message
            server_name: Name of the MCP server
            server_url: URL of the MCP server
        """
        super().__init__(
            message,
            "MCP_CONNECTION_ERROR",
            {"server_name": server_name, "server_url": server_url},
        )
        self.server_name = server_name
        self.server_url = server_url


class SupervisorInitializationError(SupervisorAgentError):
    """Exception raised when supervisor initialization fails."""

    def __init__(self, message: str, stage: Optional[str] = None):
        """Initialize the supervisor initialization error.

        Args:
            message: Error message
            stage: The initialization stage where the error occurred
        """
        super().__init__(message, "SUPERVISOR_INIT_ERROR", {"stage": stage})
        self.stage = stage


class RequestProcessingError(SupervisorAgentError):
    """Exception raised when request processing fails."""

    def __init__(
        self,
        message: str,
        request_id: Optional[str] = None,
        agent_name: Optional[str] = None,
    ):
        """Initialize the request processing error.

        Args:
            message: Error message
            request_id: ID of the request that failed
            agent_name: Name of the agent where processing failed
        """
        super().__init__(
            message,
            "REQUEST_PROCESSING_ERROR",
            {"request_id": request_id, "agent_name": agent_name},
        )
        self.request_id = request_id
        self.agent_name = agent_name


class ToolExecutionError(SupervisorAgentError):
    """Exception raised when tool execution fails."""

    def __init__(
        self,
        message: str,
        tool_name: Optional[str] = None,
        tool_args: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the tool execution error.

        Args:
            message: Error message
            tool_name: Name of the tool that failed
            tool_args: Arguments passed to the tool
        """
        super().__init__(
            message,
            "TOOL_EXECUTION_ERROR",
            {"tool_name": tool_name, "tool_args": tool_args},
        )
        self.tool_name = tool_name
        self.tool_args = tool_args


class ValidationError(SupervisorAgentError):
    """Exception raised for validation errors."""

    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        field_value: Optional[Any] = None,
    ):
        """Initialize the validation error.

        Args:
            message: Error message
            field_name: Name of the field that failed validation
            field_value: Value that failed validation
        """
        super().__init__(
            message,
            "VALIDATION_ERROR",
            {"field_name": field_name, "field_value": field_value},
        )
        self.field_name = field_name
        self.field_value = field_value


class ServiceNotAvailableError(SupervisorAgentError):
    """Exception raised when a required service is not available."""

    def __init__(self, message: str, service_name: Optional[str] = None):
        """Initialize the service not available error.

        Args:
            message: Error message
            service_name: Name of the unavailable service
        """
        super().__init__(
            message, "SERVICE_NOT_AVAILABLE", {"service_name": service_name}
        )
        self.service_name = service_name


def handle_exception(func):
    """Decorator to handle exceptions and convert them to appropriate custom exceptions."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SupervisorAgentError:
            # Re-raise custom exceptions as-is
            raise
        except ValueError as e:
            raise ValidationError(str(e))
        except ConnectionError as e:
            raise MCPConnectionError(str(e))
        except Exception as e:
            # Convert unknown exceptions to base SupervisorAgentError
            raise SupervisorAgentError(f"Unexpected error: {str(e)}", "UNKNOWN_ERROR")

    return wrapper


async def handle_async_exception(func):
    """Async decorator to handle exceptions and convert them to appropriate custom exceptions."""

    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except SupervisorAgentError:
            # Re-raise custom exceptions as-is
            raise
        except ValueError as e:
            raise ValidationError(str(e))
        except ConnectionError as e:
            raise MCPConnectionError(str(e))
        except Exception as e:
            # Convert unknown exceptions to base SupervisorAgentError
            raise SupervisorAgentError(f"Unexpected error: {str(e)}", "UNKNOWN_ERROR")

    return wrapper
