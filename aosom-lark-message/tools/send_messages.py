import json
from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.lark_client import get_client


class SendMessagesTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        receive_ids = tool_parameters.get("receive_ids", [])
        msg_type = tool_parameters.get("msg_type", "text")
        content = tool_parameters.get("content", "")
        receive_id_type = tool_parameters.get("receive_id_type", "open_id")

        if not receive_ids:
            raise ValueError("receive_ids is required")
        if not content:
            raise ValueError("content is required")

        if isinstance(content, dict):
            content = json.dumps(content, ensure_ascii=False)
        else:
            json.loads(content)

        client = get_client(self.runtime.credentials)
        results = client.send_messages(
            receive_ids,
            msg_type,
            content,
            receive_id_type=receive_id_type,
        )
        for r in results:
            yield self.create_json_message(r)
