from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.models.admin import Admin
from app.services.inbound.templates import InboundTemplates
from app.api.deps import get_current_admin

router = APIRouter()


class TemplateGenerateRequest(BaseModel):
    template_id: str  # Changed from template_name
    domain: str = ""  # Added domain field
    port: int
    tag: str = ""  # Made optional, will auto-generate
    custom_params: Dict[str, Any] = {}


class TemplateResponse(BaseModel):
    name: str
    description: str
    protocol: str
    template: str
    difficulty: str
    performance: str
    security: str


@router.get("/", response_model=List[TemplateResponse])
async def list_templates(
    current_admin: Admin = Depends(get_current_admin),
):
    """Получить список всех доступных шаблонов inbound"""
    templates = InboundTemplates.get_all_templates()
    return templates


@router.post("/generate")
async def generate_from_template(
    request: TemplateGenerateRequest,
    current_admin: Admin = Depends(get_current_admin),
):
    """Сгенерировать конфигурацию inbound из шаблона"""
    try:
        # Auto-generate tag if not provided
        if not request.tag:
            import random
            request.tag = f"{request.template_id}_{random.randint(1000, 9999)}"
        
        params = {
            "tag": request.tag,
            "port": request.port,
            "domain": request.domain,
            **request.custom_params
        }
        
        config = InboundTemplates.generate_from_template(
            request.template_id,
            **params
        )
        
        return {
            "success": True,
            "config": config,
            "template_id": request.template_id,
            "message": "Конфигурация успешно сгенерирована"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка генерации: {str(e)}"
        )


@router.get("/reality/keys")
async def generate_reality_keys(
    current_admin: Admin = Depends(get_current_admin),
):
    """Генерация новых ключей для Reality"""
    from app.services.inbound.templates import generate_reality_keys
    keys = generate_reality_keys()
    return {
        "privateKey": keys["privateKey"],
        "publicKey": keys["publicKey"],
        "message": "Ключи успешно сгенерированы. Сохраните приватный ключ в безопасном месте."
    }


@router.get("/reality/short-ids")
async def generate_short_ids(
    count: int = 3,
    current_admin: Admin = Depends(get_current_admin),
):
    """Генерация коротких ID для Reality"""
    from app.services.inbound.templates import generate_short_ids
    ids = generate_short_ids(count)
    return {
        "short_ids": ids,
        "count": len(ids)
    }
