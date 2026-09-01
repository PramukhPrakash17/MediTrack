from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, loaded once from environment variables / .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # MCP servers
    symptoms_mcp_url: str
    drug_mcp_url: str
    xray_mcp_url: str
    backend_mcp_url: str

    # Backend's plain REST base URL (e.g. http://backend:8080). Used only for
    # the lab-report upload, which travels as real multipart/form-data
    # straight to Backend's existing endpoint rather than through MCP.
    backend_base_url: str

    # Orchestration LLM. "groq" (hosted) or "ollama" (local, no rate limit).
    llm_provider: str = "groq"

    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"

    ollama_model: str = "qwen2.5:7b-instruct"
    ollama_base_url: str = "http://localhost:11434"

    llm_temperature: float = 0.15
    llm_max_tokens: int = 1024

    # Uploaded X-ray images are written here for the duration of a consultation
    temp_upload_dir: str = "temp_uploads"


settings = Settings()

MCP_SERVER_URLS: dict[str, str] = {
    "symptoms": settings.symptoms_mcp_url,
    "drug": settings.drug_mcp_url,
    "xray": settings.xray_mcp_url,
    "backend": settings.backend_mcp_url,
}
