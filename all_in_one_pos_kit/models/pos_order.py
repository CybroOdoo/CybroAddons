# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
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
from datetime import datetime
from odoo import api, fields, models


class PosOrder(models.Model):
    """ Inherited class of pos dashboard to add features of dashboard"""
    _inherit = 'pos.order'

    invoice_number = fields.Char(
        compute='_compute_invoice_number',
        help="Number of the posted invoice of this order, shown on the "
             "receipt.")

    @api.depends('account_move', 'account_move.state', 'account_move.name')
    def _compute_invoice_number(self):
        """Only a posted invoice has a real number (drafts are named '/')."""
        for order in self:
            move = order.account_move
            order.invoice_number = (
                move.name if move and move.state == 'posted' else False)

    @api.model
    def _load_pos_data_fields(self, config):
        """Send the invoice number to the POS so the receipt can print it."""
        fields_list = super()._load_pos_data_fields(config)
        # An empty list means that every field is loaded already.
        if fields_list and 'invoice_number' not in fields_list:
            fields_list = list(fields_list) + ['invoice_number']
        return fields_list

    def action_pos_order_paid(self):
        """Send the greeting message once the order is paid"""
        res = super().action_pos_order_paid()
        self._create_and_send_greetings()
        return res

    def _create_and_send_greetings(self):
        """Create a POS greeting for each paid order that has a customer
        with a phone number, then send it when greetings are enabled."""
        params = self.env['ir.config_parameter'].sudo()
        if not params.get_param('all_in_one_pos_kit.customer_msg'):
            return
        body = params.get_param('all_in_one_pos_kit.sms_body')
        twilio_number = params.get_param('all_in_one_pos_kit.twilio_number')
        greetings = self.env['pos.greetings'].sudo()
        for order in self:
            partner = order.partner_id
            number = partner.phone
            if not (body and partner and number) or greetings.search_count(
                    [('order_id', '=', order.id)]):
                continue
            greetings |= greetings.create({
                'customer_id': partner.id,
                'order_id': order.id,
                'session_id': order.session_id.id,
                'to_number': number,
                'twilio_number': twilio_number,
                'sms_body': body,
            })
        greetings.action_send_greeting()

    @api.model
    def get_department(self, option):
        """ Function to get the order details of company wise"""
        company_id = self.env.company.id
        params = [company_id]
        if option == 'pos_hourly_sales':
            user_tz = self.env.user.tz or 'UTC'
            query = """
                SELECT EXTRACT(hour FROM date_order AT TIME ZONE 'utc'
                               AT TIME ZONE %s) AS date_month,
                       SUM(amount_total)
                  FROM pos_order
                 WHERE EXTRACT(month FROM date_order::date) =
                       EXTRACT(month FROM CURRENT_DATE)
                   AND pos_order.company_id = %s
                 GROUP BY date_month
            """
            params = [user_tz, company_id]
            label = 'HOURS'
        elif option == 'pos_monthly_sales':
            query = """
                SELECT date_order::date AS date_month, SUM(amount_total)
                  FROM pos_order
                 WHERE EXTRACT(month FROM date_order::date) =
                       EXTRACT(month FROM CURRENT_DATE)
                   AND pos_order.company_id = %s
                 GROUP BY date_month
            """
            label = 'DAYS'
        else:
            query = """
                SELECT TO_CHAR(date_order, 'MON') AS date_month,
                       SUM(amount_total)
                  FROM pos_order
                 WHERE EXTRACT(year FROM date_order::date) =
                       EXTRACT(year FROM CURRENT_DATE)
                   AND pos_order.company_id = %s
                 GROUP BY date_month
            """
            label = 'MONTHS'
        self.env.cr.execute(query, params)
        docs = self.env.cr.dictfetchall()
        order = [record.get('sum') for record in docs]
        today = [record.get('date_month') for record in docs]
        return [order, today, label]

    @api.model
    def get_details(self):
        """ Function to get the payment details"""
        company_id = self.env.company.id
        cr = self.env.cr
        cr.execute(
            """
            SELECT pos_payment_method.name ->> 'en_US', SUM(amount)
              FROM pos_payment
             INNER JOIN pos_payment_method
                     ON pos_payment_method.id = pos_payment.payment_method_id
             GROUP BY pos_payment_method.name
             ORDER BY SUM(amount) DESC
            """)
        payment_details = cr.fetchall()
        cr.execute(
            """
            SELECT hr_employee.name, SUM(pos_order.amount_paid) AS total,
                   COUNT(pos_order.amount_paid) AS orders
              FROM pos_order
             INNER JOIN hr_employee
                     ON pos_order.user_id = hr_employee.user_id
             WHERE pos_order.company_id = %s
             GROUP BY hr_employee.name
             ORDER BY total DESC
            """, (company_id,))
        salesperson = cr.fetchall()
        total_sales = []
        for rec in salesperson:
            rec = list(rec)
            sym_id = rec[1]
            company = self.env.company
            if company.currency_id.position == 'after':
                rec[1] = "%s %s" % (sym_id, company.currency_id.symbol)
            else:
                rec[1] = "%s %s" % (company.currency_id.symbol, sym_id)
            rec = tuple(rec)
            total_sales.append(rec)
        sessions = self.env['pos.config'].search([], limit=1000)
        sessions_list = []
        dict = {
            'opened': 'Opened',
            'opening_control': "Opening Control"
        }
        for session in sessions:
            st = dict.get(session.pos_session_state)
            if st is None:
                sessions_list.append({
                    'session': session.name,
                    'status': 'Closed'
                })
            else:
                sessions_list.append({
                    'session': session.name,
                    'status': dict.get(session.pos_session_state)
                })
        payments = []
        for rec in payment_details:
            rec = list(rec)
            sym_id = rec[1]
            company = self.env.company
            if company.currency_id.position == 'after':
                rec[1] = "%s %s" % (sym_id, company.currency_id.symbol)
            else:
                rec[1] = "%s %s" % (company.currency_id.symbol, sym_id)
            rec = tuple(rec)
            payments.append(rec)
        return {
            'payment_details': payments,
            'salesperson': total_sales,
            'selling_product': sessions_list,
        }

    @api.model
    def get_refund_details(self):
        """ Function to get the Refund details"""
        default_date = datetime.today().date()
        pos_order = self.env['pos.order'].search([], limit=100000)
        total = 0
        today_refund_total = 0
        total_order_count = 0
        total_refund_count = 0
        today_sale = 0
        for rec in pos_order:
            if rec.amount_total < 0.0 and rec.date_order.date() == default_date:
                today_refund_total = today_refund_total + 1
            total_sales = rec.amount_total
            total = total + total_sales
            total_order_count = total_order_count + 1
            if rec.date_order.date() == default_date:
                today_sale = today_sale + 1
            if rec.amount_total < 0.0:
                total_refund_count = total_refund_count + 1
        magnitude = 0
        while abs(total) >= 1000:
            magnitude += 1
            total /= 1000.0
        # add more suffixes if you need them
        val = '%.2f%s' % (total, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])
        pos_session = self.env['pos.session'].search([], limit=100000)
        total_session = 0
        for record in pos_session:
            total_session = total_session + 1
        return {
            'total_sale': val,
            'total_order_count': total_order_count,
            'total_refund_count': total_refund_count,
            'total_session': total_session,
            'today_refund_total': today_refund_total,
            'today_sale': today_sale,
        }

    @api.model
    def get_the_top_customer(self, ):
        """ To get the top Customer details"""
        company_id = self.env.company.id
        self.env.cr.execute("""
            SELECT res_partner.name AS customer, pos_order.partner_id,
                   SUM(pos_order.amount_paid) AS amount_total
              FROM pos_order
             INNER JOIN res_partner ON res_partner.id = pos_order.partner_id
             WHERE pos_order.company_id = %s
             GROUP BY pos_order.partner_id, res_partner.name
             ORDER BY amount_total DESC
             LIMIT 10
        """, (company_id,))
        docs = self.env.cr.dictfetchall()

        order = []
        for record in docs:
            order.append(record.get('amount_total'))
        day = []
        for record in docs:
            day.append(record.get('customer'))
        final = [order, day]
        return final

    @api.model
    def get_the_top_products(self):
        """ Function to get the top products"""
        company_id = self.env.company.id
        self.env.cr.execute("""
            SELECT product_template.name ->> 'en_US' AS product_name,
                   SUM(qty) AS total_quantity
              FROM pos_order_line
             INNER JOIN product_product
                     ON product_product.id = pos_order_line.product_id
             INNER JOIN product_template
                     ON product_product.product_tmpl_id = product_template.id
             WHERE pos_order_line.company_id = %s
             GROUP BY product_template.id
             ORDER BY total_quantity DESC
             LIMIT 10
        """, (company_id,))
        top_product = self.env.cr.dictfetchall()
        total_quantity = []
        for record in top_product:
            total_quantity.append(record.get('total_quantity'))
        product_name = []
        for record in top_product:
            product_name.append(record.get('product_name'))
        final = [total_quantity, product_name]
        return final

    @api.model
    def get_the_top_categories(self):
        """ Function to get the top Product categories"""
        company_id = self.env.company.id
        self.env.cr.execute("""
            SELECT product_category.complete_name AS product_category,
                   SUM(qty) AS total_quantity
              FROM pos_order_line
             INNER JOIN product_product
                     ON product_product.id = pos_order_line.product_id
             INNER JOIN product_template
                     ON product_product.product_tmpl_id = product_template.id
             INNER JOIN product_category
                     ON product_category.id = product_template.categ_id
             WHERE pos_order_line.company_id = %s
             GROUP BY product_category
             ORDER BY total_quantity DESC
        """, (company_id,))
        top_product = self.env.cr.dictfetchall()
        total_quantity = []
        for record in top_product:
            total_quantity.append(record.get('total_quantity'))
        product_categ = []
        for record in top_product:
            product_categ.append(record.get('product_category'))
        final = [total_quantity, product_categ]
        return final
