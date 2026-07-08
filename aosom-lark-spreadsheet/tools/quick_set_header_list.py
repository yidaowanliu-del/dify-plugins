from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.lark_sheets import get_client


class SetHeaderListTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        spreadsheet_token = tool_parameters.get("spreadsheet_token", "")
        sheet_id = tool_parameters.get("sheet_id", "")
        header_list = tool_parameters.get("header_list", [])
        if not all([spreadsheet_token, sheet_id, header_list]):
            raise ValueError("spreadsheet_token, sheet_id, and header_list are required")

        client = get_client(self.runtime.credentials)
        client.quick_sheets_set_header_list(
            spreadsheet_token, sheet_id, header_list,
            keep_columns=tool_parameters.get("keep_columns"),
            data_start=int(tool_parameters.get("data_start", 2)),
        )
        yield self.create_json_message({"status": "ok", "headers": len(header_list)})
