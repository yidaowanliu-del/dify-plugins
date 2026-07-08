from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.lark_sheets import get_client


class ClearSheetContentTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        spreadsheet_token = tool_parameters.get("spreadsheet_token", "")
        sheet_id = tool_parameters.get("sheet_id", "")
        keep_header = tool_parameters.get("keep_header", True)
        before_column = tool_parameters.get("before_column")
        if not all([spreadsheet_token, sheet_id]):
            raise ValueError("spreadsheet_token and sheet_id are required")
        client = get_client(self.runtime.credentials)
        result = client.quick_sheets_clear_sheet_content(
            spreadsheet_token, sheet_id, 
            keep_header=keep_header, 
            data_start=int(tool_parameters.get("data_start", 2)), 
            before_column=before_column
        )
        yield self.create_json_message(result)
