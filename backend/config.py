from pydantic import BaseModel, Field
from typing import Optional, Literal
import os


class ServiceNowConfig(BaseModel):
    """Configuration for ServiceNow connector."""
    instance_url: str = Field(default="", description="ServiceNow instance URL")
    username: str = Field(default="", description="ServiceNow username")
    password: str = Field(default="", description="ServiceNow password")
    client_id: Optional[str] = Field(default=None, description="OAuth client ID")
    client_secret: Optional[str] = Field(default=None, description="OAuth client secret")


class JiraConfig(BaseModel):
    """Configuration for Jira Service Management connector."""
    url: str = Field(default="", description="Jira instance URL")
    username: str = Field(default="", description="Jira username/email")
    api_token: str = Field(default="", description="Jira API token")
    project_key: str = Field(default="", description="Jira project key")


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


def load_config_from_env() -> ConnectorConfig:
    """
    Load connector configuration from environment variables.
    
    Environment variables:
    - INCIDENT_CONNECTOR_TYPE: Type of connector (servicenow, jira, mock)
    - SERVICENOW_INSTANCE_URL: ServiceNow instance URL
    - SERVICENOW_USERNAME: ServiceNow username
    - SERVICENOW_PASSWORD: ServiceNow password
    - SERVICENOW_CLIENT_ID: ServiceNow OAuth client ID
    - SERVICENOW_CLIENT_SECRET: ServiceNow OAuth client secret
    - JIRA_URL: Jira instance URL
    - JIRA_USERNAME: Jira username/email
    - JIRA_API_TOKEN: Jira API token
    - JIRA_PROJECT_KEY: Jira project key
    - MOCK_DATA_SOURCE: Mock data source identifier
    
    Returns:
        ConnectorConfig with settings from environment
    """
    connector_type = os.getenv("INCIDENT_CONNECTOR_TYPE", "mock")
    
    config = ConnectorConfig(connector_type=connector_type)
    
    # Load ServiceNow config
    if connector_type == "servicenow":
        config.servicenow = ServiceNowConfig(
            instance_url=os.getenv("SERVICENOW_INSTANCE_URL", ""),
            username=os.getenv("SERVICENOW_USERNAME", ""),
            password=os.getenv("SERVICENOW_PASSWORD", ""),
            client_id=os.getenv("SERVICENOW_CLIENT_ID"),
            client_secret=os.getenv("SERVICENOW_CLIENT_SECRET")
        )
    
    # Load Jira config
    elif connector_type == "jira":
        config.jira = JiraConfig(
            url=os.getenv("JIRA_URL", ""),
            username=os.getenv("JIRA_USERNAME", ""),
            api_token=os.getenv("JIRA_API_TOKEN", ""),
            project_key=os.getenv("JIRA_PROJECT_KEY", "")
        )
    
    # Load Mock config
    else:
        config.mock = MockConfig(
            data_source=os.getenv("MOCK_DATA_SOURCE", "mock")
        )
    
    return config
