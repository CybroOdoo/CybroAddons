# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
import io
import xlsxwriter
from odoo import fields, models
from odoo.tools import date_utils
from odoo.tools.safe_eval import json


class MrpReportWizard(models.Model):
    _name = 'mrp.report'
    _description = 'MRP Report'

    filter = fields.Boolean(string='Enable filter by date')
    date_from = fields.Date(string='Start Date')
    filter_user = fields.Boolean(string='Filter On Responsible')
    responsible_id = fields.Many2many('res.users', string='Responsible')
    product_id = fields.Many2many('product.product', string='Product')
    stage = fields.Selection(
        [('confirmed', 'Confirmed'), ('planned', 'Planned'), ('progress', 'In Progress'),
         ('done', 'Done'), ('cancel', 'Cancelled')], string="Filter State")

    def check_report(self):
        """
            Function to fetch the mrp orders according to the filters given in
            the wizard and print the XLS report
        """
        orders = []
        if self.product_id and self.stage and self.date_from and self.responsible_id:
            mrp_orders = self.env['mrp.production'].search(
                [('product_id', 'in', self.product_id.ids),
                 ('state', '=', self.stage), ('date_planned_start', '>=', self.date_from),
                 ('user_id', 'in', self.responsible_id.ids)])
        elif self.product_id and self.stage and self.date_from:
            mrp_orders = self.env['mrp.production'].search(
                [('product_id', 'in', self.product_id.ids),
                 ('state', '=', self.stage),
                 ('date_planned_start', '>=', self.date_from)])
        elif self.product_id and self.stage and self.responsible_id:
            mrp_orders = self.env['mrp.production'].search(
                [('product_id', 'in', self.product_id.ids),
                 ('state', '=', self.stage), ('user_id', 'in', self.responsible_id.ids)])
        elif self.product_id and self.date_from and self.responsible_id:
            mrp_orders = self.env['mrp.production'].search(
                [('product_id', 'in', self.product_id.ids),
                 ('date_planned_start', '>=', self.date_from),
                 ('user_id', 'in', self.responsible_id.ids)])
        elif self.stage and self.date_from and self.responsible_id:
            mrp_orders = self.env['mrp.production'].search(
                [('state', '=', self.stage), ('date_planned_start', '>=', self.date_from),
                 ('user_id', 'in', self.responsible_id.ids)])
        elif self.product_id and self.stage:
            mrp_orders = self.env['mrp.production'].search(
                [('product_id', 'in', self.product_id.ids), ('state', '=', self.stage)])
        elif self.product_id and self.date_from:
            mrp_orders = self.env['mrp.production'].search(
                [('product_id', 'in', self.product_id.ids),
                 ('date_planned_start', '>=', self.date_from)])
        elif self.product_id and self.responsible_id:
            mrp_orders = self.env['mrp.production'].search(
                [('product_id', 'in', self.product_id.ids),
                 ('user_id', 'in', self.responsible_id.ids)])
        elif self.stage and self.date_from:
            mrp_orders = self.env['mrp.production'].search(
                [('state', '=', self.stage),
                 ('date_planned_start', '>=', self.date_from)])
        elif self.stage and self.responsible_id:
            mrp_orders = self.env['mrp.production'].search(
                [('state', '=', self.stage), ('user_id', 'in', self.responsible_id.ids)])
        elif self.date_from and self.responsible_id:
            mrp_orders = self.env['mrp.production'].search(
                [('date_planned_start', '>=', self.date_from),
                 ('user_id', 'in', self.responsible_id.ids)])
        elif self.product_id:
            mrp_orders = self.env['mrp.production'].search(
                [('product_id', 'in', self.product_id.ids)])
        elif self.stage:
            mrp_orders = self.env['mrp.production'].search(
                [('state', '=', self.stage)])
        elif self.date_from:
            mrp_orders = self.env['mrp.production'].search(
                [('date_planned_start', '>=', self.date_from)])
        elif self.responsible_id:
            mrp_orders = self.env['mrp.production'].search(
                [('user_id', 'in', self.responsible_id.ids)])
        else:
            mrp_orders = self.env['mrp.production'].search([])
        for rec in mrp_orders:
            orders.append({
                'name': rec.name,
                'product': rec.product_id.name,
                'quantity': rec.product_qty,
                'unit': rec.product_uom_category_id.name,
                'responsible': rec.user_id.name,
                'start_date': rec.date_planned_start,
                'state': rec.state,
            })
        data = {
            'date_from': self.date_from,
            'stage': self.stage,
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
        if self.product_id and self.stage and self.date_from and self.responsible_id:
            mrp_orders = self.env['mrp.production'].search(
                [('product_id', 'in', self.product_id.ids),
                 ('state', '=', self.stage), ('date_planned_start', '>=', self.date_from),
                 ('user_id', 'in', self.responsible_id.ids)])
        elif self.product_id and self.stage and self.date_from:
            mrp_orders = self.env['mrp.production'].search(
                [('product_id', 'in', self.product_id.ids),
                 ('state', '=', self.stage), ('date_planned_start', '>=', self.date_from)])
        elif self.product_id and self.stage and self.responsible_id:
            mrp_orders = self.env['mrp.production'].search(
                [('product_id', 'in', self.product_id.ids),
                 ('state', '=', self.stage), ('user_id', 'in', self.responsible_id.ids)])
        elif self.product_id and self.date_from and self.responsible_id:
            mrp_orders = self.env['mrp.production'].search(
                [('product_id', 'in', self.product_id.ids),
                 ('date_planned_start', '>=', self.date_from),
                 ('user_id', 'in', self.responsible_id.ids)])
        elif self.stage and self.date_from and self.responsible_id:
            mrp_orders = self.env['mrp.production'].search(
                [('state', '=', self.stage), ('date_planned_start', '>=', self.date_from),
                 ('user_id', 'in', self.responsible_id.ids)])
        elif self.product_id and self.stage:
            mrp_orders = self.env['mrp.production'].search(
                [('product_id', 'in', self.product_id.ids), ('state', '=', self.stage)])
        elif self.product_id and self.date_from:
            mrp_orders = self.env['mrp.production'].search(
                [('product_id', 'in', self.product_id.ids),
                 ('date_planned_start', '>=', self.date_from)])
        elif self.product_id and self.responsible_id:
            mrp_orders = self.env['mrp.production'].search(
                [('product_id', 'in', self.product_id.ids),
                 ('user_id', 'in', self.responsible_id.ids)])
        elif self.stage and self.date_from:
            mrp_orders = self.env['mrp.production'].search(
                [('state', '=', self.stage), ('date_planned_start', '>=', self.date_from)])
        elif self.stage and self.responsible_id:
            mrp_orders = self.env['mrp.production'].search(
                [('state', '=', self.stage), ('user_id', 'in', self.responsible_id.ids)])
        elif self.date_from and self.responsible_id:
            mrp_orders = self.env['mrp.production'].search(
                [('date_planned_start', '>=', self.date_from),
                 ('user_id', 'in', self.responsible_id.ids)])
        elif self.product_id:
            mrp_orders = self.env['mrp.production'].search(
                [('product_id', 'in', self.product_id.ids)])
        elif self.stage:
            mrp_orders = self.env['mrp.production'].search(
                [('state', '=', self.stage)])
        elif self.date_from:
            mrp_orders = self.env['mrp.production'].search(
                [('date_planned_start', '>=', self.date_from)])
        elif self.responsible_id:
            mrp_orders = self.env['mrp.production'].search(
                [('user_id', 'in', self.responsible_id.ids)])
        else:
            mrp_orders = self.env['mrp.production'].search([])
        for rec in mrp_orders:
            orders.append({
                'name': rec.name,
                'image': rec.product_id.image_1920,
                'product': rec.product_id.name,
                'quantity': rec.product_qty,
                'unit': rec.product_uom_category_id.name,
                'responsible': rec.user_id.name,
                'start_date': rec.date_planned_start,
                'state': rec.state,
            })
        data = {
            'date_from': self.date_from,
            'stage': self.stage,
            'mrp': orders
        }
        return self.env.ref(
            'manufacturing_reports.action_mrp_report').report_action(self, data=data)

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        cell_format = workbook.add_format({'font_size': '12px', 'bold': True})
        head = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '20px'})
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
        if data['stage']:
            sheet.write('B7', 'State:', cell_format)
            sheet.merge_range('C7:D7', data['stage'], txt_head)
        row = 9
        col = 2
        sheet.write(row, col, 'Reference', cell_format)
        sheet.write(row, col+1, 'Product', cell_format)
        sheet.write(row, col+2, 'Quantity', cell_format)
        sheet.write(row, col+3, 'Unit', cell_format)
        sheet.write(row, col+4, 'Responsible', cell_format)
        sheet.write(row, col+5, 'Start Date', cell_format)
        sheet.write(row, col+6, 'State', cell_format)
        for rec in data['mrp']:
            row += 1
            sheet.write(row, col, rec['name'])
            sheet.write(row, col+1, rec['product'])
            sheet.write(row, col+2, rec['quantity'])
            sheet.write(row, col+3, rec['unit'])
            sheet.write(row, col+4, rec['responsible'])
            sheet.write(row, col+5, rec['start_date'])
            sheet.write(row, col+6, rec['state'])
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
