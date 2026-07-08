from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.lark_sheets import get_client


class FilterColumnsTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        spreadsheet_token = tool_parameters.get("spreadsheet_token", "")
        sheet_id = tool_parameters.get("sheet_id", "")
        keep_columns = tool_parameters.get("keep_columns", [])
        if not all([spreadsheet_token, sheet_id, keep_columns]):
            raise ValueError("spreadsheet_token, sheet_id, and keep_columns are required")
        client = get_client(self.runtime.credentials)
        client.quick_sheets_filter_columns(
            spreadsheet_token, sheet_id, 
            keep_columns, 
            data_start=int(tool_parameters.get("data_start", 2))
        )
        yield self.create_json_message({"status": "ok", "kept": len(keep_columns)})
