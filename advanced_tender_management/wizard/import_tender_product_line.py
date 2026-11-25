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
import io
import math

from openpyxl import load_workbook

from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tools import float_round


class ImportTenderProductLine(models.TransientModel):
    """Import tender product lines from an XLSX file.

    Columns: product, description, quantity. A row without description
    becomes a section. Unknown products are created."""
    _name = "import.tender.product.line"
    _description = 'Import Tender Product Line'

    file = fields.Binary(required=True, help='XLSX file with the product lines.')
    tender_id = fields.Many2one('tender.management', help='Tender receiving the lines.')

    def _read_rows(self):
        """Rows of every sheet of the file, without the header row, as
        (sheet name, row number, row values)."""
        try:
            workbook = load_workbook(io.BytesIO(self.file.content),
                                     read_only=True, data_only=True)
        except Exception as error:
            raise UserError(self.env._('Please upload a valid XLSX file.')) from error
        rows = []
        for sheet in workbook.worksheets:
            for row_number, row in enumerate(sheet.iter_rows(values_only=True), start=1):
                if row_number > 1 and row and row[0]:
                    rows.append((sheet.title, row_number, row))
        return rows

    def _parse_quantity(self, value, sheet_name, row_number):
        """Quantity of a row, rounded to the Product Unit precision; 1 when
        empty. It must be a number greater than zero."""
        if value is None or (isinstance(value, str) and not value.strip()):
            return 1.0
        try:
            quantity = float(value)
        except (TypeError, ValueError):
            quantity = None
        if quantity is not None and not isinstance(value, bool) and math.isfinite(quantity):
            digits = self.env['decimal.precision'].precision_get('Product Unit')
            quantity = float_round(quantity, precision_digits=digits)
            if quantity > 0:
                return quantity
        raise UserError(self.env._(
            'Row %(row)s of sheet "%(sheet)s": the quantity "%(qty)s" must be a '
            'number greater than zero.',
            row=row_number, sheet=sheet_name, qty=value))

    def _prepare_line(self, sheet_name, row_number, row):
        """Values of the tender line for one row of the file."""
        name, description = str(row[0]).strip(), row[1] if len(row) > 1 else None
        if not description:
            return {'name': name, 'display_type': 'line_section'}
        quantity = self._parse_quantity(row[2] if len(row) > 2 else None,
                                        sheet_name, row_number)
        product = self.env['product.product'].search([('name', '=', name)], limit=1)
        if not product:
            product = self.env['product.product'].create({'name': name})
        return {'product_id': product.id, 'name': str(description), 'product_qty': quantity}

    def action_import_tender_product_lines(self):
        """Add the lines of the file to the tender."""
        self.ensure_one()
        self.tender_id.tender_product_line_ids = [
            fields.Command.create(self._prepare_line(*row)) for row in self._read_rows()]
