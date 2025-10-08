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
    """Inherits the account move model"""
    _inherit = 'mrp.bom'

    def action_print_bom_structure(self):
        """Generate and export the BOM Structure Report in Excel format."""
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
        """ Generate an Excel report with BOM structure and cost."""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        # Define cell formats
        head = workbook.add_format(
            {'align': 'left', 'bold': True, 'font_size': '20px'})
        format3 = workbook.add_format({'font_size': '15px', 'bold': True})
        format4 = workbook.add_format({'font_size': 10})
        format6 = workbook.add_format({'font_size': 10, 'bold': True})
        format7 = workbook.add_format({'font_size': 10, 'font_color': 'green'})
        format8 = workbook.add_format({'font_size': 10, 'font_color': 'red'})
        format9 = workbook.add_format({'font_size': 10, 'font_color': 'yellow'})
        # Check if there are components or lines in the data
        if data and data.get('components') or data.get('lines'):
            # Merge and format header cells
            sheet.merge_range('A1:F2', 'BoM Structure & Cost', head)
            sheet.merge_range('A4:Z5', data['name'], format3)
            # Merge and format cells for product information
            sheet.merge_range('A7:C7', 'Products', format6)
            sheet.merge_range('D7:E7', 'Quantity', format6)
            sheet.merge_range('F7:G7', 'Unit of Measure', format6)
            sheet.merge_range('H7:I7', 'Ready to Produce', format6)
            sheet.merge_range('J7:K7', 'Free to Use / On Hand', format6)
            sheet.merge_range('L7:M7', 'Availability', format6)
            sheet.merge_range('N7:O7', 'Lead Time', format6)
            sheet.merge_range('P7:Q7', 'Route', format6)
            sheet.merge_range('R7:S7', 'BOM Cost', format6)
            sheet.merge_range('T7:U7', 'Product Cost', format6)
            row_start = 9  # Starting row for data
            currency_symbol = self.env.user.company_id.currency_id.symbol
            # Iterate through lines in the data
            for index, value in enumerate(data.get('lines')):
                # Calculate leading spaces based on the level
                if value['level'] != 0:
                    space_td = '    ' * value['level']
                else:
                    space_td = '    '
                # Merge and format cells for product name
                sheet.merge_range('A8:C8', data['name'], format6)
                sheet.merge_range('D8:E8', data['quantity'], format4)
                sheet.merge_range(f'A{index + row_start}:C{index + row_start}',
                                  space_td + value['name'], format4)
                # Merge and format cells for quantity
                sheet.merge_range(f'D{index + row_start}:E{index + row_start}',
                                  value['quantity'], format4)
                # Merge and format cells for unit of measure
                if 'uom' in value:
                    sheet.merge_range(
                        f'F{index + row_start}:G{index + row_start}',
                        value['uom'], format4)
                # Merge and format cells for 'Ready to Produce'
                if 'producible_qty' in value:
                    sheet.merge_range('H8:I8', data['producible_qty'], format4)
                    sheet.merge_range(
                        f'H{index + row_start}:I{index + row_start}',
                        value['producible_qty'], format4)
                # Merge and format cells for 'Quantity Available / On Hand'
                if 'quantity_available' in value:
                    quantity_available_on_hand = \
                        f"{value['quantity_available']} / {value['quantity_on_hand']}"
                    sheet.merge_range(
                        'J8:K8', f"{data['quantity_available']} / "
                                 f"{data['quantity_on_hand']}", format4)
                    sheet.merge_range(
                        f'J{index + row_start}:K{index + row_start}',
                        quantity_available_on_hand, format4)
                # Merge and format cells for 'Availability'
                if 'availability_display' in value:
                    availability_main_text = data['availability_display']
                    availability_text = value['availability_display']
                    color_format_main = format7 if (
                            availability_main_text == 'Available') \
                        else (
                        format8 if availability_main_text == 'Not Available'
                        else format9)
                    color_format = format7 if availability_text == 'Available' \
                        else (format8 if availability_text == 'Not Available'
                              else format9)
                    sheet.merge_range(
                        'L8:M8', availability_main_text, color_format_main)
                    sheet.merge_range(
                        f'L{index + row_start}:M{index + row_start}',
                        availability_text, color_format)
                # Merge and format cells for 'Product Cost'
                if 'prod_cost' in value:
                    prod_cost_with_symbol = f"{currency_symbol} {data['prod_cost']} "
                    sheet.merge_range(
                        'R8:S8', prod_cost_with_symbol, format4)
                    sheet.merge_range(
                        f'R{index + row_start}:S{index + row_start}',
                        f"{currency_symbol} {value['prod_cost']}", format4)
                # Merge and format cells for 'BOM Cost'
                if 'bom_cost' in value:
                    bom_cost_with_symbol = f" {currency_symbol} {data['bom_cost']}"
                    sheet.merge_range(
                        'T8:U8', bom_cost_with_symbol, format4)
                    sheet.merge_range(
                        f'T{index + row_start}:U{index + row_start}',
                        f" {currency_symbol} {value['bom_cost']}", format4)
                # Merge and format cells for 'Route Info'
                if 'route_name' in value:
                    route_info = f"{value['route_name']} {value['route_detail']}"
                    sheet.merge_range(
                        f'P{index + row_start}:Q{index + row_start}',
                        route_info, format4)
                # Merge and format cells for 'Lead Time'
                if 'lead_time' in value:
                    lead_time = value['lead_time']
                    lead_time_days = f"{int(lead_time)} days" if lead_time != 0.0 else "0 days"
                    sheet.merge_range(
                        f'N{index + row_start}:O{index + row_start}',
                        lead_time_days, format4)
        # Close the workbook, seek to the beginning, and stream the output
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
