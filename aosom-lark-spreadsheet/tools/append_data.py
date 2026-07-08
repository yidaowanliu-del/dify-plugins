from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.lark_sheets import get_client


class AppendDataTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        spreadsheet_token = tool_parameters.get("spreadsheet_token", "")
        sheet_id = tool_parameters.get("sheet_id", "")
        values = tool_parameters.get("values", [])

        if not spreadsheet_token:
            raise ValueError("spreadsheet_token is required")
        if not sheet_id:
            raise ValueError("sheet_id is required")
        if not values:
            raise ValueError("values is required")

        client = get_client(self.runtime.credentials)
        client.append_data(spreadsheet_token, sheet_id, values, data_start=int(tool_parameters.get("data_start", 2)))
        yield self.create_json_message({"status": "ok", "rows": len(values)})
