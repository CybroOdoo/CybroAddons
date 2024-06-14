# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies(odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models
import openpyxl
import base64
from io import BytesIO


class StockMove(models.Model):
    """Inheriting stock_move to add additional new field and function"""
    _inherit = 'stock.move'

    attachment = fields.Binary(string="Upload")

    def action_import_lot(self):
        """Import and write lots to stock_move_line"""
        vals_list = []
        wb = openpyxl.load_workbook(
            filename=BytesIO(base64.b64decode(self.attachment)),
            read_only=True)
        ws = wb.active
        for record in ws.iter_rows(min_row=2, max_row=None,
                                   min_col=None,
                                   max_col=None, values_only=True):
            if record[1] == self.product_id.display_name:
                vals_list.append((0, 0, {
                    'lot_name': record[0],
                    'quantity': record[2],
                    'product_id': self.product_id.id
                }))
            continue
        self.move_line_ids.unlink()
        self.write({
            'move_line_ids': vals_list
        })
