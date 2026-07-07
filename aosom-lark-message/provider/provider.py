from typing import Any

import httpx
from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError


class LarkMessageProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        app_id = credentials.get("lark_app_id", "")
        app_secret = credentials.get("lark_app_secret", "")
        base_url = credentials.get("lark_base_url", "https://open.feishu.cn")

        if not app_id:
            raise ToolProviderCredentialValidationError("Lark App ID is required")
        if not app_secret:
            raise ToolProviderCredentialValidationError("Lark App Secret is required")

        try:
            resp = httpx.post(
                f"{base_url}/open-apis/auth/v3/tenant_access_token/internal",
                json={"app_id": app_id, "app_secret": app_secret},
                timeout=10,
            )
            data = resp.json()
            if data.get("code") != 0:
                raise ToolProviderCredentialValidationError(
                    f"Invalid credentials: {data.get('msg', '')}"
                )
        except httpx.HTTPError as e:
            raise ToolProviderCredentialValidationError(
                f"Failed to validate credentials: {e}"
            )
