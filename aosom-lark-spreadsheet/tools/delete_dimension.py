from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.lark_sheets import get_client


class DeleteDimensionTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        spreadsheet_token = tool_parameters.get("spreadsheet_token", "")
        sheet_id = tool_parameters.get("sheet_id", "")
        major_dimension = tool_parameters.get("major_dimension", "COLUMNS")
        start_index = tool_parameters.get("start_index")
        end_index = tool_parameters.get("end_index")

        if not spreadsheet_token:
            raise ValueError("spreadsheet_token is required")
        if not sheet_id:
            raise ValueError("sheet_id is required")
        if start_index is None or end_index is None:
            raise ValueError("start_index and end_index are required")

        client = get_client(self.runtime.credentials)
        client.delete_dimension(
            spreadsheet_token, sheet_id,
            major_dimension=major_dimension,
            start_index=int(start_index),
            end_index=int(end_index),
        )
        yield self.create_json_message({"status": "ok"})
