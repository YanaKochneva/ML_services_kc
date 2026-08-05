# services/crud/llm_config.py
from sqlmodel import Session, select
from models.llm_config import LLMConfig
from typing import List, Optional

def create_llm_config(config: LLMConfig, session: Session) -> LLMConfig:
    """
    Создание новой LLM конфигурации.
    """
    config.validate()
    session.add(config)
    session.commit()
    session.refresh(config)
    return config

def get_all_llm_configs(session: Session, active_only: bool = False) -> List[LLMConfig]:
    """
    Получение всех LLM конфигураций.
    """
    query = select(LLMConfig)
    if active_only:
        query = query.where(LLMConfig.is_active == True)
    return session.exec(query).all()

def get_llm_config_by_id(config_id: int, session: Session) -> Optional[LLMConfig]:
    """
    Получение LLM конфигурации по ID.
    """
    return session.get(LLMConfig, config_id)

def get_llm_config_by_name(name: str, session: Session) -> Optional[LLMConfig]:
    """
    Получение LLM конфигурации по имени.
    """
    return session.exec(
        select(LLMConfig).where(LLMConfig.name == name)
    ).first()

def update_llm_config(config_id: int, update_data: dict, session: Session) -> Optional[LLMConfig]:
    """
    Обновление LLM конфигурации.
    """
    config = session.get(LLMConfig, config_id)
    if not config:
        return None
    
    config.update(**update_data)
    session.add(config)
    session.commit()
    session.refresh(config)
    return config

def delete_llm_config(config_id: int, session: Session) -> bool:
    """
    Удаление LLM конфигурации.
    """
    config = session.get(LLMConfig, config_id)
    if not config:
        return False
    
    session.delete(config)
    session.commit()
    return True