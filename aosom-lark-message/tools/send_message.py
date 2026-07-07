import json
from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.lark_client import build_client


class SendMessageTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        receive_id = tool_parameters.get("receive_id", "")
        msg_type = tool_parameters.get("msg_type", "text")
        content = tool_parameters.get("content", "")
        receive_id_type = tool_parameters.get("receive_id_type", "open_id")
        uuid = tool_parameters.get("uuid")

        if not receive_id:
            raise ValueError("receive_id is required")
        if not content:
            raise ValueError("content is required")

        if isinstance(content, dict):
            content = json.dumps(content, ensure_ascii=False)
        else:
            json.loads(content)

        client = build_client(self.runtime.credentials)
        try:
            result = client.send_message(
                receive_id,
                msg_type,
                content,
                receive_id_type=receive_id_type,
                uuid=uuid,
            )
            yield self.create_json_message(
                {
                    "message_id": result.get("message_id", ""),
                    "receive_id": receive_id,
                    "msg_type": msg_type,
                }
            )
        except Exception as e:
            raise Exception(f"Failed to send message: {e}")
        finally:
            client.close()
