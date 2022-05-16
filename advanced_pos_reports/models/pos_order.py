import logging
from odoo import models

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def get_category_summary(self, order_ids):
        orders = self.env['pos.order'].search([('id', 'in', order_ids)])
        categories = []
        if orders:
            self.env.cr.execute("""SELECT category.name, sum(price_subtotal_incl) as amount, 
                sum(qty) as qty FROM pos_order_line AS line INNER JOIN
                product_product AS product ON line.product_id = product.id INNER JOIN
                product_template AS template ON product.product_tmpl_id = template.id 
                INNER JOIN pos_category as category ON template.pos_categ_id = category.id 
                WHERE line.order_id IN %s GROUP BY category.name """, (tuple(orders.ids),))
            categories = self.env.cr.dictfetchall()
        return categories

    def get_product_summary(self, order_ids):
        orders = self.env['pos.order'].search([('id', 'in', order_ids)])
        if orders:
            self.env.cr.execute("""
                SELECT product.id, template.name, product.default_code as code, sum(qty) as qty
                FROM product_product AS product,
                     pos_order_line AS line, product_template AS template
                WHERE product.id = line.product_id AND template.id = product.product_tmpl_id
                    AND line.order_id IN %s
                GROUP BY product.id, template.name, template.default_code
            """, (tuple(orders.ids),))
            product_summary = self.env.cr.dictfetchall()
        else:
            product_summary = []
        return product_summary

    def get_order_summary(self, order_ids):
        orders = self.env['pos.order'].search([('id', 'in', order_ids)])
        order_summary = []
        for order in orders:
            order_summary.append(
                {'order_name': order.name, 'state': dict(self._fields['state'].selection).get(order.state),
                 'date_order': order.date_order, 'amount_total': order.amount_total})
        return order_summary


class PosPayment(models.Model):
    _inherit = 'pos.payment'

    def get_payment_summary(self, order_ids):
        orders = self.env['pos.order'].search([('id', 'in', order_ids)])
        payment_ids = self.env["pos.payment"].search([('pos_order_id', 'in', orders.ids)]).ids
        if payment_ids:
            self.env.cr.execute("""
                SELECT method.name, sum(amount) total
                FROM pos_payment AS payment,
                     pos_payment_method AS method
                WHERE payment.payment_method_id = method.id
                    AND payment.id IN %s
                GROUP BY method.name
                """, (tuple(payment_ids),))
            payments_summary = self.env.cr.dictfetchall()
        else:
            payments_summary = []
        return payments_summary


class PosSession(models.Model):
    _inherit = 'pos.session'

    def get_session_summary(self, session):
        if session:
            session = self.env['pos.session'].search([('id', '=', session)])
            order_ids = session.order_ids
            if order_ids:
                self.env.cr.execute("""
                    SELECT product.id, template.name, product.default_code as code, sum(qty) as qty, sum(line.price_subtotal_incl) as total
                    FROM product_product AS product,
                         pos_order_line AS line, product_template AS template
                    WHERE product.id = line.product_id AND template.id = product.product_tmpl_id
                        AND line.order_id IN %s
                    GROUP BY product.id, template.name, template.default_code
                    """, (tuple(order_ids.ids),))
                product_summary = self.env.cr.dictfetchall()
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
                    payments_summary = self.env.cr.dictfetchall()
                else:
                    payments_summary = []
            else:
                product_summary = []
                payments_summary = []
            session_summary = {
                'session_name': session.name,
                'start_date': session.start_at,
                'end_date': session.stop_at,
                'opening_balance': session.cash_register_balance_start,
                'closing_balance': session.cash_register_balance_end_real,
                'product_summary': product_summary,
                'payments_summary': payments_summary
            }
        return session_summary


class PosConfig(models.Model):
    _inherit = 'pos.config'

    def get_location_summary(self, location_id):
        location_quant = self.env['stock.quant'].search(
            [('location_id', '=', int(location_id))])
        location_summary = []
        for quant in location_quant.filtered(lambda x: x.product_id.available_in_pos):
            values = {
                'product_id': quant.product_id.id,
                'product': quant.product_id.name,
                'quantity': quant.available_quantity,
            }
            location_summary.append(values)
        return location_summary
