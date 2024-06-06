# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import io
import json
import xlsxwriter
from odoo import models
from odoo.tools import date_utils


class StockPicking(models.Model):
    """ Added a function that to print sale order Excel report
            which is added using  server action """
    _inherit = "stock.picking"

    def print_excel_report(self):
        """ Function is used to print the Excel report
                It will pass the picking data through js file to
                 print Excel file"""
        # Take the ids of the selected pickings
        data = self._context['active_ids']
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'data': {'model': 'stock.picking',
                     'output_format': 'xlsx',
                     'options': json.dumps(data,
                                           default=date_utils.json_default),
                     'report_name': 'Picking Order Excel Report', }, }

    def get_xlsx_report(self, datas, response):
        """ From this function we can create and design the Excel file template
            and the map the values in the corresponding cells
            :param datas:Selected record ids
            :param response: Response after creating excel
        """
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        # for printing multiple sheet per file, iterate the pickings
        for picking in self.env['stock.picking'].browse(datas):
            picking_name = 'Delivery - ' + picking.name
            company_name = 'Company Name : ' + picking.company_id.name
            # Copy the value to a variable set black if it is null
            # instead of printing 'FALSE' in the report
            ref = picking.origin if picking.origin is not False else ''
            # Copy the value to a variable set black if it is null
            # instead of printing 'FALSE' in the report
            responsible_person = picking.user_id.name if \
                picking.user_id.name is not False else ''
            # Copy the value to a variable set black if it is null
            # instead of printing 'FALSE' in the report
            partner_name = picking.partner_id.name if \
                picking.partner_id.name is not False else ''
            # Copy the value to a variable set black if it is null instead
            # of printing 'FALSE' in the report
            partner_street = picking.partner_id.street if \
                picking.partner_id.street is not False else ''
            # Copy the value to a variable set black if it is null instead of
            # printing 'FALSE' in the report
            partner_state = picking.partner_id.state_id.name if \
                picking.partner_id.state_id.name is not False else ''
            # Copy the value to a variable set black if it is null instead
            # of printing 'FALSE' in the report
            partner_zip = picking.partner_id.zip if \
                picking.partner_id.zip is not False else ''
            # Copy the value to a variable set black if it is null instead
            # of printing 'FALSE' in the report
            partner_county = picking.partner_id.country_id.name if \
                picking.partner_id.country_id.name is not False else ''
            # Copy the value to a variable set black if it is null
            # instead of printing 'FALSE' in the report
            partner_phone = picking.partner_id.phone if \
                picking.partner_id.phone is not False else ''
            # Copy the value to a variable set black if it is null instead
            # of printing 'FALSE' in the report
            date_done = str(picking.date_done) if \
                picking.date_done is not False else ''
            scheduled_date = str(picking.scheduled_date)
            sheet = workbook.add_worksheet(
                picking.name)  # set the sheet name as picking name
            sheet.set_column(0, 8, 25)
            head = workbook.add_format(
                {'align': 'center', 'bold': True, 'font_size': '20px'})
            txt = workbook.add_format({'align': 'center', 'bold': True})
            txt_border = workbook.add_format(
                {'align': 'center', 'bold': True, 'border': 1})
            border = workbook.add_format({'border': 1})
            sheet.merge_range('B2:E3', picking_name, head)
            sheet.merge_range('B4:E4', company_name, txt)
            sheet.write('A6', 'Customer/Vendor Name', txt)
            sheet.write('B6', partner_name)
            sheet.write('B7', partner_street)
            sheet.write('B8', partner_state)
            sheet.write('B9', partner_zip)
            sheet.write('B10', partner_county)
            sheet.write('B11', partner_phone)
            sheet.write('D6', 'Scheduled Date', txt)
            sheet.write('D7', 'Effective Date', txt)
            sheet.write('D8', 'Operation Type', txt)
            sheet.write('D9', 'Source Location', txt)
            sheet.write('D10', 'Destination Location', txt)
            sheet.write('D11', 'State', txt)
            sheet.write('E6', scheduled_date)
            sheet.write('E7', date_done)
            sheet.write('E8', picking.picking_type_id.display_name)
            sheet.write('E9', picking.location_id.complete_name)
            sheet.write('E10', picking.location_dest_id.complete_name)
            sheet.write('E11', picking.state)
            sheet.write('A13', 'Responsible Person', txt)
            sheet.write('A14', responsible_person)
            sheet.write('B13', 'Source Document', txt)
            sheet.write('B14', ref)
            sheet.write('A16', 'Product', txt_border)
            sheet.write('B16', 'Description', txt_border)
            sheet.write('C16', 'Scheduled Date', txt_border)
            sheet.write('D16', 'Deadline', txt_border)
            sheet.write('E16', 'Quantity', txt_border)
            sheet.write('F16', 'Quantity Done', txt_border)
            row = 17
            # calling this function for adding picking line data to the
            # Excel sheet
            self._add_picking_line_to_excel(sheet, picking, row, border)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def _add_picking_line_to_excel(self, sheet, picking, row, border):
        """
            Function to add stock picking line values to the Excel file
            :param sheet: Current Excel sheet where data to be added
            :param picking : Object of transfer in which data adding
            :param row:Excel row value of next data to be added
            :param border :Excel styling for adding border for each cell
        """
        # For adding value of the sale order line
        for line in picking.move_ids:
            # Copy the value to a variable set black if it is null
            # instead of printing 'FALSE' in the report
            date_deadline = str(line.date_deadline) if \
                line.date_deadline is not False else ''
            date = str(line.date)
            sheet.write(row, 0, line.product_id.name, border)
            sheet.write(row, 1, line.description_picking, border)
            sheet.write(row, 2, date, border)
            sheet.write(row, 3, date_deadline, border)
            sheet.write(row, 4, line.product_uom_qty, border)
            sheet.write(row, 5, line.quantity, border)
            row += 1
