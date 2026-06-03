# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
import logging
from twilio.rest import Client
from datetime import datetime
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    """Inherited the pos_order class to add filed and function to calculate pos
    order details in the dashboard menu"""
    _inherit = 'pos.order'

    exchange = fields.Boolean(string='Exchange',
                              help='Enable if the order contain is exchange '
                                   'product')
    sale_barcode = fields.Char(string='Barcode',
                               help='Barcode associated with the pos order.')

    def set_pos_exchange_order(self):
        """Mark order a exchanged"""
        self.exchange = True
        return

    @api.model
    def get_department(self, option):
        """ Function to get the order details of company wise"""

        company_id = self.env.company.id
        user_tz = self.env.user.tz or 'UTC'
        config_ids = self.env.user.pos_config_ids.ids
        config_filter = ""
        params = [user_tz, company_id]
        if config_ids:
            config_filter = " AND pos_order.config_id IN %s"
            params.append(tuple(config_ids))

        if option == 'pos_hourly_sales':
            query = '''select  EXTRACT(hour FROM date_order at time zone 'utc' at time zone %s) 
                       as date_month,sum(amount_total) from pos_order where  
                       EXTRACT(month FROM date_order::date) = EXTRACT(month FROM CURRENT_DATE) 
                       AND pos_order.company_id = %s''' + config_filter + ''' group by date_month '''
            label = 'HOURS'
        elif option == 'pos_monthly_sales':
            query = '''select  date_order::date as date_month,sum(amount_total) from pos_order where 
             EXTRACT(month FROM date_order::date) = EXTRACT(month FROM CURRENT_DATE) AND pos_order.company_id = %s''' + config_filter + '''  group by date_month '''
            params = [company_id]
            if config_ids:
                params.append(tuple(config_ids))
            label = 'DAYS'
        else:
            query = '''select TO_CHAR(date_order,'MON')date_month,sum(amount_total) from pos_order where
             EXTRACT(year FROM date_order::date) = EXTRACT(year FROM CURRENT_DATE) AND pos_order.company_id = %s''' + config_filter + ''' group by date_month'''
            params = [company_id]
            if config_ids:
                params.append(tuple(config_ids))
            label = 'MONTHS'
        self._cr.execute(query, params)
        docs = self._cr.dictfetchall()
        order = []
        for record in docs:
            order.append(record.get('sum'))
        today = []
        for record in docs:
            today.append(record.get('date_month'))
        final = [order, today, label]
        return final

    @api.model
    def get_details(self):
        """ Function to get the payment details"""
        company_id = self.env.company.id
        cr = self._cr
        config_ids = self.env.user.pos_config_ids.ids
        config_filter = ""
        params = []
        if config_ids:
            config_filter = " AND pos_order.config_id IN %s"
            params.append(tuple(config_ids))

        cr.execute(
            """select pos_payment_method.name ->>'en_US',sum(amount) from pos_payment inner join pos_payment_method on 
            pos_payment_method.id=pos_payment.payment_method_id inner join pos_order on pos_order.id = pos_payment.pos_order_id
            where pos_order.company_id = %s""" + config_filter + """ group by pos_payment_method.name ORDER 
            BY sum(amount) DESC; """, [company_id] + params)
        payment_details = cr.fetchall()
        cr.execute(
            '''select hr_employee.name,sum(pos_order.amount_paid) as total,count(pos_order.amount_paid) as orders 
            from pos_order inner join hr_employee on pos_order.user_id = hr_employee.user_id 
            where pos_order.company_id = %s''' + config_filter + ''' GROUP BY hr_employee.name order by total DESC;''', [company_id] + params)
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
        cr.execute(
            '''select DISTINCT(product_template.name) as product_name,sum(qty) as total_quantity from 
       pos_order_line inner join product_product on product_product.id=pos_order_line.product_id inner join 
       product_template on product_product.product_tmpl_id = product_template.id  where pos_order_line.company_id =''' + str(
                company_id) + ''' group by product_template.id ORDER 
       BY total_quantity DESC Limit 10 ''')
        # Filter shops by Allowed Pos
        domain = []
        if self.env.user.pos_config_ids:
            domain = [('id', 'in', self.env.user.pos_config_ids.ids)]
        sessions = self.env['pos.config'].search(domain)
        sessions_list = []
        dict = {
            'opened': 'Opened',
            'opening_control': "Opening Control"
        }
        for session in sessions:
            st = dict.get(session.pos_session_state)
            if st == None:
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
        domain = []
        if self.env.user.pos_config_ids:
            domain = [('config_id', 'in', self.env.user.pos_config_ids.ids)]
        pos_order = self.env['pos.order'].search(domain)
        total = 0
        today_refund_total = 0
        total_order_count = 0
        total_refund_count = 0
        today_sale = 0
        a = 0
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
        # Filter sessions by Allowed Pos
        session_domain = []
        if self.env.user.pos_config_ids:
            session_domain = [('config_id', 'in', self.env.user.pos_config_ids.ids)]
        pos_session = self.env['pos.session'].search(session_domain)
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
        config_ids = self.env.user.pos_config_ids.ids
        config_filter = ""
        params = [company_id]
        if config_ids:
            config_filter = " AND po.config_id IN %s"
            params.append(tuple(config_ids))

        query = """
            SELECT 
                rp.name AS customer,
                po.partner_id,
                SUM(po.amount_paid) AS amount_total
            FROM pos_order po
            INNER JOIN res_partner rp ON rp.id = po.partner_id
            WHERE po.company_id = %s
        """ + config_filter + """
            GROUP BY po.partner_id, rp.name
            ORDER BY amount_total DESC
            LIMIT 10;
        """
        self._cr.execute(query, params)
        docs = self._cr.dictfetchall()
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
        config_ids = self.env.user.pos_config_ids.ids
        config_filter = ""
        params = [company_id]
        if config_ids:
            config_filter = " AND pos_order.config_id IN %s"
            params.append(tuple(config_ids))

        query = '''select DISTINCT(product_template.name)->>'en_US' as product_name,sum(qty) as total_quantity from 
       pos_order_line inner join product_product on product_product.id=pos_order_line.product_id inner join 
       product_template on product_product.product_tmpl_id = product_template.id 
       inner join pos_order on pos_order.id = pos_order_line.order_id
       where pos_order_line.company_id = %s''' + config_filter + ''' group by product_template.id ORDER 
       BY total_quantity DESC Limit 10 '''
        self._cr.execute(query, params)
        top_product = self._cr.dictfetchall()
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
        config_ids = self.env.user.pos_config_ids.ids
        config_filter = ""
        params = [company_id]
        if config_ids:
            config_filter = " AND pos_order.config_id IN %s"
            params.append(tuple(config_ids))

        query = '''select DISTINCT(product_category.complete_name) as product_category,sum(qty) as total_quantity 
        from pos_order_line inner join product_product on product_product.id=pos_order_line.product_id  inner join 
        product_template on product_product.product_tmpl_id = product_template.id inner join product_category on 
        product_category.id =product_template.categ_id 
        inner join pos_order on pos_order.id = pos_order_line.order_id
        where pos_order_line.company_id = %s''' + config_filter + ''' group by product_category ORDER BY total_quantity DESC '''
        self._cr.execute(query, params)
        top_product = self._cr.dictfetchall()
        total_quantity = []
        for record in top_product:
            total_quantity.append(record.get('total_quantity'))
        product_categ = []
        for record in top_product:
            product_categ.append(record.get('product_category'))
        final = [total_quantity, product_categ]
        return final

    @api.model
    def get_invoice(self, id):
        """Retrieve invoice information based on a POS reference ID.
    This method searches for a POS record with the specified reference ID. It
    then retrieves the associated invoice based on the name matching the
    reference. The invoice details, including ID, name, base URL, and account
    barcode, are returned as a dictionary.
    :param id: The POS reference ID to search for.
    :return: A dictionary containing the invoice details.
    :rtype: dict"""
        pos_order = self.search([('pos_reference', '=', id)], limit=1)
        invoice_id = self.env['account.move']
        if pos_order:
            invoice_id = self.env['account.move'].search(
                [('ref', '=', pos_order.name)], limit=1)
        return {'invoice_id': invoice_id.id, 'invoice_name': invoice_id.name,
                'base_url': self.env['ir.config_parameter'].get_param(
                    'web.base.url'), 'barcode': invoice_id.account_barcode}

    @api.model
    def sync_from_ui(self, orders):
        """Override sync_from_ui to send SMS greetings to customers
           after POS order validation using Twilio."""
        res = super().sync_from_ui(orders)
        order_ids = [order['id'] for order in res.get('pos.order', [])]
        if order_ids:
            pos_orders = self.browse(order_ids)
            params = self.env['ir.config_parameter'].sudo()
            customer_msg = params.get_param(
                'all_in_one_pos_kit.customer_msg')
            if customer_msg:
                twilio_auth_token = params.get_param(
                    'all_in_one_pos_kit.twilio_auth_token')
                account_sid = params.get_param(
                    'all_in_one_pos_kit.account_sid')
                twilio_number = params.get_param(
                    'all_in_one_pos_kit.twilio_number')
                sms_body = params.get_param(
                    'all_in_one_pos_kit.sms_body')
                for pos_order in pos_orders:
                    # Check both phone and mobile
                    customer_phone = pos_order.partner_id.mobile or pos_order.partner_id.phone
                    if customer_phone:
                        try:
                            customer_phone = str(customer_phone)
                            client = Client(account_sid,
                                            twilio_auth_token)
                            client.messages.create(
                                body=sms_body,
                                from_=twilio_number,
                                to=customer_phone
                            )
                            send_success = True
                        except Exception as e:
                            _logger.error("Twilio SMS sending failed: %s", e)
                            send_success = False

                        # Create log record regardless of success to show effort in Odoo
                        self.env['pos.greetings'].create({
                            'customer_id': pos_order.partner_id.id,
                            'order_id': pos_order.id,
                            'twilio_auth_token': twilio_auth_token,
                            'twilio_number': twilio_number,
                            'to_number': customer_phone,
                            'session_id': pos_order.session_id.id,
                            'sms_body': sms_body,
                            'send_sms': send_success,
                        })
        return res


class PosOrderLine(models.Model):
    """Inherit the class pos_order_line"""
    _inherit = "pos.order.line"

    @api.model
    def get_product_details(self, ids):
        """Function to get the product details"""
        return [{'product_id': rec.product_id.id, 'name': rec.product_id.name,
                 'qty': rec.qty}
                for rec in self.env['pos.order.line'].browse(ids)]
