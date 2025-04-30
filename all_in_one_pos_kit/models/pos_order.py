# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Haseen (odoo@cybrosys.com)
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
from datetime import datetime

try:
    import qrcode
except ImportError:
    qrcode = None
try:
    import base64
except ImportError:
    base64 = None


class PosOrder(models.Model):
    """Inherited the pos_order class to add filed and function to calculate pos
    order details in the dashboard menu"""
    _inherit = 'pos.order'
    is_exchange = fields.Boolean(string='Exchange',
                                 help='Will enable when create an exchange'
                                      'order')

    @api.model
    def pos_exchange_order(self, order_id):
        """Mark order a exchanged"""
        self.browse(order_id).is_exchange = True

    @api.model
    def get_invoice(self, id):
        """Retrieve the corresponding invoice details based on the provided ID.
        Args:
        id (int): The ID of the invoice.
        Returns:
        dict: A dictionary containing the invoice details.
        """
        pos_id = self.search([('pos_reference', '=', id)])
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        invoice_id = self.env['account.move'].search(
            [('invoice_origin', '=', pos_id.name)])
        return {
            'invoice_id': invoice_id.id,
            'invoice_name': invoice_id.name,
            'base_url': base_url,
            'is_qr_code': invoice_id.account_barcode}

    @api.model
    def get_department(self, option):
        """
        Retrieve sales data based on the specified option for POS (Point of Sale) orders.

        This method generates a sales report based on the given option, which can be
        'pos_hourly_sales', 'pos_monthly_sales', or default to annual sales grouped by month.
        The report is generated for the current company and for the current month or year
        as appropriate.

        Args:
            option (str): The type of sales report to generate. Possible values are:
                          - 'pos_hourly_sales': Hourly sales data for the current month.
                          - 'pos_monthly_sales': Daily sales data for the current month.
                          - Any other value: Monthly sales data for the current year.

        Returns:
            list: A list containing three elements:
                  - order (list): A list of total sales amounts.
                  - today (list): A list of time labels corresponding to the sales amounts
                                  (hours, days, or months).
                  - label (str): A string indicating the type of time label used ('HOURS', 'DAYS', 'MONTHS').

        Raises:
            Exception: If an error occurs while executing the database query.
        """
        company_id = self.env.company.id
        if option == 'pos_hourly_sales':
            user_tz = self.env.user.tz if self.env.user.tz else pytz.UTC
            query = ('''select  EXTRACT(hour FROM date_order at time zone 
            'utc' at time zone '{}')  as date_month,sum(amount_total) from 
            pos_order where EXTRACT(month FROM date_order::date) =
             EXTRACT(month FROM CURRENT_DATE) AND pos_order.company_id = '''
                     + str(company_id) + ''' group by date_month ''')
            query = query.format(user_tz)
            label = 'HOURS'
        elif option == 'pos_monthly_sales':
            query = '''select  date_order::date as date_month,sum(amount_total)
             from pos_order where EXTRACT(month FROM date_order::date) = EXTRACT
             (month FROM CURRENT_DATE) AND pos_order.company_id = ''' + str(
                company_id) + '''  group by date_month '''
            label = 'DAYS'
        else:
            query = '''select TO_CHAR(date_order,'MON')date_month,
            sum(amount_total) from pos_order where EXTRACT(year FROM 
            date_order::date) = EXTRACT(year FROM CURRENT_DATE) AND 
            pos_order.company_id = ''' + str( company_id) + ''' group by 
            date_month'''
            label = 'MONTHS'
        self._cr.execute(query)
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
        """
        Retrieve various details related to POS (Point of Sale) operations for the current company.

        This method fetches payment details, salesperson performance, and session statuses
        from the POS system. The details include the total amount collected per payment method,
        the total sales and order count per salesperson, and the status of active POS sessions.

        Returns:
            dict: A dictionary containing the following keys:
                - 'payment_details': A list of tuples, each containing the name of the payment
                                     method and the total amount collected, formatted with the
                                     company currency symbol.
                - 'salesperson': A list of tuples, each containing the name of the salesperson,
                                 the total sales amount formatted with the company currency
                                 symbol, and the number of orders processed.
                - 'selling_product': A list of dictionaries, each representing a POS session with
                                     its name and status (e.g., 'Closed', 'Opened').

        Raises:
            Exception: If an error occurs during database queries or data formatting.
        """
        company_id = self.env.company.id
        cr = self._cr
        cr.execute(
            """select pos_payment_method.name,sum(amount) from pos_payment inner
             join pos_payment_method on pos_payment_method.id=pos_payment.
             payment_method_id group by pos_payment_method.name ORDER 
            BY sum(amount) DESC; """)
        payment_details = cr.fetchall()
        cr.execute(
            '''select hr_employee.name,sum(pos_order.amount_paid) as total,
            count(pos_order.amount_paid) as orders from pos_order inner join
             hr_employee on pos_order.user_id = hr_employee.user_id 
            where pos_order.company_id =''' + str(
                company_id) + '''GROUP BY hr_employee.name order by total 
                DESC;''')
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
            '''select DISTINCT(product_template.name) as product_name,sum(qty) 
            as total_quantity from pos_order_line inner join product_product on
             product_product.id=pos_order_line.product_id inner join 
       product_template on product_product.product_tmpl_id = product_template.id
         where pos_order_line.company_id =''' + str(
                company_id) + ''' group by product_template.id ORDER 
               BY total_quantity DESC Limit 10 ''')
        sessions = self.env['pos.config'].search([])
        sessions_list = []
        dict = {
            'closing_control': 'Closed',
            'opened': 'Opened',
            'new_session': 'New Session',
            'opening_control': "Opening Control"
        }
        for session in sessions:
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
        """
        Retrieve details about sales, refunds, and POS sessions for the current date.

        This method calculates various metrics related to POS (Point of Sale) operations,
        including the total sales amount, number of orders, refund counts, and session
        information. It also formats the total sales with appropriate magnitude suffixes
        (e.g., K for thousand, M for million) for easier readability.

        Returns:
            dict: A dictionary containing the following keys:
                - 'total_sale': A formatted string representing the total sales amount with
                                an appropriate suffix (e.g., '1.2K' for 1200).
                - 'total_order_count': An integer representing the total number of orders.
                - 'total_refund_count': An integer representing the total number of refund orders.
                - 'total_session': An integer representing the total number of POS sessions.
                - 'today_refund_total': An integer representing the number of refunds made today.
                - 'today_sale': An integer representing the number of sales made today.

        Raises:
            Exception: If an error occurs while querying the database or calculating the metrics.
        """
        default_date = datetime.today().date()
        pos_order = self.env['pos.order'].search([])
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
        pos_session = self.env['pos.session'].search([])
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
    def get_the_top_customer(self):
        """
        Retrieve the top 10 customers based on the total amount spent in POS (Point of Sale) orders.

        This method fetches the top customers who have made the highest total payments for
        POS orders in the current company. It returns a list of the top 10 customers along
        with the corresponding total amounts they have spent.

        Returns:
            list: A list containing two elements:
                - order (list): A list of total amounts spent by the top 10 customers.
                - day (list): A list of customer names corresponding to the total amounts.

        Raises:
            Exception: If an error occurs during the database query execution.
        """
        company_id = self.env.company.id
        query = '''select res_partner.name as customer,pos_order.partner_id,
        sum(pos_order.amount_paid) as amount_total from pos_order inner join
         res_partner on res_partner.id = pos_order.partner_id where pos_order
         .company_id = ''' + str(
            company_id) + ''' GROUP BY pos_order.partner_id,
                res_partner.name  ORDER BY amount_total  DESC LIMIT 10;'''
        self._cr.execute(query)
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
        """
        Retrieve the top 10 products based on the total quantity sold in POS (Point of Sale) orders.

        This method fetches the top-selling products in terms of quantity for the current company
        and returns a list of the top 10 products along with their corresponding total quantities sold.

        Returns:
            list: A list containing two elements:
                - total_quantity (list): A list of quantities for the top 10 products.
                - product_name (list): A list of product names corresponding to the quantities.

        Raises:
            Exception: If an error occurs during the database query execution.
        """
        company_id = self.env.company.id
        query = '''select DISTINCT(product_template.name) as product_name,
        sum(qty) as total_quantity from 
               pos_order_line inner join product_product on product_product.
               id=pos_order_line.product_id inner join 
               product_template on product_product.product_tmpl_id = 
               product_template.id where pos_order_line.company_id = ''' + str(
            company_id) + ''' group by product_template.id ORDER 
               BY total_quantity DESC Limit 10 '''
        self._cr.execute(query)
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
        """
        Retrieve the top product categories based on the total quantity sold in POS (Point of Sale) orders.

        This method fetches the top-selling product categories for the current company and returns
        a list containing the total quantities sold for each category, sorted in descending order.

        Returns:
            list: A list containing two elements:
                - total_quantity (list): A list of quantities for the top-selling product categories.
                - product_categ (list): A list of category names corresponding to the quantities.

        Raises:
            Exception: If an error occurs during the database query execution.
        """
        company_id = self.env.company.id
        query = ('''select DISTINCT(product_category.complete_name) as
         product_category,sum(qty) as total_quantity from pos_order_line inner
         join product_product on product_product.id=pos_order_line.product_id 
         inner join product_template on product_product.product_tmpl_id =
         product_template.id inner join product_category on product_category.id
         = product_template.categ_id where pos_order_line.company_id = ''' +
        str(company_id) + ''' group by product_category ORDER BY 
        total_quantity DESC ''')
        self._cr.execute(query)
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
    def create_from_ui(self, orders, draft=False):
        """
        Create POS orders from the UI and send SMS notifications to customers if configured.

        This method extends the default behavior of creating POS orders from the user interface.
        After the orders are created, it checks for configurations that allow SMS notifications
        and sends an SMS to the customer using Twilio if applicable. The SMS message details
        are also logged in the 'pos.greetings' model.

        Args:
            orders (list): A list of order dictionaries coming from the POS UI.

        Returns:
            list: The result from the parent 'create_from_ui' method, representing the
            created orders.

        Raises:
            Exception: If an error occurs while sending the SMS, it is caught and suppressed.
        """
        res = super(PosOrder, self).create_from_ui(orders, draft)
        ids = []
        for line in res:
            if line['id']:
                ids.append(line['id'])
        backend_order = self.search([('id', 'in', ids)])
        if backend_order:
            for pos_order in backend_order:
                config_id = pos_order.session_id.config_id
                if config_id.customer_msg:
                    if pos_order.partner_id.phone:
                        try:
                            customer_phone = str(pos_order.partner_id.phone)
                            twilio_number = config_id.twilio_number
                            auth_token = config_id.auth_token
                            account_sid = config_id.account_sid
                            body = config_id.sms_body
                            client = Client(account_sid, auth_token)
                            client.messages.create(
                                body=body,
                                from_=twilio_number,
                                to=customer_phone
                            )
                            pos_greeting_obj = self.env['pos.greetings']
                            pos_greeting_obj.create({
                                'customer_id': pos_order.partner_id.id,
                                'order_id': pos_order.id,
                                'auth_token': auth_token,
                                'twilio_number': twilio_number,
                                'to_number': customer_phone,
                                'session_id': pos_order.session_id.id,
                                'sms_body': body,
                                'send_sms': True,
                            })
                        except:
                            pass
            return res
