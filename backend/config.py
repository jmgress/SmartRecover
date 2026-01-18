from pydantic import BaseModel, Field, SecretStr, field_validator
from typing import Optional, Literal, Dict
import os
import logging

logger = logging.getLogger(__name__)


class ServiceNowConfig(BaseModel):
    """Configuration for ServiceNow connector."""
    instance_url: str = Field(..., min_length=1, description="ServiceNow instance URL")
    username: str = Field(..., min_length=1, description="ServiceNow username")
    password: SecretStr = Field(..., description="ServiceNow password")
    client_id: Optional[str] = Field(default=None, description="OAuth client ID (optional)")
    client_secret: Optional[SecretStr] = Field(default=None, description="OAuth client secret (optional)")


class JiraConfig(BaseModel):
    """Configuration for Jira Service Management connector."""
    url: str = Field(..., min_length=1, description="Jira instance URL")
    username: str = Field(..., min_length=1, description="Jira username/email")
    api_token: SecretStr = Field(..., description="Jira API token")
    project_key: str = Field(..., min_length=1, description="Jira project key")


class MockConfig(BaseModel):
    """Configuration for Mock connector."""
    data_source: str = Field(default="mock", description="Data source identifier")


class ConnectorConfig(BaseModel):
    """Main configuration for incident management connector."""
    connector_type: Literal["servicenow", "jira", "mock"] = Field(
        default="mock",
        description="Type of connector to use"
    )
    servicenow: Optional[ServiceNowConfig] = None
    jira: Optional[JiraConfig] = None
    mock: Optional[MockConfig] = None


def _validate_required_env_vars(env_vars: Dict[str, Optional[str]], service_name: str) -> None:
    """
    Validate that required environment variables are set.
    
    Args:
        env_vars: Dictionary mapping environment variable names to their values
        service_name: Name of the service (for error messages, e.g., "ServiceNow", "Jira")
        
    Raises:
        ValueError: If any required environment variables are missing
    """
    missing = [name for name, value in env_vars.items() if not value]
    if missing:
        error_msg = f"Missing required {service_name} configuration: {', '.join(missing)}"
        logger.error(error_msg)
        raise ValueError(error_msg)


def load_config_from_env() -> ConnectorConfig:
    """
    Load connector configuration from environment variables.
    
    Environment variables:
    - INCIDENT_CONNECTOR_TYPE: Type of connector (servicenow, jira, mock)
    
    ServiceNow (username/password authentication - default):
    - SERVICENOW_INSTANCE_URL: ServiceNow instance URL
    - SERVICENOW_USERNAME: ServiceNow username
    - SERVICENOW_PASSWORD: ServiceNow password
    
    ServiceNow (OAuth authentication - optional, use instead of username/password):
    - SERVICENOW_CLIENT_ID: ServiceNow OAuth client ID
    - SERVICENOW_CLIENT_SECRET: ServiceNow OAuth client secret
    
    Jira Service Management:
    - JIRA_URL: Jira instance URL
    - JIRA_USERNAME: Jira username/email
    - JIRA_API_TOKEN: Jira API token (generate from Atlassian account settings)
    - JIRA_PROJECT_KEY: Jira project key
    
    Mock:
    - MOCK_DATA_SOURCE: Mock data source identifier (optional, default: "mock")
    
    Returns:
        ConnectorConfig with settings from environment
        
    Raises:
        ValueError: If connector_type is invalid or required configuration is missing
    """
    connector_type = os.getenv("INCIDENT_CONNECTOR_TYPE", "mock")
    
    # Validate connector type
    allowed_connector_types = {"servicenow", "jira", "mock"}
    if connector_type not in allowed_connector_types:
        allowed_values_str = ", ".join(sorted(allowed_connector_types))
        error_msg = (
            f"Invalid INCIDENT_CONNECTOR_TYPE '{connector_type}'. "
            f"Allowed values are: {allowed_values_str}."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    config = ConnectorConfig(connector_type=connector_type)
    
    # Load ServiceNow config
    if connector_type == "servicenow":
        try:
            instance_url = os.getenv("SERVICENOW_INSTANCE_URL")
            username = os.getenv("SERVICENOW_USERNAME")
            password = os.getenv("SERVICENOW_PASSWORD")
            
            _validate_required_env_vars({
                "SERVICENOW_INSTANCE_URL": instance_url,
                "SERVICENOW_USERNAME": username,
                "SERVICENOW_PASSWORD": password
            }, "ServiceNow")
            
            config.servicenow = ServiceNowConfig(
                instance_url=instance_url,
                username=username,
                password=password,
                client_id=os.getenv("SERVICENOW_CLIENT_ID"),
                client_secret=os.getenv("SERVICENOW_CLIENT_SECRET")
            )
        except Exception as e:
            logger.error(f"Failed to load ServiceNow configuration: {e}")
            raise
    
    # Load Jira config
    elif connector_type == "jira":
        try:
            url = os.getenv("JIRA_URL")
            username = os.getenv("JIRA_USERNAME")
            api_token = os.getenv("JIRA_API_TOKEN")
            project_key = os.getenv("JIRA_PROJECT_KEY")
            
            _validate_required_env_vars({
                "JIRA_URL": url,
                "JIRA_USERNAME": username,
                "JIRA_API_TOKEN": api_token,
                "JIRA_PROJECT_KEY": project_key
            }, "Jira")
            
            config.jira = JiraConfig(
                url=url,
                username=username,
                api_token=api_token,
                project_key=project_key
            )
        except Exception as e:
            logger.error(f"Failed to load Jira configuration: {e}")
            raise
    
    # Load Mock config
    else:
        config.mock = MockConfig(
            data_source=os.getenv("MOCK_DATA_SOURCE", "mock")
        )
    
    return config
