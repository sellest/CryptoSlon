from langchain_core.messages import BaseMessage

def msg_to_dict(message: BaseMessage) -> dict:
    """Преобразует объект BaseMessage в явный словарь"""
    return {
        "type": message.type,
        "content": message.content,
        "additional_kwargs": message.additional_kwargs,
        **({"tool_calls": message.tool_calls} if hasattr(message, "tool_calls") else {}),
        **({"example": message.example} if hasattr(message, "example") else {}),
    }
