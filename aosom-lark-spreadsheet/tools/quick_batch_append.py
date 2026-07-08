from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.lark_sheets import get_client


class BatchAppendTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        spreadsheet_token = tool_parameters.get("spreadsheet_token", "")
        sheet_id = tool_parameters.get("sheet_id", "")
        data = tool_parameters.get("data", [])
        if not all([spreadsheet_token, sheet_id, data]):
            raise ValueError("spreadsheet_token, sheet_id, and data are required")

        client = get_client(self.runtime.credentials)
        client.quick_sheets_batch_append(
            spreadsheet_token, sheet_id, data,
            batch_size=int(tool_parameters.get("batch_size", 500)),
            data_start=int(tool_parameters.get("data_start", 2)),
            overwrite_start=tool_parameters.get("overwrite_start"),
        )
        yield self.create_json_message({"status": "ok", "appended": len(data)})
