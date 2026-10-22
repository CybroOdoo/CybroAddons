# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import api, fields, models


class ReportPosOngoingSession(models.AbstractModel):
    """Generate ongoing session report of pos"""
    _name = 'report.advanced_pos_reports.report_pos_ongoing_session'
    _description = "Ongoing POS Session Report"

    def get_ongoing_sessions_details(self, session_ids=False):
        """Function to get ongoing session details"""
        sessions = self.env['pos.session']
        amount_total_without_tax = 0.0
        amount_total_tax = 0.0
        amount_total_return = 0.0
        orders = []

        if session_ids:
            sessions = self.env['pos.session'].search(
                [('state', '=', 'opened'),
                 ('id', 'in', session_ids)])
            for session in sessions:
                for order in session.order_ids.filtered(
                        lambda x: x.state in ['paid', 'done', 'invoiced']):
                    orders.append(order.id)
                    currency = order.currency_id
                    amount_untaxed = currency.round(
                        sum(line.price_subtotal for line in order.lines))
                    amount_return = sum(
                        payment.amount < 0 and payment.amount or 0 for payment
                        in order.payment_ids)
                    amount_total_without_tax += amount_untaxed
                    amount_total_tax += order.amount_tax
                    amount_total_return += amount_return

        order_ids = self.env["pos.order"].browse(orders)
        user_currency = self.env.company.currency_id
        total = 0.0
        for order in order_ids:
            order_curr = order.currency_id or order.pricelist_id.currency_id or user_currency
            if user_currency != order_curr:
                total += order_curr._convert(
                    order.amount_total, user_currency, order.company_id,
                    order.date_order or fields.Date.today())
            else:
                total += order.amount_total

        categories = []
        if order_ids:
            self.env.cr.execute("""
                SELECT category.name, sum(line.price_subtotal_incl) AS amount
                FROM pos_order_line AS line
                INNER JOIN product_product AS product ON line.product_id = product.id
                INNER JOIN product_template AS template ON product.product_tmpl_id = template.id
                INNER JOIN pos_category_product_template_rel AS categ ON product.product_tmpl_id = categ.product_template_id
                INNER JOIN pos_category AS category ON categ.pos_category_id = category.id
                WHERE line.order_id IN %s
                GROUP BY category.name
            """, (tuple(order_ids.ids),))
            for row in self.env.cr.dictfetchall():
                name = row['name']
                if isinstance(name, dict):
                    name = name.get(self.env.lang) or name.get('en_US') or next(iter(name.values()), '')
                row['name'] = name
                categories.append(row)

        payments = []
        payment_ids = self.env["pos.payment"].search(
            [('pos_order_id', 'in', order_ids.ids)]).ids
        if payment_ids:
            self.env.cr.execute("""
                SELECT method.name, sum(amount) total
                FROM pos_payment AS payment
                INNER JOIN pos_payment_method AS method ON payment.payment_method_id = method.id
                WHERE payment.id IN %s
                GROUP BY method.name
            """, (tuple(payment_ids),))
            for row in self.env.cr.dictfetchall():
                name = row['name']
                if isinstance(name, dict):
                    name = name.get(self.env.lang) or name.get('en_US') or next(iter(name.values()), '')
                row['name'] = name
                payments.append(row)

        opening_balance = 0.0
        for session in sessions:
            session_currency = session.currency_id or user_currency
            session_opening = session.opening_balance
            opening_lines = session.bank_statement_line_ids.filtered(
                lambda line: line.payment_ref and (
                    'Cash correction' in line.payment_ref or
                    line.payment_ref == session.env._('Cash correction from %(session)s', session=session.name) or
                    (not line.partner_id and not (line.payment_ref.startswith(f'{session.name}-in-') or line.payment_ref.startswith(f'{session.name}-out-')))
                )
            )
            session_opening += sum(opening_lines.mapped('amount'))
            if user_currency != session_currency:
                opening_balance += session_currency._convert(
                    session_opening, user_currency, session.company_id,
                    session.start_at or fields.Date.today()
                )
            else:
                opening_balance += session_opening

        return {
            'sessions': sessions,
            'categories': categories,
            'today': fields.Datetime.now(),
            'total_paid': user_currency.round(total),
            'amount_total_without_tax': amount_total_without_tax,
            'amount_total_tax': amount_total_tax,
            'amount_return': amount_total_return,
            'amount_total': total,
            'payments': payments,
            'opening_balance': opening_balance,
            'currency_precision': user_currency.decimal_places,
        }

    @api.model
    def _get_report_values(self, docids, data=None):
        """Get ongoing session report values"""
        data = dict(data or {})
        data.update(self.get_ongoing_sessions_details(data.get('session_ids', [])))
        return data
