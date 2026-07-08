from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.lark_sheets import get_client


class ReadRangeTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        spreadsheet_token = tool_parameters.get("spreadsheet_token", "")
        range_str = tool_parameters.get("range_str", "")

        if not spreadsheet_token:
            raise ValueError("spreadsheet_token is required")
        if not range_str:
            raise ValueError("range_str is required")

        client = get_client(self.runtime.credentials)
        data = client.read_range(spreadsheet_token, range_str)
        yield self.create_json_message({"values": data})
