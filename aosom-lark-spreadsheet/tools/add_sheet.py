from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.lark_sheets import get_client


class AddSheetTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        spreadsheet_token = tool_parameters.get("spreadsheet_token", "")
        title = tool_parameters.get("title", "")
        if not spreadsheet_token:
            raise ValueError("spreadsheet_token is required")
        if not title:
            raise ValueError("title is required")

        client = get_client(self.runtime.credentials)
        sheet_id = client.add_sheet(spreadsheet_token, title)
        yield self.create_json_message({"sheet_id": sheet_id, "title": title})
