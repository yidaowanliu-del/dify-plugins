from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.lark_sheets import get_client


class BatchUpdateTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        spreadsheet_token = tool_parameters.get("spreadsheet_token", "")
        sheet_id = tool_parameters.get("sheet_id", "")
        update_data = tool_parameters.get("update_data", [])
        columns = tool_parameters.get("columns")

        if not all([spreadsheet_token, sheet_id, update_data]):
            raise ValueError("spreadsheet_token, sheet_id, and update_data are required")

        client = get_client(self.runtime.credentials)
        client.quick_sheets_batch_update(
            spreadsheet_token, sheet_id, 
            update_data, 
            columns=columns, 
            data_start=int(tool_parameters.get("data_start", 2))
        )
        yield self.create_json_message({"status": "ok", "updated": len(update_data)})
