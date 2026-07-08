from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.lark_sheets import get_client


class GetMetainfoTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        spreadsheet_token = tool_parameters.get("spreadsheet_token", "")
        if not spreadsheet_token:
            raise ValueError("spreadsheet_token is required")

        client = get_client(self.runtime.credentials)
        data = client.get_metainfo(spreadsheet_token)
        yield self.create_json_message(data)
