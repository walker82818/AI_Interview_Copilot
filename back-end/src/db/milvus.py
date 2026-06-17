from typing import Optional

from loguru import logger
from pymilvus import Collection, connections, utility

from src.core.config import settings

_client_connected = False


def connect_milvus() -> None:
    global _client_connected
    if _client_connected:
        return
    try:
        connections.connect(
            alias="default",
            host=settings.milvus_host,
            port=str(settings.milvus_port),
        )
        _client_connected = True
        logger.info("Milvus connected: {}:{}", settings.milvus_host, settings.milvus_port)
    except Exception as exc:
        logger.warning("Milvus unavailable: {}", exc)


def get_collection(name: Optional[str] = None) -> Optional[Collection]:
    connect_milvus()
    collection_name = name or settings.milvus_collection
    if not utility.has_collection(collection_name):
        logger.warning("Milvus collection not found: {}", collection_name)
        return None
    return Collection(collection_name)


def disconnect_milvus() -> None:
    global _client_connected
    if _client_connected:
        connections.disconnect("default")
        _client_connected = False
