import json
import sys
from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.lark_bitable import get_client


def _ensure_list(val: Any) -> list | None:
    if not val:
        return None
    if isinstance(val, list):
        return val if val else None
    if isinstance(val, str):
        try:
            parsed = json.loads(val)
            return parsed if isinstance(parsed, list) and parsed else None
        except json.JSONDecodeError:
            return None
    return None


class LarkSearchRecordsTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        print(f"[DEBUG] params: {json.dumps(tool_parameters, ensure_ascii=False)}", file=sys.stderr)

        app_token = tool_parameters.get("app_token", "")
        table_id = tool_parameters.get("table_id", "")
        view_id = tool_parameters.get("view_id")
        field_names = _ensure_list(tool_parameters.get("field_names"))
        sort = _ensure_list(tool_parameters.get("sort"))
        filter = tool_parameters.get("filter")
        page_size = tool_parameters.get("page_size")
        page_token = tool_parameters.get("page_token")
        automatic_fields = tool_parameters.get("automatic_fields")
        user_id_type = tool_parameters.get("user_id_type")

        if not app_token:
            raise ValueError("app_token is required")
        if not table_id:
            raise ValueError("table_id is required")

        client = get_client(self.runtime.credentials)
        result = client.search_records(
            app_token,
            table_id,
            view_id=view_id,
            field_names=field_names,
            sort=sort,
            filter=filter,
            page_size=page_size,
            page_token=page_token,
            automatic_fields=automatic_fields,
            user_id_type=user_id_type,
        )
        yield self.create_json_message(result)
