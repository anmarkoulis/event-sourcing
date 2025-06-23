def configure_openapi_tags() -> list:
    """
    Configures OpenAPI tags based on the authentication type.
    """
    tags = [{"name": "health", "description": "Health check"}]
    return sorted(tags, key=lambda x: x["name"])
