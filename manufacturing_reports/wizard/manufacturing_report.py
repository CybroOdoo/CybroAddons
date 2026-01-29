# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Javid A(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import fields, models
from odoo.tools import date_utils
from odoo.tools.safe_eval import json

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter
import io


class ManufacturingReport(models.TransientModel):
    """
        This class creates a new model named manufacturing report and has the
        fields to filter the report
    """
    _name = 'manufacturing.report'
    _description = 'Manufacturing Report'

    filter = fields.Boolean(string='Enable Filter by Date',
                            help='Enabling filter by date allows you to filter '
                                 'the records by date')
    date_from = fields.Date(string='Start Date',
                            help='Filter by starting date')
    filter_user = fields.Boolean(string='Filter On Responsible',
                                 help='Enabling filter on responsible allows '
                                      'you to filter the records by '
                                      'responsible person')
    responsible_ids = fields.Many2many('res.users',
                                       string='Responsible',
                                       help='Filter by Responsible Person')
    product_ids = fields.Many2many('product.product',
                                   string='Product',
                                   help='Filter by Products')
    state = fields.Selection(
        [('confirmed', 'Confirmed'), ('planned', 'Planned'),
         ('progress', 'In Progress'),
         ('done', 'Done'), ('cancel', 'Cancelled')], string="State",
        help='Filter by states')

    def fetch_data(self):
        """fetches the data and append to a list and returns it"""
        conditions = []
        if self.product_ids:
            conditions.append(('product_id', 'in', self.product_ids.ids))
        if self.state:
            conditions.append(('state', '=', self.state))
        if self.date_from:
            conditions.append(('date_planned_start', '>=', self.date_from))
        if self.responsible_ids:
            conditions.append(('user_id', 'in', self.responsible_ids.ids))
        mrp_orders = self.env['mrp.production'].search(conditions)
        return mrp_orders

    def action_print_xlsx(self):
        """Calls the fetch_data function and print the Excel report"""
        mrp_orders = self.fetch_data()
        orders = [{
            'name': rec.name,
            'product': rec.product_id.name,
            'quantity': rec.product_qty,
            'unit': rec.product_uom_category_id.name,
            'responsible': rec.user_id.name,
            'start_date': rec.date_planned_start,
            'state': rec.state,
        } for rec in mrp_orders]
        data = {
            'date_from': self.date_from,
            'state': self.state,
            'mrp': orders
        }
        return {
            'type': 'ir.actions.report',
            'data': {
                'model': 'manufacturing.report',
                'options': json.dumps(data, default=date_utils.json_default),
                'output_format': 'xlsx',
                'report_name': 'Manufacturing Report', },
            'report_type': 'xlsx',
        }

    def action_print_pdf(self):
        """Calls the fetch_data function and print the PDF report"""
        mrp_orders = self.fetch_data()
        orders = [{
            'name': rec.name,
            'image': rec.product_id.image_1920,
            'product': rec.product_id.name,
            'quantity': rec.product_qty,
            'unit': rec.product_uom_category_id.name,
            'responsible': rec.user_id.name,
            'start_date': rec.date_planned_start,
            'state': rec.state,
        } for rec in mrp_orders]
        data = {
            'date_from': self.date_from,
            'state': self.state,
            'mrp': orders
        }
        return self.env.ref(
            'manufacturing_reports.action_report_mrp').report_action(self,
                                                                     data=data)

    def get_xlsx_report(self, data, response):
        """
        Set the rows and column for datas to print in Excel sheet
        :param data: The records data
        :param response: the corresponding response
        :return: XLSX file
        """
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        cell_format = workbook.add_format({'font_size': '12px', 'bold': True})
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '20px'})
        txt_head = workbook.add_format({'font_size': '12px'})
        sheet.set_column('B:B', 15)
        sheet.set_column('C:C', 15)
        sheet.set_column('D:D', 16)
        sheet.set_column('E:E', 11)
        sheet.set_column('F:F', 11)
        sheet.set_column('G:G', 15)
        sheet.set_column('H:H', 19)
        sheet.set_column('I:I', 15)
        sheet.merge_range('B2:H3', 'Manufacturing Orders', head)
        if data['date_from']:
            sheet.write('B6', 'From:', cell_format)
            sheet.merge_range('C6:D6', data['date_from'], txt_head)
        row = 9
        col = 2
        sheet.write(row, col, 'Reference', cell_format)
        sheet.write(row, col + 1, 'Product', cell_format)
        sheet.write(row, col + 2, 'Quantity', cell_format)
        sheet.write(row, col + 3, 'Unit', cell_format)
        sheet.write(row, col + 4, 'Responsible', cell_format)
        sheet.write(row, col + 5, 'Start Date', cell_format)
        sheet.write(row, col + 6, 'State', cell_format)
        for rec in data['mrp']:
            row += 1
            sheet.write(row, col, rec['name'])
            sheet.write(row, col + 1, rec['product'])
            sheet.write(row, col + 2, rec['quantity'])
            sheet.write(row, col + 3, rec['unit'])
            sheet.write(row, col + 4, rec['responsible'])
            sheet.write(row, col + 5, rec['start_date'])
            sheet.write(row, col + 6, rec['state'])
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
