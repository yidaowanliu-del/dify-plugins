from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.lark_sheets import get_client


class WriteMultipleRangeTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        spreadsheet_token = tool_parameters.get("spreadsheet_token", "")
        value_ranges = tool_parameters.get("value_ranges", [])
        if not spreadsheet_token:
            raise ValueError("spreadsheet_token is required")
        if not value_ranges:
            raise ValueError("value_ranges is required")
        client = get_client(self.runtime.credentials)
        result = client.write_multiple_range(spreadsheet_token, value_ranges)
        yield self.create_json_message(result)
