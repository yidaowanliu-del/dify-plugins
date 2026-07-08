import time
from typing import Any

import httpx


class LarkClient:
    """Synchronous Lark/Feishu API client for bitable."""

    def __init__(self, app_id: str, app_secret: str, base_url: str) -> None:
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_url = base_url.rstrip("/")
        self._http = httpx.Client(timeout=30)
        self._tenant_token = ""
        self._token_expire_at = 0.0

    def _ensure_token(self) -> str:
        if self._tenant_token and time.time() < self._token_expire_at - 60:
            return self._tenant_token
        resp = self._http.post(
            f"{self.base_url}/open-apis/auth/v3/tenant_access_token/internal",
            json={"app_id": self.app_id, "app_secret": self.app_secret},
        )
        data = resp.json()
        if data.get("code") != 0:
            raise Exception(f"Failed to get tenant_access_token: {data.get('msg', '')}")
        self._tenant_token = data["tenant_access_token"]
        self._token_expire_at = time.time() + data.get("expire", 7200)
        return self._tenant_token

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | list[Any] | None = None,
    ) -> dict[str, Any]:
        token = self._ensure_token()
        max_retries = 3
        for attempt in range(max_retries):
            url = f"{self.base_url}{path}"
            resp = self._http.request(
                method,
                url,
                headers={"Authorization": f"Bearer {token}"},
                params=params,
                json=json_data,
            )
            data = resp.json()
            code = data.get("code", -1)
            if code == 90217:
                time.sleep(1.5 * (attempt + 1))
                continue
            if code != 0:
                msg = data.get("msg", "")
                raise Exception(f"[{method} {path}] Failed(code={code}): {msg}")
            return data.get("data", {})
        raise Exception(f"[{method} {path}] Failed after {max_retries} retries: too many requests")

    def search_records(
        self,
        app_token: str,
        table_id: str,
        *,
        view_id: str | None = None,
        field_names: list[str] | None = None,
        sort: dict[str, Any] | None = None,
        filter: dict[str, Any] | None = None,
        page_token: str | None = None,
        page_size: int | None = None,
        automatic_fields: bool | None = None,
        user_id_type: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if user_id_type:
            params["user_id_type"] = user_id_type
        if page_token:
            params["page_token"] = page_token
        if page_size is not None:
            params["page_size"] = page_size

        body: dict[str, Any] = {}
        if view_id:
            body["view_id"] = view_id
        if field_names:
            body["field_names"] = field_names
        if sort:
            body["sort"] = sort
        if filter:
            body["filter"] = filter
        if automatic_fields is True or automatic_fields == "true":
            body["automatic_fields"] = True

        data = self._request(
            "POST",
            f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/search",
            params=params or None,
            json_data=body,
        )
        return {
            "items": data.get("items", []),
            "has_more": data.get("has_more", False),
            "page_token": data.get("page_token", ""),
            "total": data.get("total", 0),
        }

    def close(self) -> None:
        self._http.close()


_shared_client: LarkClient | None = None


def get_client(credentials: dict[str, Any]) -> LarkClient:
    global _shared_client
    if _shared_client is None:
        _shared_client = LarkClient(
            credentials["lark_app_id"],
            credentials["lark_app_secret"],
            credentials.get("lark_base_url", "https://open.feishu.cn"),
        )
    return _shared_client
