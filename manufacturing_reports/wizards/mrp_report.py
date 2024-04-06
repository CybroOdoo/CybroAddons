# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana Haseen (<https://www.cybrosys.com>)
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
import io
import xlsxwriter
from odoo import api, fields, models
from odoo.tools import date_utils
from odoo.tools.safe_eval import json


class MrpReport(models.TransientModel):
    _name = 'mrp.report'
    _description = 'MRP Report'

    filter = fields.Boolean(string='Enable filter by date')
    date_from = fields.Date(string='Start Date')
    filter_user = fields.Boolean(string='Filter On Responsible')
    responsible_id = fields.Many2many('res.users', string='Responsible')
    product_id = fields.Many2many('product.product', string='Product')
    state = fields.Selection(
        [('draft', 'Draft'), ('confirmed', 'Confirmed'), ('planned', 'Planned'),
         ('progress', 'In Progress'),
         ('done', 'Done'), ('cancel', 'Cancelled')], string="Filter State")

    @api.onchange('filter_user')
    def onchange_filter_mode(self):
        if self.filter_user == 'False':
            self.responsible_id = None
        self.responsible_id = False

    @api.onchange('filter')
    def onchange_filter_state(self):
        if self.filter == 'False':
            self.date_from = None
        self.date_from = False

    def check_report(self):
        """
            Function to fetch the mrp orders according to the filters given in
            the wizard and print the XLS report
        """
        orders = []
        conditions = []
        if self.product_id:
            conditions.append(('product_id', 'in', self.product_id.ids))
        if self.state:
            conditions.append(('state', '=', self.state))
        if self.date_from:
            conditions.append(('date_start', '>=', self.date_from))
        if self.responsible_id:
            conditions.append(('user_id', 'in', self.responsible_id.ids))

        mrp_orders = self.env['mrp.production'].search(conditions)
        for rec in mrp_orders:
            orders.append({
                'name': rec.name,
                'product': rec.product_id.name,
                'quantity': rec.product_qty,
                'unit': rec.product_uom_category_id.name,
                'responsible': rec.user_id.name,
                'start_date': rec.date_start,
                'state': dict(self.env['mrp.production']._fields[
                    'state']._description_selection(
                    self.env)).get(rec['state']),
            })
        data = {
            'date_from': self.date_from,
            'state': dict(self.env['mrp.production']._fields[
                'state']._description_selection(
                self.env)).get(rec['state']),
            'mrp': orders
        }
        return {
            'type': 'ir.actions.report',
            'data': {
                'model': 'mrp.report',
                'options': json.dumps(data, default=date_utils.json_default),
                'output_format': 'xlsx',
                'report_name': 'Manufacturing Report', },
            'report_type': 'xlsx',
        }

    def print_pdf(self):
        """
            Function to fetch the mrp orders according to the filters given in
            the wizard and print the PDF report
        """
        orders = []
        conditions = []
        if self.product_id:
            conditions.append(('product_id', 'in', self.product_id.ids))
        if self.state:
            conditions.append(('state', '=', self.state))
        if self.date_from:
            conditions.append(('date_start', '>=', self.date_from))
        if self.responsible_id:
            conditions.append(('user_id', 'in', self.responsible_id.ids))
        mrp_orders = self.env['mrp.production'].search(conditions)
        for rec in mrp_orders:
            orders.append({
                'name': rec.name,
                'image': rec.product_id.image_1920,
                'product': rec.product_id.name,
                'quantity': rec.product_qty,
                'unit': rec.product_uom_category_id.name,
                'responsible': rec.user_id.name,
                'start_date': rec.date_start,
                'state': dict(self.env['mrp.production']._fields[
                    'state']._description_selection(
                    self.env)).get(rec['state']),
            })
        data = {
            'date_from': self.date_from,
            'state': [order['state'] for order in orders] if self.state else None,
            'mrp': orders
        }
        return self.env.ref(
            'manufacturing_reports.action_mrp_report').report_action(self,
                                                                     data=data)

    def get_xlsx_report(self, data, response):
        """
            Setting the position to print the datas in the xlsx file
        """
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        head_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#dec5c5'
        })
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
        sheet.merge_range('C2:I3', 'Manufacturing Orders', head_format)
        if data['date_from']:
            sheet.write('C6', 'From:', cell_format)
            sheet.merge_range('D6:E6', data['date_from'], txt_head)
        if data['state'] and self.state:
            sheet.write('C7', 'State:', cell_format)
            sheet.merge_range('D7:E7', data['state'], txt_head)
        else:
            sheet.write('C7', 'State:', cell_format)
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
