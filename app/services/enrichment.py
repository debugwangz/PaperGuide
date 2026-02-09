from app.models.schemas import EnrichmentResult
from app.prompts.templates import ENRICH_SYSTEM_PROMPT, ENRICH_USER_PROMPT
from app.services.llm import get_llm_provider


async def enrich_entry(entry_text: str) -> EnrichmentResult:
    """对用户输入的学习笔记进行结构化处理"""
    llm = get_llm_provider()
    user_prompt = ENRICH_USER_PROMPT.format(entry_text=entry_text)
    result = await llm.generate_json(
        system_prompt=ENRICH_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        schema=EnrichmentResult,
    )
    return result
