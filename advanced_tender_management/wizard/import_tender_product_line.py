# -*- coding: utf-8 -*-
###############################################################################
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
###############################################################################
import base64
import xlrd
from odoo import models, fields, _
from odoo.exceptions import UserError


class ImportTenderProductLine(models.TransientModel):
    """Import tender product lines from xlsx files"""
    _name = "import.tender.product.line"
    _description = 'Import Tender Product Line'

    file = fields.Binary(string="File", required=True,help='tender file')
    tender_id = fields.Many2one('tender.management',help='related tender')

    def action_import_tender_product_lines(self):
        """Function for importing records from xlsx file to tender product lines"""
        try:
            book = xlrd.open_workbook(
                file_contents=base64.decodebytes(self.file))
            row_value = []
            for sheet in book.sheets():
                for row in range(1, sheet.nrows):
                    row_value.append(sheet.row_values(row))

            for row in row_value:
                product_record = self.env['product.product'].search([('name', '=', row[0])])
                if not row[1]:
                    tender_product_lines = [(fields.Command.create({
                        'name': row[0],
                        'display_type': 'line_section'
                    }))]
                elif product_record:
                    tender_product_lines = [(fields.Command.create({
                        'product_id': product_record[0].id,
                        'name': row[0],
                        'product_qty': row[2]
                    }))]
                else:
                    new_product=self.env['product.product'].create({
                        'name':row[0],
                        'uom_id':1,
                    })
                    tender_product_lines = [(fields.Command.create({
                        'product_id': new_product.id,
                        'name': row[1],
                        'product_qty': row[2]
                    }))]
                self.tender_id.update({
                    'tender_product_line_ids': tender_product_lines})
        except:
            raise UserError(_('Please insert a valid file'))
