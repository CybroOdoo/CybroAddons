# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from datetime import timedelta
from functools import partial
from itertools import groupby

import psycopg2
import pytz
import re

from odoo import api, fields, models, tools, _
from odoo.tools import float_is_zero, float_round, float_repr, float_compare
from odoo.exceptions import ValidationError, UserError
from odoo.http import request
from odoo.osv.expression import AND
import base64

_logger = logging.getLogger(__name__)


class ReportSaleDetails(models.AbstractModel):
    _name = 'report.advanced_pos_reports.report_pos_saledetails'
    _description = 'Point of Sale Details'

    @api.model
    def get_sale_details(self, date_start=False, date_stop=False, user_ids=False):
        domain = [('state', 'in', ['paid', 'invoiced', 'done'])]

        if date_start:
            date_start = fields.Datetime.from_string(date_start)
        else:
            user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
            today = user_tz.localize(fields.Datetime.from_string(fields.Date.context_today(self)))
            date_start = today.astimezone(pytz.timezone('UTC'))

        if date_stop:
            date_stop = fields.Datetime.from_string(date_stop)
            if (date_stop < date_start):
                date_stop = date_start + timedelta(days=1, seconds=-1)
        else:
            date_stop = date_start + timedelta(days=1, seconds=-1)

        domain = AND([domain,
                      [('date_order', '>=', fields.Datetime.to_string(date_start)),
                       ('date_order', '<=', fields.Datetime.to_string(date_stop))]
                      ])

        orders = self.env['pos.order'].search(domain)
        orders_summary = []
        amount_total = 0
        amount_tax = 0
        for user in user_ids:
            total_sales = 0
            total_tax = 0
            orders_list = []
            payments = []
            categories = []
            for order in orders.filtered(lambda x:x.user_id.id == user.id):
                total_sales += order.amount_total
                total_tax += order.amount_tax
                amount_total += order.amount_total
                amount_tax += order.amount_tax
                orders_list.append(order.id)
            if orders_list:
                payment_ids = self.env["pos.payment"].search([('pos_order_id', 'in', orders_list)]).ids
                if payment_ids:
                    self.env.cr.execute("""
                        SELECT method.name, sum(amount) total
                        FROM pos_payment AS payment,
                             pos_payment_method AS method
                        WHERE payment.payment_method_id = method.id
                            AND payment.id IN %s
                        GROUP BY method.name
                    """, (tuple(payment_ids),))
                    payments = self.env.cr.dictfetchall()
                else:
                    payments = []
                categ = self.env.cr.execute("""SELECT category.name,
                    sum(price_subtotal_incl) as amount FROM pos_order_line AS line,
                    pos_category AS category, product_product AS product INNER JOIN
                    product_template AS template ON product.product_tmpl_id = template.id 
                    WHERE line.product_id = product.id
                    AND template.pos_categ_id = category.id
                    AND line.order_id IN %s
                    GROUP BY category.name ORDER BY amount DESC
                    """, (tuple(orders_list),))
                categories = self.env.cr.dictfetchall()
            orders_summary.append({'user': user.name, 'total_sales': total_sales, 'tax': total_tax,
                                   'gross_total': total_sales, 'payments': payments, 'categories': categories})
        user_currency = self.env.company.currency_id

        return {
            'currency_precision': user_currency.decimal_places,
            'order_summary': orders_summary,
            'users': user_ids,
            'company_name': self.env.company.name,
            'amount_total_without_tax': amount_total - amount_tax,
            'amount_tax': amount_tax
        }

    @api.model
    def _get_report_values(self, docids, data=None):
        data = dict(data or {})
        users = self.env['res.users'].browse(data['user_ids'])
        data.update(self.get_sale_details(data['date_start'], data['date_stop'], users))
        return data
