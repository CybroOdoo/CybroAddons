# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anshad Ahammed M (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (
#    OPL-1) It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################

import io
import json
import xlsxwriter
from datetime import timedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StockValuationReport(models.TransientModel):
    """Wizard for printing stock valuation report (PDF & XLSX)."""

    _name = "stock.valuation.report"
    _description = "Stock Valuation Report"

    product_id = fields.Many2one(
        "product.product",
        string="Product",
        help="To pick the product",
    )
    product_category_id = fields.Many2one(
        "product.category",
        string="Product Category",
        required=True,
        help="To pick product_category",
    )
    from_Date = fields.Datetime(
        string="From Date",
        required=True,
        default=lambda self: fields.Datetime.now() - timedelta(days=30),
        help="For filtering data using from date",
    )
    to_date = fields.Datetime(
        string="To Date",
        required=True,
        default=fields.Datetime.now,
        help="For filtering data using to date",
    )
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
    )

    @api.constrains("from_Date", "to_date")
    def _check_dates(self):
        """Check if from date is less than or equal to to date."""
        for record in self:
            if record.from_Date and record.to_date and record.from_Date > record.to_date:
                raise ValidationError(_("The 'From Date' must be smaller than or equal to the 'To Date'."))

    # ---------------------------------------------------------------------
    # Helper – fetch rows using the official Odoo 19 valuation API
    # ---------------------------------------------------------------------
    def _fetch_valuation_rows(self):
        """Fetch stock valuation data for the selected filters.
        Returns:
            list[dict]: Valuation data used by the PDF and XLSX reports.
        """
        # Build a product recordset with valuation context so that
        # qty_available and related fields are filtered to valued locations.
        # _with_valuation_context() is provided by stock_account (a declared
        # dependency of this module).
        product_ctx = (
            self.env["product.product"]
            .sudo()
            .with_company(self.company_id or self.env.company)
            ._with_valuation_context()
        )
        domain = [
            ("is_storable", "=", True),
            "|",
            ("qty_available", "!=", 0),
            ("lot_valuated", "=", True),
        ]
        if self.product_id:
            domain.append(("id", "=", self.product_id.id))
        if self.product_category_id:
            domain.append(("categ_id", "child_of", self.product_category_id.id))
        products = product_ctx.search(domain)

        domain_moves = [
            ("product_id", "in", products.ids),
            ("state", "=", "done"),
        ]
        if self.from_Date:
            domain_moves.append(("create_date", ">=", self.from_Date))
        if self.to_date:
            domain_moves.append(("create_date", "<", self.to_date))

        moves = (
            self.env["stock.move"]
            .with_context(allowed_company_ids=self.env.company.ids)
            .search(domain_moves, order="create_date")
        )

        rows = []
        for move in moves:
            rows.append(
                {
                    "create_date": move.create_date,
                    "product_ref": move.product_id.default_code or "",
                    "name": move.product_id.name,
                    "description": move.reference or "",
                    "complete_name": move.product_id.categ_id.complete_name,
                    "company_name": move.company_id.name,
                    "quantity": move._get_valued_qty(),
                    "unit_cost": move._get_price_unit(),
                    "value": move.value,
                }
            )
        return rows

    def action_print_pdf_report(self):
        """Generate the Stock Valuation PDF report.
        Returns:
            dict: Report action for the PDF report.
        """
        self._check_dates()
        data = {
            "product_name": self.product_id.product_tmpl_id.name,
            "vehicle_id": self.product_category_id.display_name,
            "company_name": self.company_id.name,
            "company_street": self.company_id.street,
            "state": self.company_id.state_id.name,
            "country": self.company_id.country_id.name,
            "company_email": self.company_id.email,
            "stock_valuation": self._fetch_valuation_rows(),
        }
        return self.env.ref(
            "report_stock_inventory.stock_valuation_report"
        ).report_action(None, data=data)

    def action_print_xls_report(self):
        """Generate the Stock Valuation XLSX report.
        Returns:
            dict: XLSX report action.
        """
        self._check_dates()
        data = {
            "product_name": self.product_id.product_tmpl_id.name,
            "vehicle_id": self.product_category_id.display_name,
            "company_name": self.company_id.name,
            "company_street": self.company_id.street,
            "state": self.company_id.state_id.name,
            "country": self.company_id.country_id.name,
            "company_email": self.company_id.email,
            "stock_valuation": self._fetch_valuation_rows(),
        }
        return {
            "type": "ir.actions.report",
            "report_type": "xlsx",
            "data": {
                "model": "stock.valuation.report",
                "output_format": "xlsx",
                "options": json.dumps(data, default=str), # date_utils.json_default
                "report_name": "Stock valuation report",
            },
        }

    def get_xlsx_report(self, data, response):
        """Generate and stream the Stock Valuation Excel report.
        Args:
            data (dict): Report data.
            response: HTTP response used to stream the workbook.
        """
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        sheet = workbook.add_worksheet()
        sheet.set_column(0, 10, 24)
        head = workbook.add_format({"align": "center", "bold": True, "font_size": "20px"})
        txt = workbook.add_format({"align": "center"})
        sheet.merge_range("C2:E3", "STOCK VALUATION REPORT", head)
        sheet.merge_range("C4:E4", data["company_name"], txt)
        headers = [
            "SL No.",
            "Date",
            "Product Reference",
            "Product Name",
            "Description",
            "Product Category",
            "Company Name",
            "Quantity",
            "Unit Cost",
            "Value",
        ]
        for col, title in enumerate(headers):
            sheet.write(7, col, title, txt)
        for idx, rec in enumerate(data["stock_valuation"], start=1):
            row = 8 + idx
            sheet.write(row, 0, idx, txt)
            sheet.write(row, 1, rec["create_date"], txt)
            sheet.write(row, 2, rec["product_ref"], txt)
            sheet.write(row, 3, rec["name"], txt)
            sheet.write(row, 4, rec["description"], txt)
            sheet.write(row, 5, rec["complete_name"], txt)
            sheet.write(row, 6, rec["company_name"], txt)
            sheet.write(row, 7, rec["quantity"], txt)
            sheet.write(row, 8, rec["unit_cost"], txt)
            sheet.write(row, 9, rec["value"], txt)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
