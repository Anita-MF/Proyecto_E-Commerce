from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Agente de Optimización de Inventario"
    version: str = "1.0.0"
    description: str = "Sistema IA para gestión de inventario E-Commerce"
    debug: bool = True

settings = Settings()