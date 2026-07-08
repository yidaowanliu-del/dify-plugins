from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.lark_sheets import get_client


class GetColumnLastValueTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        spreadsheet_token = tool_parameters.get("spreadsheet_token", "")
        sheet_id = tool_parameters.get("sheet_id", "")
        column_name = tool_parameters.get("column_name", "")
        if not all([spreadsheet_token, sheet_id, column_name]):
            raise ValueError("spreadsheet_token, sheet_id, and column_name are required")

        client = get_client(self.runtime.credentials)
        result = client.quick_sheets_get_last_value(
            spreadsheet_token, sheet_id, 
            column_name, 
            data_start=int(tool_parameters.get("data_start", 2))
        )
        yield self.create_json_message(result)
