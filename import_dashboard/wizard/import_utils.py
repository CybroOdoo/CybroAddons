# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
import base64
import csv
import io
import openpyxl


def get_file_content(record, field_name=None):
    """Retrieve raw file content bytes from a BinaryValue, bytes, or base64 string."""
    if field_name:
        file_val = getattr(record, field_name, None)
    else:
        file_val = getattr(record, 'file_upload', getattr(record, 'file', None))
    if not file_val:
        return b''
    if hasattr(file_val, 'content'):
        return file_val.content
    if isinstance(file_val, (bytes, memoryview)):
        return bytes(file_val)
    if isinstance(file_val, str):
        try:
            return base64.b64decode(file_val)
        except Exception:
            return file_val.encode('utf-8')
    return bytes(file_val) if file_val else b''


def read_csv_data(raw_bytes, delimiter=','):
    """Parse raw bytes into a list of row dicts from CSV content."""
    content = raw_bytes.decode("utf-8-sig", errors="replace").replace('\r\r\n', '\r\n')
    data_file = io.StringIO(content, newline='')
    data_file.seek(0)
    return [
        {key.strip() if isinstance(key, str) else key: value for key, value in row.items()}
        for row in csv.DictReader(data_file, delimiter=delimiter)
    ]


def read_xlsx_data(raw_bytes):
    """Parse raw bytes into a list of row dicts from XLSX/XLS content."""
    workbook = openpyxl.load_workbook(io.BytesIO(raw_bytes), data_only=True)
    sheet = workbook.active
    rows = list(sheet.iter_rows(values_only=True))
    headers = [h.strip() if isinstance(h, str) else h for h in rows[0]] if rows else []
    data = []
    for row in rows[1:]:
        if all(c is None or str(c).strip() == '' for c in row):
            continue
        data.append({k: v for k, v in zip(headers, row) if k is not None})
    return data
