import time
from typing import Any

import httpx


class LarkClient:
    """Synchronous Lark/Feishu API client."""

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

    def send_message(
        self,
        receive_id: str,
        msg_type: str,
        content: str,
        *,
        receive_id_type: str = "open_id",
        uuid: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "receive_id": receive_id,
            "msg_type": msg_type,
            "content": content,
        }
        if uuid is not None:
            body["uuid"] = uuid
        return self._request(
            "POST",
            "/open-apis/im/v1/messages",
            params={"receive_id_type": receive_id_type},
            json_data=body,
        )

    def send_messages(
        self,
        receive_ids: list[str],
        msg_type: str,
        content: str,
        *,
        receive_id_type: str = "open_id",
        uuid: str | None = None,
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for uid in receive_ids:
            try:
                data = self.send_message(
                    uid, msg_type, content, receive_id_type=receive_id_type, uuid=uuid
                )
                results.append({"receive_id": uid, "message_id": data.get("message_id", "")})
            except Exception as e:
                results.append({"receive_id": uid, "message_id": "", "error": str(e)})
        return results
    
    def _send_examples(self, _receive_id: str = "ou_45d3cc5b79714d1d48fd2787e4288d5a") -> None:
        """各种消息类型的发送示例（逐条取消注释运行）"""
        # ✅self.send_message(_receive_id, "text", '{"text":"hello world"}')
        # ✅self.send_message(_receive_id, "post", '{"zh_cn":{"title":"标题","content":[[{"tag":"text","text":"hello"}]]}}')
        # ✅self.send_message(_receive_id, "image", '{"image_key":"img_7ea74629-9191-4176-998c-2e603c9c5e8g"}')
        # ✅self.send_message(_receive_id, "interactive", '{"elements":[{"tag":"markdown","content":"**hello**"}],"header":{"title":{"tag":"plain_text","content":"Card Title"}}}')

    def close(self) -> None:
        self._http.close()


def build_client(credentials: dict[str, Any]) -> LarkClient:
    return LarkClient(
        credentials["lark_app_id"],
        credentials["lark_app_secret"],
        credentials.get("lark_base_url", "https://open.feishu.cn"),
    )




