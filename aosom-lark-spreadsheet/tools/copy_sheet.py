from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.lark_sheets import get_client


class CopySheetTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        spreadsheet_token = tool_parameters.get("spreadsheet_token", "")
        source_sheet_id = tool_parameters.get("source_sheet_id", "")
        title = tool_parameters.get("title", "")
        if not all([spreadsheet_token, source_sheet_id, title]):
            raise ValueError("spreadsheet_token, source_sheet_id, and title are required")

        client = get_client(self.runtime.credentials)
        sheet_id = client.copy_sheet(spreadsheet_token, source_sheet_id, title)
        yield self.create_json_message({"new_sheet_id": sheet_id, "title": title})
