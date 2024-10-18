# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohamed Muzammil VP (odoo@cybrosys.com)
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
###############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ReportRender(models.AbstractModel):
    """Model to print the report"""
    _name = 'report.product_profit_report.product_profit_report'
    _description = 'Product Profit Report Render'

    @api.multi
    def _get_report_values(self, docid, data):
        """This method takes the value to the pdf report"""
        return self.generate_report_values(data['form'])

    @api.model
    def generate_report_values(self, data):
        """Generate values for the report based on condition"""
        domain = [('invoice_id.date_invoice', '>=', data['from_date']),
                  ('invoice_id.date_invoice', '<=', data['to_date']),
                  ('invoice_id.state', 'in', ['open', 'paid']),
                  ('company_id', '=', data['company_id'][0]),
                  ('invoice_id.type', 'in', ['out_invoice', 'out_refund'])]
        if data['from_date'] > data['to_date']:
            raise ValidationError(_('From date must be less than To date'))
        if data['product_id']:
            domain += [('product_id.id', '=', data['product_id'][0])]
        orders = self.env['account.invoice.line'].search(domain, order='name')
        groups = {}
        for order in orders:
            if order.product_id.id in data['product_product_ids']:
                dic_name = str(order.product_id.id)
                quantity = order.quantity
                price = quantity * (order.price_unit - order.discount)
                expense = order.product_id.get_history_price(
                    order.company_id.id,
                    date=order.invoice_id.date_invoice) * quantity
                if expense == 0.0:
                    expense = order.product_id.standard_price * quantity
                if order.invoice_id.type == 'out_refund':
                    quantity = -quantity
                    price = -price
                    expense = -expense
                profit = price - expense
                if not groups.get(dic_name):
                    groups[dic_name] = {}
                    groups[dic_name].update({
                        'qty': quantity,
                        'unit': order.product_id.uom_id.name,
                        'sales': price,
                        'expense': expense,
                        'profit': profit,
                        'name': order.product_id.name
                    })
                else:
                    groups[dic_name].update({
                        'qty': groups[dic_name].get('qty') + quantity,
                        'sales': groups[dic_name].get('sales') + price,
                        'expense': groups[dic_name].get('expense') + expense,
                        'profit': groups[dic_name].get('profit') + profit
                    })
        return {
            'data': data,
            'groups': groups,
            'report_date': fields.Datetime.now().strftime("%Y-%m-%d"),
        }
