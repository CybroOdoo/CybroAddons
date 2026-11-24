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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
"""export_x2many — Excel Export Controller.

Extends the standard Odoo Excel export to support:
  - Multisheet workbooks: data can be split across named sheets, each filtered
    by a user-defined domain.
  - X2Many child-field selection: handled on the JS side; the controller
    receives and processes the resulting flat field list transparently.

Routes:
    POST /web/export/xlsx_multisheet  — multisheet XLSX download
"""

import io
import json
import logging
import operator
from ast import literal_eval

import xlsxwriter
from werkzeug.exceptions import InternalServerError

from odoo import http
from odoo.http import content_disposition, request
from odoo.tools import osutil

from odoo.addons.web.controllers.export import ExcelExport, ExportXlsxWriter

_logger = logging.getLogger(__name__)


SHEET_NAME_TRANS = str.maketrans({c: '_' for c in '[]:*?/\\'})


class MultiSheetExcelExport(ExcelExport):
    """Inherit ExcelExport to write a multisheet workbook with
    xlsxwriter."""

    @staticmethod
    def _sanitize_sheet_name(name, existing_names):
        """Sanitize a worksheet name for Excel, and make it unique.

        Excel restricts sheet names to:
          - Maximum 31 characters.
          - Prohibited characters: [ ] : * ? / \\
          - Cannot be blank or empty.
          - Must be unique within the workbook.
        """
        clean_name = (name or "").translate(SHEET_NAME_TRANS).strip()
        if not clean_name:
            clean_name = "Sheet"
        clean_name = clean_name[:31]

        if clean_name not in existing_names:
            existing_names.add(clean_name)
            return clean_name

        i = 1
        while True:
            suffix = f"_{i}"
            candidate = f"{clean_name[:31 - len(suffix)]}{suffix}"
            if candidate not in existing_names:
                existing_names.add(candidate)
                return candidate
            i += 1

    @http.route(
        "/web/export/xlsx_multisheet",
        type="http",
        auth="user",
    )
    def web_export_xlsx_multisheet(self, data, token=None):
        """Fetch export data and delegate to multisheet or standard export.

        If no ``sheet_list`` is present in the request params the standard
        parent export is used, preserving full backwards-compatibility.
        """
        try:
            params = json.loads(data)
            model, fields, ids, domain, import_compat = operator.itemgetter(
                "model",
                "fields",
                "ids",
                "domain",
                "import_compat",
            )(params)

            sheet_list = params.get("sheet_list")

            if not sheet_list:
                return super().base(data)

            Model = request.env[model].with_context(
                import_compat=import_compat,
                **params.get("context", {}),
            )

            records = Model.browse(ids) if ids else Model.search(domain)

            field_names = [f["name"] for f in fields]
            columns_headers = (
                field_names
                if import_compat
                else [f["label"].strip() for f in fields]
            )

            response = self.from_multisheet_data(
                Model,
                records,
                field_names,
                fields,
                columns_headers,
                sheet_list,
            )

            return request.make_response(
                response,
                headers=[
                    (
                        "Content-Disposition",
                        content_disposition(
                            osutil.clean_filename(
                                self.filename(model) + self.extension,
                            ),
                        ),
                    ),
                    ("Content-Type", self.content_type),
                ],
            )
        except Exception as exc:
            _logger.exception(
                "Exception during multisheet export request handling.")
            payload = json.dumps({
                "code": 0,
                "message": "Odoo Server Error",
                "data": http.serialize_exception(exc),
            })
            raise InternalServerError(payload) from exc

    def from_multisheet_data(
            self, Model, records, field_names, fields, headers, sheet_list,
    ):
        """Write export data into a multi-sheet XLSX workbook and return bytes.

        Each entry in ``sheet_list`` defines one worksheet:
            - ``name``   (str): worksheet tab label (sanitized and
            truncated to 31 chars).
            - ``domain`` (list|str): Odoo domain expression to filter records.
        """
        sheet_groups = []
        used_names = set()

        for sheet in sheet_list:
            raw_name = sheet.get("name") or "Sheet"
            clean_name = self._sanitize_sheet_name(raw_name, used_names)
            sheet_domain = sheet.get("domain", [])
            if isinstance(sheet_domain, str):
                sheet_domain = literal_eval(sheet_domain)

            filtered_records = records.filtered_domain(sheet_domain)
            sheet_groups.append((clean_name, filtered_records.ids))

        writer = MultiSheetExportXlsxWriter(fields, headers, env=request.env)

        for sheet_name, ids in sheet_groups:
            worksheet = writer.workbook.add_worksheet(sheet_name)
            writer.set_worksheet(worksheet)
            writer.write_header()

            rows = Model.browse(ids).export_data(field_names)["datas"]

            for r, row in enumerate(rows, start=1):
                for c, value in enumerate(row):
                    writer.write_cell(r, c, value)

        writer.close()
        return writer.value


class MultiSheetExportXlsxWriter(ExportXlsxWriter):
    """Extends ExportXlsxWriter to support multi-sheet workbooks.

    The base class always creates an initial worksheet in ``__init__``.
    This subclass overrides the constructor to skip that step, allowing
    ``MultiSheetExcelExport`` to create and manage sheets explicitly.
    """

    def __init__(self, fields, headers, env=None):
        """Initialise the workbook without creating an initial worksheet."""
        self.fields = fields
        self.columns_headers = headers
        self.output = io.BytesIO()
        self.workbook = xlsxwriter.Workbook(self.output, {'in_memory': True})
        self.header_style = self.workbook.add_format({'bold': True})
        self.date_style = self.workbook.add_format(
            {'text_wrap': True, 'num_format': 'yyyy-mm-dd'})
        self.datetime_style = self.workbook.add_format(
            {'text_wrap': True, 'num_format': 'yyyy-mm-dd hh:mm:ss'})
        self.base_style = self.workbook.add_format({'text_wrap': True})
        self.float_style = self.workbook.add_format(
            {'text_wrap': True, 'num_format': '#,##0.00'})
        decimal_places = 2
        try:
            target_env = env
            if not target_env:
                try:
                    if request and hasattr(request, 'env') and request.env:
                        target_env = request.env
                except RuntimeError:
                    target_env = None
            if target_env:
                decimal_places = target_env['res.currency']._read_group(
                    [],
                    aggregates=['decimal_places:max'],
                )[0][0] or 2
        except (AttributeError, KeyError, ValueError, RuntimeError, TypeError):
            decimal_places = 2
        self.monetary_style = self.workbook.add_format({
            'text_wrap': True,
            'num_format': f'#,##0.{(decimal_places or 2) * "0"}',
        })

        header_bold_props = {
            'text_wrap': True,
            'bold': True,
            'bg_color': '#e9ecef',
        }
        self.header_bold_style = self.workbook.add_format(header_bold_props)
        self.header_bold_style_float = self.workbook.add_format(
            dict(**header_bold_props, num_format='#,##0.00'))
        self.header_bold_style_monetary = self.workbook.add_format(
            dict(**header_bold_props,
                 num_format=f'#,##0.{(decimal_places or 2) * "0"}'))
        self.value = False

    def set_worksheet(self, worksheet):
        """Set the active worksheet for subsequent write operations."""
        self.worksheet = worksheet
