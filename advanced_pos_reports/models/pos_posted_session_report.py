# -*- coding: utf-8 -*-


from odoo import api, fields, models, tools, _

from odoo.osv.expression import AND


class ReportPosPosted(models.AbstractModel):
    _name = 'report.advanced_pos_reports.report_pos_posted_session'

    def get_posted_sessions_details(self, session_ids=False):
        domain = [('state', '=', 'closed')]
        if session_ids:
            domain = AND([domain, [('id', 'in', session_ids)]])
        sessions = self.env['pos.session'].search(domain)
        amount_total_without_tax = 0
        amount_total_tax = 0
        amount_total_return = 0
        orders = []
        for session in sessions:
            for order in session.order_ids.filtered(lambda x: x.state in ['paid', 'done', 'invoiced']):
                orders.append(order.id)
                currency = order.pricelist_id.currency_id
                amount_tax = currency.round(
                    sum(order._amount_line_tax(line, order.fiscal_position_id) for line in order.lines))
                amount_untaxed = currency.round(sum(line.price_subtotal for line in order.lines))
                amount_return = sum(payment.amount < 0 and payment.amount or 0 for payment in order.payment_ids)
                amount_total_without_tax += amount_untaxed
                amount_total_tax += amount_tax
                amount_total_return += amount_return
        order_ids = self.env["pos.order"].search([('id', 'in', orders)])
        user_currency = self.env.company.currency_id

        total = 0.0
        for order in order_ids:
            if user_currency != order.pricelist_id.currency_id:
                total += order.pricelist_id.currency_id._convert(
                    order.amount_total, user_currency, order.company_id, order.date_order or fields.Date.today())
            else:
                total += order.amount_total
            currency = order.session_id.currency_id

        categories = []
        if order_ids:
            self.env.cr.execute("""SELECT category.name,
                sum(price_subtotal_incl) as amount FROM pos_order_line AS line,
                pos_category AS category, product_product AS product INNER JOIN
                product_template AS template ON product.product_tmpl_id = template.id WHERE line.product_id = product.id
                AND template.pos_categ_id = category.id
                AND line.order_id IN %s GROUP BY category.name """, (tuple(order_ids.ids),))
            categories = self.env.cr.dictfetchall()

        payment_ids = self.env["pos.payment"].search([('pos_order_id', 'in', order_ids.ids)]).ids
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

        return {
            'sessions': sessions,
            'categories': categories,
            'today': fields.Datetime.now(),
            'total_paid': user_currency.round(total),
            'amount_total_without_tax': amount_total_without_tax,
            'amount_total_tax': amount_total_tax,
            'amount_return': amount_total_return,
            'amount_total': total,
            'payments': payments
        }

    @api.model
    def _get_report_values(self, docids, data=None):
        data = dict(data or {})
        data.update(self.get_posted_sessions_details(data['session_ids']))
        return data
