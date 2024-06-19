# -*- coding: utf-8 -*-
################################################################################
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
################################################################################
import datetime
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductProfitReport(models.AbstractModel):
    """Abstract model to print the report"""
    _name = 'report.product_profit_report.product_profit_report'
    _description = 'Product profit Report Render'

    def _get_report_values(self, docids, data):
        """This method takes the value to the pdf report"""
        model_data = data['form']
        return self.generate_report_values(model_data)

    @api.model
    def generate_report_values(self, data):
        """Generate values for the report, based on condition"""
        domain = [('move_id.invoice_date', '>=', data['from_date']),
                  ('move_id.invoice_date', '<=', data['to_date']),
                  ('move_id.state', 'in', ['posted', 'paid']),
                  ('company_id', '=', data['company_id'][0]),
                  ('move_id.move_type', 'in', ['out_invoice', 'out_refund'])]
        if data['from_date'] > data['to_date']:
            raise ValidationError(_('From date must be less than To date'))
        if data['product_id']:
            domain += [('product_id.id', '=', data['product_id'][0])]
        orders = self.env['account.move.line'].search(domain, order='name')
        groups = {}
        for order in orders:
            if order.product_id.id in data['product_product_ids']:
                dic_name = str(order.product_id.id)
                quantity = order.quantity
                price = quantity * (order.price_unit - order.discount)
                if order.currency_id != order.company_currency_id:
                    currency_rate = self.env[
                        'res.currency']._get_conversion_rate(
                        from_currency=order.currency_id,
                        to_currency=order.company_currency_id,
                        company=order.company_id,
                        date=order.move_id.invoice_date or order.move_id.date or fields.Date.context_today(
                            order))
                    price = order.company_currency_id.round(
                        price * currency_rate)
                expense = order.product_id.get_history_price(
                    order.company_id.id,
                    date=order.move_id.invoice_date) * quantity
                if expense == 0.0:
                    expense = order.product_id.standard_price * quantity
                if order.move_id.move_type == 'out_refund':
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
            'report_date': datetime.datetime.now().strftime("%Y-%m-%d"),
        }
