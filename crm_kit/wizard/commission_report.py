    # -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
import io
import json
from odoo import api, fields, models
from odoo.tools import date_utils
from odoo.exceptions import ValidationError

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class CommissionReport(models.TransientModel):
    """
    Commission Report wizard
    """
    _name = 'commission.report'
    _description = 'Commission Report Wizard'

    date_from = fields.Date(string="From Date", help="Date from which")
    date_to = fields.Date(string="To Date", help="Date to")
    salesperson_ids = fields.Many2many('res.users', string='Salesperson',
                                       domain="[('share','=',False)]",
                                       help="Salesperson")
    sales_team_ids = fields.Many2many('crm.team', string='Sales Team',
                                      help="Sales team")
    date = fields.Date(string='Date', default=fields.Date.context_today,
                       help="Date")
    is_sales_person = fields.Boolean(default=False, string="Is sales person",
                                     help="Is sales person")
    is_sales_team = fields.Boolean(default=False, string="Is sales team",
                                   help="Is sales team")

    @api.onchange('salesperson_ids')
    def onchange_salesperson_ids(self):
        """Function for hide a field base on values"""
        self.is_sales_person = True if self.salesperson_ids else False

    @api.onchange('sales_team_ids')
    def onchange_sales_team_ids(self):
        self.is_sales_team = True if self.sales_team_ids else False

    @api.constrains('sales_team_ids', 'salesperson_ids')
    def sales_team_constrains(self):
        """Function for showing validation error"""
        for rec in self:
            if self.sales_team_ids:
                if not rec.sales_team_ids.member_ids:
                    raise ValidationError(
                        "Selected Sales Team haven't any Salespersons")
                if not self.sales_team_ids.member_ids.commission_id and \
                        not self.sales_team_ids.commission_id:
                    raise ValidationError(
                        "Selected Sales Team haven't any Commission Plan")
            elif self.salesperson_ids and not rec.salesperson_ids.commission_id:
                raise ValidationError(
                    "Selected Salesperson haven't any Commission Plan")

    def action_print_xls_report(self):
        """Function for printing xlsx report"""
        # sales person's condition starts here #
        user_sale_orders = self.env['sale.order'].search([
            ('user_id', 'in', self.salesperson_ids.ids)])
        user_sale_orders_dict = {}
        total_list = []
        commission_list = []
        user_commission_name = []
        user_commission_salesperson = []
        user_obj = user_sale_orders.mapped('user_id').sorted(key=lambda d: d.id)
        for user in user_obj:
            user_sale_orders_dict.update({
                user: user_sale_orders.filtered(lambda l: l.user_id == user)
            })
        for user, user_sale_orders in user_sale_orders_dict.items():
            commission_id = user.commission_id
            if not commission_id:
                continue
            filtered_order_lines = user_sale_orders.filtered(
                lambda l: self.date_from <= l.date_order.date(
                ) <= self.date_to and l.date_order.date() >= commission_id.date_from
            ).mapped('order_line')
            filtered_order_lines_commission_total = sum(
                filtered_order_lines.mapped('price_subtotal'))

            if commission_id.type == 'product':
                commission_products = commission_id.product_comm_ids.product_id
                prod_commission = filtered_order_lines.filtered(
                    lambda l: l.product_id in commission_products)
                for rule in commission_id.product_comm_ids.filtered(
                        lambda l: l.product_id in prod_commission.mapped(
                            'product_id')):
                    product_order_line = prod_commission.filtered(
                        lambda l: l.product_id == rule.product_id)
                    total_price = sum(
                        product_order_line.mapped('price_subtotal'))
                    product_commission = (total_price * rule.percentage) / 100
                    total_list.append(total_price)
                    user_commission_name.append(commission_id.name)
                    user_commission_salesperson.append(user.name)
                    commission_list.append(rule.amount) if (
                            product_commission > rule.amount) \
                        else commission_list.append(product_commission)

            if commission_id.type == 'revenue' and (
                    commission_id.revenue_type == 'graduated'):
                for rule in commission_id.revenue_grd_comm_ids:
                    if rule.amount_from <= filtered_order_lines_commission_total < rule.amount_to:
                        graduated_commission = (filtered_order_lines_commission_total
                                                * rule.graduated_commission_rate) / 100
                        commission_list.append(graduated_commission)
                        user_commission_name.append(commission_id.name)
                        user_commission_salesperson.append(user.name)
                        total_list.append(filtered_order_lines_commission_total)

            if commission_id.type == 'revenue' and (
                    commission_id.revenue_type == 'straight'):
                straight_commission = (filtered_order_lines_commission_total
                                       * commission_id.straight_commission_rate) / 100
                commission_list.append(straight_commission)
                user_commission_name.append(commission_id.name)
                user_commission_salesperson.append(user.name)
                total_list.append(filtered_order_lines_commission_total)
        # sales person's condition ends here #

        if not self.sales_team_ids and not self.salesperson_ids:
            self.sales_team_ids = self.env['crm.team'].search([])

        # sales team's condition starts here #
        team_wizard_persons = self.sales_team_ids.member_ids
        team_sale_orders = self.env['sale.order'].search(
            [('user_id', 'in', team_wizard_persons.ids)])
        team_sale_orders_dict = {}
        commission_total = []
        commission = []
        commission_name = []
        commission_salesperson = []
        commission_sales_team = []
        team_obj = team_sale_orders.mapped('user_id').sorted(key=lambda d: d.id)
        for team_user in team_obj:
            team_sale_orders_dict.update({
                team_user: team_sale_orders.filtered(
                    lambda l: l.user_id == team_user)
            })
        for team_user, team_sale_orders in team_sale_orders_dict.items():
            commissions_id = team_user.commission_id if team_user.commission_id \
                else team_user.sale_team_id.commission_id
            if commissions_id:
                filtered_order_lines = team_sale_orders.filtered(
                    lambda l: self.date_from <= l.date_order.date(
                    ) <= self.date_to and l.date_order.date() >= commissions_id.date_from
                ).mapped('order_line')
                filtered_order_lines_commission_total = sum(
                    filtered_order_lines.mapped('price_subtotal'))
                if commissions_id.type == 'product':
                    commission_products = commissions_id.product_comm_ids.product_id
                    prod_commission = filtered_order_lines.filtered(
                        lambda l: l.product_id in commission_products)
                    for rules in commissions_id.product_comm_ids.filtered(
                            lambda l: l.product_id in prod_commission.mapped(
                                'product_id')):
                        product_order_line = prod_commission.filtered(
                            lambda l: l.product_id == rules.product_id)
                        total_price = sum(
                            product_order_line.mapped('price_subtotal'))
                        product_commission = (total_price * rules.percentage) / 100
                        commission_total.append(total_price)
                        commission_name.append(commissions_id.name)
                        commission_salesperson.append(team_user.name)
                        commission_sales_team.append(
                            team_user.sale_team_id.name)
                        commission.append(rules.amount) if (
                                product_commission > rules.amount) \
                            else commission.append(product_commission)

                if commissions_id.type == 'revenue' and (
                        commissions_id.revenue_type == 'graduated'):
                    for rules in commissions_id.revenue_grd_comm_ids:
                        if rules.amount_from <= filtered_order_lines_commission_total \
                                < rules.amount_to:
                            graduated_commission = (filtered_order_lines_commission_total
                                                               * rules.graduated_commission_rate) / 100
                            commission.append(graduated_commission)
                            commission_name.append(commissions_id.name)
                            commission_salesperson.append(team_user.name)
                            commission_sales_team.append(
                                team_user.sale_team_id.name)
                            commission_total.append(
                                filtered_order_lines_commission_total)

                if commissions_id.type == 'revenue' and (
                        commissions_id.revenue_type == 'straight'):
                    straight_commission = (filtered_order_lines_commission_total
                                           * commissions_id.straight_commission_rate) / 100
                    commission.append(straight_commission)
                    commission_name.append(commissions_id.name)
                    commission_salesperson.append(team_user.name)
                    commission_sales_team.append(team_user.sale_team_id.name)
                    commission_total.append(
                        filtered_order_lines_commission_total)
        # sales team's condition ends here #

        data = {
            'model_id': self.id,
            'date': self.date,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'sales_team_ids': self.sales_team_ids.ids,
            'salesperson_ids': self.salesperson_ids.ids,
            'commission_list': commission_list,
            'total_list': total_list,
            'commission': commission,
            'commission_total': commission_total,
            'commission_name': commission_name,
            'commission_salesperson': commission_salesperson,
            'commission_sales_team': commission_sales_team,
            'user_commission_name': user_commission_name,
            'user_commission_salesperson': user_commission_salesperson,
        }
        return {
            'type': 'ir.actions.report',
            'data': {
                'model': 'commission.report',
                'options': json.dumps(data, default=date_utils.json_default),
                'output_format': 'xlsx',
                'report_name': 'Commission Plan xlsx report'},
            'report_type': 'xlsx'
        }

    def get_xlsx_report(self, data, response):
        """get_xlsx_report function"""
        date = data['date']
        team = data['sales_team_ids']
        user = data['salesperson_ids']
        commission_list = data['commission_list']
        total_list = data['total_list']
        commission = data['commission']
        commission_total = data['commission_total']
        commission_name = data['commission_name']
        commission_salesperson = data['commission_salesperson']
        commission_sales_team = data['commission_sales_team']
        user_commission_name = data['user_commission_name']
        user_commission_salesperson = data['user_commission_salesperson']

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        head = workbook.add_format({'align': 'center', 'bold': True,
                                    'font_size': '15px', 'valign': 'vcenter'})
        format1 = workbook.add_format({'align': 'left', 'font_size': '12px'})
        format2 = workbook.add_format({'align': 'right', 'font_size': '12x'})
        format3 = workbook.add_format(
            {'align': 'right', 'font_size': '12x', 'bold': True})
        heading = workbook.add_format({'align': 'left', 'bold': True,
                                       'font_size': '12px',
                                       'valign': 'vcenter'})
        date_format = workbook.add_format(
            {'num_format': 'dd/mm/yy', 'align': 'left', 'font_size': '10px'})

        sheet.merge_range('A2:B2', "Printed Date: " + date, date_format)
        sheet.write('A4', 'No.', heading)
        sheet.set_column(5, 1, 25)
        sheet.set_row(0, 25)
        row = 5
        col = 0
        index = 1
        if user:
            sheet.merge_range('A1:E1', 'COMMISSION PLAN REPORT', head)
            sheet.write('D2', 'Date From: ' + data['date_from'], date_format)
            sheet.write('E2', 'Date To: ' + data['date_to'], date_format)

            sheet.write('B4', 'Sale Persons', heading)
            sheet.write('C4', 'Commission Plan Name', heading)
            sheet.write('D4', 'Total Revenue', heading)
            sheet.write('E4', 'Commission Amount', heading)

            for data in user_commission_salesperson:
                sheet.write(row, col + 0, index, format2)
                sheet.write(row, col + 1, data, format1)
                row += 1
                index += 1

            row = 5
            col = 0
            for data in user_commission_name:
                sheet.write(row, col + 2, data, format1)
                row += 1

            row = 5
            col = 0
            for data in total_list:
                sheet.write(row, col + 3, round(data, 2), format2)
                row += 1

            row = 5
            col = 0
            for data in commission_list:
                sheet.write(row, col + 4, round(data, 2), format2)
                row += 1

            sheet.write(row + 1, col + 2, 'Total', format3)
            sheet.write(row + 1, col + 3, round(sum(total_list), 2), format2)
            sheet.write(row + 1, col + 4, round(sum(commission_list), 2),
                        format2)

        elif team:
            sheet.merge_range('A1:F1', 'COMMISSION PLAN REPORT', head)
            sheet.write('E2', 'Date From: ' + data['date_from'], date_format)
            sheet.write('F2', 'Date To: ' + data['date_to'], date_format)

            sheet.write('B4', 'Sales Teams', heading)
            sheet.write('C4', 'Sales Person', heading)
            sheet.write('D4', 'Commission Plan Name', heading)
            sheet.write('E4', 'Total Revenue', heading)
            sheet.write('F4', 'Commission Amount', heading)

            for data in commission_sales_team:
                sheet.write(row, col + 0, index, format2)
                sheet.write(row, col + 1, data, format1)
                row += 1
                index += 1

            row = 5
            col = 0
            for data in commission_salesperson:
                sheet.write(row, col + 2, data, format1)
                row += 1

            row = 5
            col = 0
            for data in commission_name:
                sheet.write(row, col + 3, data, format1)
                row += 1

            row = 5
            col = 0
            for data in commission_total:
                sheet.write(row, col + 4, round(data, 2), format2)
                row += 1

            row = 5
            col = 0
            for data in commission:
                sheet.write(row, col + 5, round(data, 2), format2)
                row += 1

            sheet.write(row + 1, col + 3, 'Total:', format3)
            sheet.write(row + 1, col + 4, round(sum(commission_total), 2),
                        format2)
            sheet.write(row + 1, col + 5, round(sum(commission), 2), format2)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
