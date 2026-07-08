import time
from itertools import groupby
from typing import Any

import httpx


class LarkClient:
    def __init__(self, app_id: str, app_secret: str, base_url: str) -> None:
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_url = base_url.rstrip("/")
        self._http = httpx.Client(timeout=30)
        self._tenant_token = ""
        self._token_expire_at = 0.0

    def _ensure_token(self) -> str:
        if self._tenant_token and time.time() < self._token_expire_at - 60:
            return self._tenant_token
        resp = self._http.post(
            f"{self.base_url}/open-apis/auth/v3/tenant_access_token/internal",
            json={"app_id": self.app_id, "app_secret": self.app_secret},
        )
        data = resp.json()
        if data.get("code") != 0:
            raise Exception(f"Failed to get tenant_access_token: {data.get('msg', '')}")
        self._tenant_token = data["tenant_access_token"]
        self._token_expire_at = time.time() + data.get("expire", 7200)
        return self._tenant_token

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | list[Any] | None = None,
    ) -> dict[str, Any]:
        token = self._ensure_token()
        max_retries = 3
        for attempt in range(max_retries):
            url = f"{self.base_url}{path}"
            resp = self._http.request(
                method,
                url,
                headers={"Authorization": f"Bearer {token}"},
                params=params,
                json=json_data,
            )
            data = resp.json()
            code = data.get("code", -1)
            if code == 90217:
                time.sleep(1.5 * (attempt + 1))
                continue
            if code != 0:
                msg = data.get("msg", "")
                raise Exception(f"[{method} {path}] Failed(code={code}): {msg}")
            return data.get("data", {})
        raise Exception(f"[{method} {path}] Failed after {max_retries} retries: too many requests")

    def _get(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._request("GET", path, params=params)

    def _post(self, path: str, *, json_data: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._request("POST", path, json_data=json_data)

    def _put(self, path: str, *, json_data: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._request("PUT", path, json_data=json_data)

    @staticmethod
    def _index_to_letter(index: int) -> str:
        result = ""
        while True:
            result = chr(ord("A") + index % 26) + result
            index = index // 26 - 1
            if index < 0:
                break
        return result

    # ── Sheet metadata ──

    def get_metainfo(self, spreadsheet_token: str) -> dict[str, Any]:
        return self._get(
            f"/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/metainfo",
            params={"ext_fields": "protectedRange"},
        )

    def add_sheet(self, spreadsheet_token: str, title: str) -> str:
        data = self._post(
            f"/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/sheets_batch_update",
            json_data={"requests": [{"addSheet": {"properties": {"title": title}}}]},
        )
        replies = data.get("replies", [])
        if not replies:
            raise Exception(f"创建工作表 {title} 失败：无返回")
        sheet_id = replies[0].get("addSheet", {}).get("properties", {}).get("sheetId")
        if not sheet_id:
            raise Exception(f"创建工作表 {title} 失败：缺少 sheetId")
        return str(sheet_id)

    def delete_sheet(self, spreadsheet_token: str, sheet_id: str) -> None:
        self._post(
            f"/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/sheets_batch_update",
            json_data={"requests": [{"deleteSheet": {"sheetId": sheet_id}}]},
        )

    def copy_sheet(self, spreadsheet_token: str, source_sheet_id: str, title: str) -> str:
        data = self._post(
            f"/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/sheets_batch_update",
            json_data={
                "requests": [
                    {
                        "copySheet": {
                            "source": {"sheetId": source_sheet_id},
                            "destination": {"title": title},
                        }
                    }
                ]
            },
        )
        replies = data.get("replies", [])
        if not replies:
            raise Exception(f"复制工作表 {title} 失败：无返回")
        sheet_id = replies[0].get("copySheet", {}).get("properties", {}).get("sheetId")
        if not sheet_id:
            raise Exception(f"复制工作表 {title} 失败：缺少 sheetId")
        return str(sheet_id)

    def delete_dimension(
        self,
        spreadsheet_token: str,
        sheet_id: str,
        *,
        major_dimension: str = "COLUMNS",
        start_index: int,
        end_index: int,
    ) -> None:
        self._request(
            "DELETE",
            f"/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/dimension_range",
            json_data={
                "dimension": {
                    "sheetId": sheet_id,
                    "majorDimension": major_dimension,
                    "startIndex": start_index,
                    "endIndex": end_index,
                },
            },
        )

    # ── Data operations ──

    def read_range(self, spreadsheet_token: str, range_str: str) -> list[list[Any]]:
        data = self._get(
            f"/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values/{range_str}",
        )
        return data.get("valueRange", {}).get("values", [])

    def write_range(
        self, spreadsheet_token: str, range_str: str, values: list[list[Any]]
    ) -> dict[str, Any]:
        return self._put(
            f"/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values",
            json_data={"valueRange": {"range": range_str, "values": values}},
        )

    def write_multiple_range(self, spreadsheet_token: str, value_ranges: list[dict[str, Any]]) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values_batch_update",
            json_data={"valueRanges": value_ranges},
        )

    def append_data(
        self,
        spreadsheet_token: str,
        sheet_id: str,
        values: list[list[Any]],
        *,
        data_start: int = 2,
    ) -> None:
        col_count = len(values[0]) if values else 1
        end_col = self._index_to_letter(col_count - 1)
        self._request(
            "POST",
            f"/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values_append",
            params={"insertDataOption": "OVERWRITE"},
            json_data={
                "valueRange": {
                    "range": f"{sheet_id}!A{data_start}:{end_col}",
                    "values": values,
                }
            },
        )

    # ── Sheet lookups ──

    def get_sheet_id(self, spreadsheet_token: str, sheet_title: str) -> str:
        meta = self.get_metainfo(spreadsheet_token)
        for s in meta.get("sheets", []):
            if s.get("title") == sheet_title:
                return str(s.get("sheetId", ""))
        raise Exception(f"未找到工作表 '{sheet_title}'")

    def find_sheet_ids(self, spreadsheet_token: str, *titles: str) -> dict[str, str]:
        meta = self.get_metainfo(spreadsheet_token)
        result = {t: "" for t in titles}
        for s in meta.get("sheets", []):
            t = s.get("title", "")
            if t in result:
                result[t] = str(s.get("sheetId", ""))
        return result

    def find_sheet_id(self, spreadsheet_token: str, title: str) -> str:
        try:
            return self.get_sheet_id(spreadsheet_token, title)
        except Exception:
            return ""

    def _get_sheet_dimensions(self, spreadsheet_token: str, sheet_id: str) -> tuple[int, str]:
        meta = self.get_metainfo(spreadsheet_token)
        for s in meta.get("sheets", []):
            if str(s.get("sheetId", "")) == sheet_id:
                col_count = s.get("columnCount", 0)
                if col_count > 0:
                    return col_count, self._index_to_letter(col_count - 1)
        return 0, ""

    def _resolve_column_letter(self, spreadsheet_token: str, sheet_id: str, column_name: str, *, data_start: int = 2) -> str:
        header_row = data_start - 1
        col_count, end_col = self._get_sheet_dimensions(spreadsheet_token, sheet_id)
        if col_count <= 0:
            raise Exception(f"无法获取工作表 {sheet_id} 的列数")
        rng = f"{sheet_id}!A{header_row}:{end_col}{header_row}"
        headers = self.read_range(spreadsheet_token, rng)
        if not headers:
            raise Exception(f"无法读取表头：{sheet_id}")
        for i, h in enumerate(headers[0]):
            if h == column_name:
                return self._index_to_letter(i)
        raise Exception(f"在表头中未找到列 '{column_name}'")

    def _ensure_column(self, spreadsheet_token: str, sheet_id: str, column_name: str, *, data_start: int = 2) -> str:
        header_row = data_start - 1
        try:
            return self._resolve_column_letter(spreadsheet_token, sheet_id, column_name, data_start=data_start)
        except Exception:
            col_count, end_col = self._get_sheet_dimensions(spreadsheet_token, sheet_id)
            if col_count > 0:
                headers = self.read_range(spreadsheet_token, f"{sheet_id}!A{header_row}:{end_col}{header_row}")
                existing = headers[0] if headers else []
                while existing and existing[-1] in (None, ""):
                    existing.pop()
                col_letter = self._index_to_letter(len(existing))
            else:
                col_letter = self._index_to_letter(0)
            self.write_range(spreadsheet_token, f"{sheet_id}!{col_letter}{header_row}:{col_letter}{header_row}", [[column_name]])
            return col_letter

    def quick_sheets_set_header_list(self, spreadsheet_token: str, sheet_id: str, header_list: list[str], *, keep_columns: int | None = None, data_start: int = 2) -> None:
        header_row = data_start - 1
        start_col = keep_columns if keep_columns is not None else 0
        start_letter = self._index_to_letter(start_col)
        end_letter = self._index_to_letter(start_col + len(header_list) - 1)
        self.write_range(spreadsheet_token, f"{sheet_id}!{start_letter}{header_row}:{end_letter}{header_row}", [header_list])

    def quick_sheets_set_batch_index(self, spreadsheet_token: str, sheet_id: str, *, batch_column: str = "f_batch_index", batch_size: int = 10, data_start: int = 2) -> None:
        col_letter = self._ensure_column(spreadsheet_token, sheet_id, batch_column, data_start=data_start)
        data = self.read_range(spreadsheet_token, f"{sheet_id}!A:A")
        rows_to_write: list[tuple[int, int]] = []
        batch_num = 1
        row_count = 0
        for i in range(data_start - 1, len(data)):
            val = str(data[i][0]) if i < len(data) and data[i] else ""
            if val.strip():
                rows_to_write.append((i + 1, batch_num))
                row_count += 1
                if row_count >= batch_size:
                    batch_num += 1
                    row_count = 0
        if not rows_to_write:
            return
        value_ranges: list[dict[str, Any]] = []
        for batch_val, group in groupby(rows_to_write, key=lambda x: x[1]):
            group_list = list(group)
            rng = f"{sheet_id}!{col_letter}{group_list[0][0]}:{col_letter}{group_list[-1][0]}"
            vals = [[str(batch_val)] for _ in group_list]
            value_ranges.append({"range": rng, "values": vals})
        self.write_multiple_range(spreadsheet_token, value_ranges)

    def quick_sheets_get_rows_by_batch(self, spreadsheet_token: str, sheet_id: str, batch_id: int, batch_size: int, *, data_start: int = 2) -> list[dict[str, Any]]:
        header_row = data_start - 1
        col_count, end_col = self._get_sheet_dimensions(spreadsheet_token, sheet_id)
        if col_count <= 0:
            return []
        rng = f"{sheet_id}!A{header_row}:{end_col}{header_row}"
        headers_raw = self.read_range(spreadsheet_token, rng)
        if not headers_raw:
            return []
        headers = headers_raw[0]
        start_row = data_start + (batch_id - 1) * batch_size
        end_row = start_row + batch_size - 1
        all_data = self.read_range(spreadsheet_token, f"{sheet_id}!A{start_row}:{end_col}{end_row}")
        result: list[dict[str, Any]] = []
        for row_offset, row in enumerate(all_data):
            row_dict: dict[str, Any] = {}
            for col_idx, header in enumerate(headers):
                val = row[col_idx] if col_idx < len(row) else ""
                row_dict[header] = val
            row_dict["row_number"] = start_row + row_offset
            result.append(row_dict)
        return result

    # ── Quick/batch operations ──

    def quick_sheets_filter_columns(self, spreadsheet_token: str, sheet_id: str, keep_columns: list[str], *, data_start: int = 2) -> str:
        header_row = data_start - 1
        col_count, end_col = self._get_sheet_dimensions(spreadsheet_token, sheet_id)
        if col_count <= 0:
            return sheet_id
        rng = f"{sheet_id}!A{header_row}:{end_col}{header_row}"
        headers = self.read_range(spreadsheet_token, rng)
        if not headers:
            return sheet_id
        raw_headers = headers[0]
        keep = set()
        for col in keep_columns:
            if col in raw_headers:
                keep.add(raw_headers.index(col))
        if not keep:
            return sheet_id
        drop = sorted(i for i in range(col_count) if i not in keep)
        if not drop:
            return sheet_id
        groups: list[tuple[int, int]] = []
        for _, g in groupby(enumerate(drop), lambda x: x[1] - x[0]):
            glist = list(g)
            groups.append((glist[0][1] + 1, glist[-1][1] + 1))
        for s, e in reversed(groups):
            self.delete_dimension(spreadsheet_token, sheet_id, major_dimension="COLUMNS", start_index=s, end_index=e)
        return sheet_id

    def quick_sheets_get_last_value(self, spreadsheet_token: str, sheet_id: str, column_name: str, *, data_start: int = 2) -> dict[str, Any]:
        col_letter = self._resolve_column_letter(spreadsheet_token, sheet_id, column_name, data_start=data_start)
        data = self.read_range(spreadsheet_token, f"{sheet_id}!{col_letter}:{col_letter}")
        for i in range(len(data) - 1, data_start - 2, -1):
            row = data[i]
            if row and row[0] is not None and row[0] != "":
                return {"value": row[0], "row_number": i + 1}
        return {"value": None, "row_number": 0}

    def quick_sheets_batch_update(self, spreadsheet_token: str, sheet_id: str, update_data: list[dict[str, Any]], columns: list[str] | None = None, *, data_start: int = 2) -> None:
        if not update_data:
            return
        if columns is None:
            columns = [k for k in update_data[0] if k != "row_number"]
        header_row = data_start - 1
        _col_count, _end_col = self._get_sheet_dimensions(spreadsheet_token, sheet_id)
        if _col_count <= 0:
            return
        headers = self.read_range(spreadsheet_token, f"{sheet_id}!A{header_row}:{_end_col}{header_row}")[0]
        col_indices = {h: i for i, h in enumerate(headers) if h is not None}
        value_ranges: list[dict[str, Any]] = []
        for row in update_data:
            row_number = row.get("row_number")
            if not row_number:
                continue
            try:
                row_number = int(row_number)
            except (ValueError, TypeError):
                continue
            cell_updates: list[tuple[str, Any]] = []
            for col_name in columns:
                if col_name not in col_indices or col_name not in row:
                    continue
                col_letter = self._index_to_letter(col_indices[col_name])
                cell_updates.append((col_letter, row[col_name]))
            if not cell_updates:
                continue
            start_letter = cell_updates[0][0]
            end_letter = cell_updates[-1][0]
            range_str = f"{sheet_id}!{start_letter}{row_number}:{end_letter}{row_number}"
            value_ranges.append({"range": range_str, "values": [[v for _, v in cell_updates]]})
        if value_ranges:
            self.write_multiple_range(spreadsheet_token, value_ranges)

    def quick_sheets_batch_append(self, spreadsheet_token: str, sheet_id: str, data: list[dict[str, Any]], *, batch_size: int = 500, batch_interval: int = 2, data_start: int = 2, overwrite_start: int | bool | None = None) -> None:
        if not data:
            return
        headers = list(data[0].keys())
        values: list[list[str]] = [[str(row.get(h, "")) for h in headers] for row in data]
        if overwrite_start is not None:
            start_row = data_start if overwrite_start is True else overwrite_start
            col_count = len(headers)
            end_col = self._index_to_letter(col_count - 1)
            for i in range(0, len(values), batch_size):
                chunk = values[i:i + batch_size]
                row_start = start_row + i
                row_end = row_start + len(chunk) - 1
                self.write_range(spreadsheet_token, f"{sheet_id}!A{row_start}:{end_col}{row_end}", chunk)
                if i + batch_size < len(values) and batch_interval > 0:
                    time.sleep(batch_interval)
        else:
            for i in range(0, len(values), batch_size):
                chunk = values[i:i + batch_size]
                self.append_data(spreadsheet_token, sheet_id, chunk, data_start=data_start)
                if i + batch_size < len(values) and batch_interval > 0:
                    time.sleep(batch_interval)

    def quick_sheets_clear_sheet(self, spreadsheet_token: str, sheet_id: str, *, keep_header: bool = True, data_start: int = 2) -> None:
        meta = self.get_metainfo(spreadsheet_token)
        row_count = 0
        for s in meta.get("sheets", []):
            if str(s.get("sheetId", "")) == sheet_id:
                row_count = s.get("rowCount", 0)
                break
        start = data_start if keep_header else 1
        if start > row_count:
            return
        chunk_size = 5000
        for end in range(row_count, start - 1, -chunk_size):
            chunk_start = max(start, end - chunk_size + 1)
            self.delete_dimension(spreadsheet_token, sheet_id, major_dimension="ROWS", start_index=chunk_start, end_index=end)

    def quick_sheets_clear_sheet_content(self, spreadsheet_token: str, sheet_id: str, *, keep_header: bool = True, data_start: int = 2, before_column: str | None = None) -> dict[str, Any]:
        meta = self.get_metainfo(spreadsheet_token)
        row_count = 0
        for s in meta.get("sheets", []):
            if str(s.get("sheetId", "")) == sheet_id:
                row_count = s.get("rowCount", 0)
                break
        start = data_start if keep_header else 1
        if start > row_count:
            return {"col_count": 0, "row_count": 0, "start_row": start}
        if before_column:
            upper = before_column.upper().strip()
            before_idx = 0
            for ch in upper:
                before_idx = before_idx * 26 + (ord(ch) - ord("A") + 1)
            if before_idx <= 1:
                return {"col_count": 0, "row_count": 0, "start_row": start}
            clear_count = before_idx - 1
            end_col = self._index_to_letter(clear_count - 1)
            empty_row = [""] * clear_count
        else:
            meta2 = self.get_metainfo(spreadsheet_token)
            col_count = 0
            for s in meta2.get("sheets", []):
                if str(s.get("sheetId", "")) == sheet_id:
                    col_count = s.get("columnCount", 0)
                    break
            if col_count <= 0:
                return {"col_count": 0, "row_count": 0, "start_row": start}
            end_col = self._index_to_letter(col_count - 1)
            empty_row = [""] * col_count
        chunk_size = 5000
        for batch_start in range(start, row_count + 1, chunk_size):
            batch_end = min(batch_start + chunk_size - 1, row_count)
            values = [empty_row] * (batch_end - batch_start + 1)
            range_str = f"{sheet_id}!A{batch_start}:{end_col}{batch_end}"
            self.write_range(spreadsheet_token, range_str, values)
        return {"col_count": len(empty_row), "row_count": row_count - start + 1, "start_row": start}

    def close(self) -> None:
        self._http.close()


_shared_client: LarkClient | None = None


def get_client(credentials: dict[str, Any]) -> LarkClient:
    global _shared_client
    if _shared_client is None:
        _shared_client = LarkClient(
            credentials["lark_app_id"],
            credentials["lark_app_secret"],
            credentials.get("lark_base_url", "https://open.feishu.cn"),
        )
    return _shared_client
