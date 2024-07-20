# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anfas Faisal K (odoo@cybrosys.info)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
import io
import json
import xlsxwriter
from odoo import models
from odoo.tools import date_utils


class AccountMove(models.Model):
    """Inherits the mrp bom model"""
    _inherit = 'mrp.bom'

    def action_print_bom_structure(self):
        """ generates an Excel report for the Bill of Materials (BoM)
        structure"""
        bom = self.env['mrp.bom'].browse(self.id)
        candidates = bom.product_id or bom.product_tmpl_id.product_variant_ids
        quantity = bom.product_qty
        for product_variant_id in candidates.ids:
            doc = self.env['report.mrp.report_bom_structure']._get_pdf_line(
                bom.id, product_id=product_variant_id,
                qty=quantity, unfolded=True)
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'mrp.bom',
                     'options': json.dumps(doc,
                                           default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'BoM Structure',
                     },
            'report_type': 'xlsx',
        }

    def get_xlsx_report(self, data, response):
        """assembling and formatting the report content"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        head = workbook.add_format(
            {'align': 'left', 'bold': True, 'font_size': '20px'})
        format3 = workbook.add_format({'font_size': '15px', 'bold': True})
        format4 = workbook.add_format({'font_size': 10})
        format6 = workbook.add_format({'font_size': 10, 'bold': True})
        sheet.merge_range('A1:F2', 'BoM Structure & Cost', head)
        sheet.merge_range('A4:Z5', data['bom_prod_name'], format3)
        sheet.merge_range('A7:B7', 'Products', format6)
        sheet.merge_range('D7:E7', 'BOM', format6)
        sheet.merge_range('F7:G7', 'Quantity', format6)
        sheet.merge_range('H7:I7', 'Unit of Measure', format6)
        sheet.merge_range('J7:K7', 'Product Cost', format6)
        sheet.merge_range('L7:M7', 'BOM Cost', format6)

        currency_symbol = self.env.user.company_id.currency_id.symbol
        row_start = 8

        # Write the main product and its BOM
        sheet.merge_range('A8:C8', data['bom_prod_name'], format6)
        sheet.merge_range('D8:E8', data.get('code', ''), format6)
        sheet.merge_range('F8:G8', '1.00', format4)

        if 'price' in data:
            price_with_symbol = f"{currency_symbol} {data['price']}"
            sheet.merge_range('J8:K8', price_with_symbol, format4)
        if 'bom_cost' in data:
            bom_cost_with_symbol = f"{currency_symbol} {data['bom_cost']}"
            sheet.merge_range('L8:M8', bom_cost_with_symbol, format4)

        row_start = 9
        for index, product in enumerate(data.get('lines', [])):
            current_row = index + row_start
            space_td = '    ' * product['level']

            sheet.merge_range(f'A{current_row}:C{current_row}',
                              space_td + product['name'], format4)
            if 'code' in product:
                sheet.merge_range(f'D{current_row}:E{current_row}',
                                  product['code'], format4)
            sheet.merge_range(f'F{current_row}:G{current_row}',
                              product['quantity'], format4)

            if 'uom' in product:
                sheet.merge_range(f'H{current_row}:I{current_row}',
                                  product['uom'], format4)
            if 'prod_cost' in product:
                prod_cost_with_symbol = f"{currency_symbol} {product['prod_cost']}"
                sheet.merge_range(f'J{current_row}:K{current_row}',
                                  prod_cost_with_symbol, format4)
            if 'bom_cost' in product:
                bom_cost_with_symbol = f"{currency_symbol} {product['bom_cost']}"
                sheet.merge_range(f'L{current_row}:M{current_row}',
                                  bom_cost_with_symbol, format4)

        # Add the Unit Cost row at the end
        last_row = row_start + len(data.get('lines', []))
        sheet.merge_range(f'F{last_row}:G{last_row}', 'Unit Cost', format6)
        if 'price' in data:
            prod_cost_with_symbol = f"{currency_symbol} {data['price']}"
            sheet.merge_range(f'J{last_row}:K{last_row}',
                              prod_cost_with_symbol, format4)
        if 'bom_cost' in data:
            bom_cost_with_symbol = f"{currency_symbol} {data['bom_cost']}"
            sheet.merge_range(f'L{last_row}:M{last_row}', bom_cost_with_symbol,
                              format4)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()