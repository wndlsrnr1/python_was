from __future__ import annotations

import logging
from typing import Any, Optional
from uuid import UUID

from django.db import transaction
from django.db.models import QuerySet

from transcription.models import RealtimeSTTConfig
from transcription.repositories import RealtimeSTTConfigRepository
from shared_kernel.utils.encryption import encrypt, decrypt
from shared_kernel.user import User
from projects.services import ServiceError

logger = logging.getLogger(__name__)


class RealtimeSTTConfigService:
    """실시간 STT 설정 서비스"""

    @staticmethod
    def list_all(provider: Optional[str] = None) -> QuerySet[RealtimeSTTConfig]:
        """모든 실시간 STT 설정 조회 (provider 필터 지원)"""
        if provider:
            return RealtimeSTTConfigRepository.list_by_provider(provider)
        return RealtimeSTTConfigRepository.list_all()

    @staticmethod
    @transaction.atomic
    def create(data: dict[str, Any], user: User) -> RealtimeSTTConfig:
        """실시간 STT 설정 생성"""
        provider = data.get("provider")
        if not provider:
            raise ServiceError("Provider is required", status_code=400)

        # NAVER 제공업체는 API URL 필수
        api_url = data.get("api_url")
        if provider == RealtimeSTTConfig.PROVIDER_NAVER and not api_url:
            raise ServiceError(
                "NAVER 제공업체는 API URL이 필수입니다.", status_code=400
            )

        # API 키 암호화
        api_key = data.get("api_key", "")
        encrypted_key = encrypt(api_key) if api_key else ""

        config = RealtimeSTTConfigRepository.create(
            provider=provider,
            title=data.get("title"),
            api_key=encrypted_key,
            api_url=data.get("api_url"),
            is_active=data.get("is_active", False),
        )

        return config

    @staticmethod
    def get_by_id(config_id: UUID) -> Optional[RealtimeSTTConfig]:
        """ID로 실시간 STT 설정 조회"""
        return RealtimeSTTConfigRepository.get_by_id(config_id)

    @staticmethod
    def get_active() -> Optional[RealtimeSTTConfig]:
        """활성화된 실시간 STT 설정 조회"""
        return RealtimeSTTConfigRepository.get_active()

    @staticmethod
    @transaction.atomic
    def update(config_id: UUID, data: dict[str, Any], user: User) -> RealtimeSTTConfig:
        """실시간 STT 설정 업데이트"""
        config = RealtimeSTTConfigRepository.get_by_id(config_id)
        if not config:
            raise ServiceError("Realtime STT config not found", status_code=404)

        # NAVER 제공업체는 API URL 필수
        provider = data.get("provider", config.provider)
        api_url = data.get("api_url", config.api_url)
        if provider == RealtimeSTTConfig.PROVIDER_NAVER and not api_url:
            raise ServiceError(
                "NAVER 제공업체는 API URL이 필수입니다.", status_code=400
            )

        # API 키 암호화 (제공된 경우)
        update_fields: dict[str, Any] = {}
        if "api_key" in data:
            api_key = data.get("api_key", "")
            update_fields["api_key"] = encrypt(api_key) if api_key else ""

        if "provider" in data:
            update_fields["provider"] = data["provider"]
        if "title" in data:
            update_fields["title"] = data.get("title")
        if "api_url" in data:
            update_fields["api_url"] = data.get("api_url")
        if "is_active" in data:
            update_fields["is_active"] = data.get("is_active", False)

        updated_config = RealtimeSTTConfigRepository.update(config, **update_fields)
        return updated_config

    @staticmethod
    @transaction.atomic
    def delete(config_id: UUID, user: User) -> None:
        """실시간 STT 설정 삭제"""
        config = RealtimeSTTConfigRepository.get_by_id(config_id)
        if not config:
            raise ServiceError("Realtime STT config not found", status_code=404)

        provider = config.provider
        RealtimeSTTConfigRepository.delete(config)

    @staticmethod
    @transaction.atomic
    def activate(config_id: UUID, user: User) -> RealtimeSTTConfig:
        """실시간 STT 설정 활성화 (단일 활성 강제)"""
        config = RealtimeSTTConfigRepository.get_by_id(config_id)
        if not config:
            raise ServiceError("Realtime STT config not found", status_code=404)

        # 다른 모든 설정 비활성화
        RealtimeSTTConfigRepository.deactivate_all()
        # 현재 설정 활성화
        activated_config = RealtimeSTTConfigRepository.update(config, is_active=True)

        return activated_config

    @staticmethod
    @transaction.atomic
    def deactivate(config_id: UUID, user: User) -> RealtimeSTTConfig:
        """실시간 STT 설정 비활성화"""
        config = RealtimeSTTConfigRepository.get_by_id(config_id)
        if not config:
            raise ServiceError("Realtime STT config not found", status_code=404)

        deactivated_config = RealtimeSTTConfigRepository.update(config, is_active=False)
        return deactivated_config

    @staticmethod
    def get_decrypted_api_key(config: RealtimeSTTConfig) -> str:
        """복호화된 API 키 반환"""
        if not config.api_key:
            return ""
        decrypted = decrypt(config.api_key)
        return decrypted or ""


__all__ = ["RealtimeSTTConfigService"]
