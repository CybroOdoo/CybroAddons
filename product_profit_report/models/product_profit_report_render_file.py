# -*- coding: utf-8 -*-
import datetime
import logging
from odoo import api, models, _

_logger = logging.getLogger(__name__)


class ReportRender(models.AbstractModel):
    _name = 'report.product_profit_report.report_product_profit_report'
    _description = 'Product profit Report Render'

    @api.multi
    def get_report_values(self, docid, data):
        # only for pdf report
        model_data = data['form']
        return self.generate_report_values(model_data)

    @api.model
    def generate_report_values(self, data):
        from_date = data['from_date']
        to_date = data['to_date']
        company = data['company']
        categ_id = data['categ_id']
        product_id = data['product_id']
        domain = [('invoice_id.date_invoice', '>=', from_date),
                  ('invoice_id.date_invoice', '<=', to_date),
                  ('invoice_id.state', 'in', ['open', 'paid']),
                  ('company_id', '=', company[0]),
                  ('invoice_id.type', 'in', ['out_invoice', 'out_refund'])]
        if categ_id:
            domain += [('product_id.categ_id.id', '=', categ_id[0])]
        if product_id:
            domain += [('product_id.id', '=', product_id[0])]
        orders = self.env['account.invoice.line'].search(domain, order='name')
        groups = {}
        for order in orders:
            dic_name = str(order.product_id.id)
            quantity = order.quantity
            price = quantity * (order.price_unit - order.discount)
            expense = order.product_id.get_history_price(order.company_id.id, date=order.invoice_id.date_invoice) * quantity
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
            'report_date': datetime.datetime.now().strftime("%Y-%m-%d"),
        }
