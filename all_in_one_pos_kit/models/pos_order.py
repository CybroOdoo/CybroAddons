# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra MP (odoo@cybrosys.com)
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
import pytz
from twilio.rest import Client
from odoo import api, fields, models


class PosOrder(models.Model):
    """Inherited the pos_order class to add filed and function to calculate pos
    order details in the dashboard menu"""
    _inherit = 'pos.order'

    exchange = fields.Boolean(string='Exchange',
                              help='Enable if the order contain is exchange '
                                   'product')
    sale_barcode = fields.Char(string='Barcode',
                               help='Barcode associated with the pos order.')

    def get_pos_exchange_order(self):
        """Mark order a exchanged"""
        self.exchange = True
        return

    @api.model
    def get_department(self, option):
        """Function to filter the POs sales report chart"""
        company_id = self.env.company.id
        if option == 'pos_hourly_sales':
            query = '''select  EXTRACT(hour FROM date_order at time zone 'utc' at time zone '{}') 
                           as date_month,sum(amount_total) from pos_order where  
                           EXTRACT(month FROM date_order::date) = EXTRACT(month FROM CURRENT_DATE) 
                           AND pos_order.company_id = ''' + str(
                company_id) + ''' group by date_month '''
            query = query.format(
                self.env.user.tz if self.env.user.tz else pytz.UTC)
            label = 'HOURS'
        elif option == 'pos_monthly_sales':
            query = '''select  date_order::date as date_month,sum(amount_total) from pos_order where 
                 EXTRACT(month FROM date_order::date) = EXTRACT(month FROM CURRENT_DATE) AND pos_order.company_id = ''' + str(
                company_id) + '''  group by date_month '''
            label = 'DAYS'
        else:
            query = '''select TO_CHAR(date_order,'MON')date_month,sum(amount_total) from pos_order where
                 EXTRACT(year FROM date_order::date) = EXTRACT(year FROM CURRENT_DATE) AND pos_order.company_id = ''' + str(
                company_id) + ''' group by date_month'''
            label = 'MONTHS'
        self._cr.execute(query)
        docs = self._cr.dictfetchall()
        order = []
        today = []
        for record in docs:
            order.append(record.get('sum'))
            today.append(record.get('date_month'))
        return [order, today, label]

    @api.model
    def get_details(self):
        """Function to get payment details,session details and sales person
        details"""
        company_id = self.env.company
        self._cr.execute('''select pos_payment_method.name ->>'en_US',sum(amount) 
                        from pos_payment inner join pos_payment_method on 
                        pos_payment_method.id=pos_payment.payment_method_id 
                        where pos_payment.company_id = ''' + str(company_id.id) + " " + '''
                        group by pos_payment_method.name ORDER 
                        BY sum(amount) DESC; ''')
        payment_details = self._cr.fetchall()
        self._cr.execute('''select hr_employee.name,sum(pos_order.amount_paid) 
                        as total,count(pos_order.amount_paid) as orders from 
                        pos_order inner join hr_employee on pos_order.user_id = 
                        hr_employee.user_id where pos_order.company_id =''' + str(
            company_id.id) + " " + '''GROUP BY hr_employee.name order by total DESC;''')
        salesperson = self._cr.fetchall()
        payments = []
        for rec in payment_details:
            rec = list(rec)
            if company_id.currency_id.position == 'after':
                rec[1] = "%s %s" % (rec[1], company_id.currency_id.symbol)
            else:
                rec[1] = "%s %s" % (company_id.currency_id.symbol, rec[1])
            payments.append(tuple(rec))
        total_sales = []
        for rec in salesperson:
            rec = list(rec)
            if company_id.currency_id.position == 'after':
                rec[1] = "%s %s" % (rec[1], company_id.currency_id.symbol)
            else:
                rec[1] = "%s %s" % (company_id.currency_id.symbol, rec[1])
            total_sales.append(tuple(rec))
        sessions_list = []
        session = {'opened': 'Opened', 'opening_control': "Opening Control"}
        for session_id in self.env['pos.config'].search([]):
            if session.get(session_id.pos_session_state) is None:
                sessions_list.append({'session': session_id.name,
                                      'status': 'Closed'})
            else:
                sessions_list.append({'session': session_id.name,
                                      'status': session.get(
                                          session_id.pos_session_state)})
        return {'payment_details': payments, 'salesperson': total_sales,
                'selling_product': sessions_list}

    @api.model
    def get_refund_details(self):
        """Function to get total count of orders,session and refund orders"""
        total = sum(self.env['pos.order'].search([]).mapped('amount_total'))
        today_refund_total = 0
        today_sale = 0
        for pos_order_id in self.env['pos.order'].search([]):
            if pos_order_id.date_order.date() == fields.date.today():
                today_sale = today_sale + 1
                if pos_order_id.amount_total < 0.0:
                    today_refund_total = today_refund_total + 1
        magnitude = 0
        while abs(total) >= 1000:
            magnitude += 1
            total /= 1000.0
        # add more suffixes if you need them
        val = '%.2f%s' % (total, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])
        return {
            'total_sale': val,
            'total_order_count': self.env['pos.order'].search_count([]),
            'total_refund_count': self.env['pos.order'].search_count(
                [('amount_total', '<', 0.0)]),
            'total_session': self.env['pos.session'].search_count([]),
            'today_refund_total': today_refund_total,
            'today_sale': today_sale,
        }

    @api.model
    def get_the_top_customer(self):
        """Function to get top 10 customer in pos"""
        self._cr.execute('''select res_partner.name as customer,pos_order.partner_id,sum(pos_order.amount_paid) as amount_total from pos_order 
            inner join res_partner on res_partner.id = pos_order.partner_id where pos_order.company_id = ''' + str(
            self.env.company.id) + ''' GROUP BY pos_order.partner_id,
            res_partner.name  ORDER BY amount_total  DESC LIMIT 10;''')
        top_customer = self._cr.dictfetchall()
        order = []
        day = []
        for record in top_customer:
            order.append(record.get('amount_total'))
            day.append(record.get('customer'))
        return [order, day]

    @api.model
    def get_the_top_products(self):
        """Function to get top 10 product in """

        self._cr.execute('''select DISTINCT(product_template.name)->>'en_US' as product_name,sum(qty) as total_quantity from 
           pos_order_line inner join product_product on product_product.id=pos_order_line.product_id inner join 
           product_template on product_product.product_tmpl_id = product_template.id where pos_order_line.company_id = ''' + str(
            self.env.company.id) + ''' group by product_template.id ORDER 
           BY total_quantity DESC Limit 10 ''')
        top_product = self._cr.dictfetchall()
        total_quantity = []
        product_name = []
        for record in top_product:
            total_quantity.append(record.get('total_quantity'))
            product_name.append(record.get('product_name'))
        return [total_quantity, product_name]

    @api.model
    def get_the_top_categories(self):
        """Function to get top categories in pos"""
        query = '''select DISTINCT(product_category.complete_name) as product_category,sum(qty) as total_quantity 
            from pos_order_line inner join product_product on product_product.id=pos_order_line.product_id  inner join 
            product_template on product_product.product_tmpl_id = product_template.id inner join product_category on 
            product_category.id =product_template.categ_id where pos_order_line.company_id = ''' + str(
            self.env.company.id) + ''' group by product_category ORDER BY total_quantity DESC '''
        self._cr.execute(query)
        top_categories = self._cr.dictfetchall()
        total_quantity = []
        product_categ = []
        for record in top_categories:
            total_quantity.append(record.get('total_quantity'))
            product_categ.append(record.get('product_category'))
        return [total_quantity, product_categ]

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
        invoice_id = self.env['account.move'].search(
            [('ref', '=', self.search([('pos_reference', '=', id)]).name)])
        return {'invoice_id': invoice_id.id, 'invoice_name': invoice_id.name,
                'base_url': self.env['ir.config_parameter'].get_param(
                    'web.base.url'), 'barcode': invoice_id.account_barcode}

    @api.model
    def create_from_ui(self, orders, draft=False):
        """Create POS orders from the user interface.
            This method is called to create POS orders based on the provided
            data from the user interface.
            :param orders: A list of dictionaries representing the POS orders.
            :param draft: Set to True if the orders should be created in the
            draft state.
            :returns: A list of dictionaries containing the created order
            details.
            """
        res = super(PosOrder, self).create_from_ui(orders)
        id = [line['id'] for line in res if line['id']]
        if backend_order := self.search([('id', 'in', id)]):
            for pos_order in backend_order:
                params = self.env['ir.config_parameter'].sudo()
                if params.get_param(
                        'pos.customer_msg') and pos_order.partner_id.phone:
                    try:
                        # Download the helper library from https://www.twilio.com/docs/python/install
                        Client(params.get_param('pos.account_sid'),
                               params.get_param(
                                   'pos.auth_token')).messages.create(
                            body=params.get_param('pos.sms_body'),
                            from_=params.get_param('pos.twilio_number'),
                            to=str(pos_order.partner_id.phone))
                        self.env['pos.greetings'].create({
                            'partner_id': pos_order.partner_id.id,
                            'order_id': pos_order.id,
                            'auth_token': params.get_param('pos.auth_token'),
                            'twilio_number': params.get_param(
                                'pos.twilio_number'),
                            'to_number': str(pos_order.partner_id.phone),
                            'session_id': pos_order.session_id.id,
                            'sms_body': params.get_param('pos.sms_body'),
                            'send_sms': True,
                        })
                    except Exception:
                        pass
            return res


class PosOrderLine(models.Model):
    """Inherit the class pos_order_line"""
    _inherit = "pos.order.line"

    def get_product_details(self, ids):
        """Function to get the product details"""
        return [{'product_id': rec.product_id.id, 'name': rec.product_id.name,
                 'qty': rec.qty}
                for rec in self.env['pos.order.line'].browse(ids)]
