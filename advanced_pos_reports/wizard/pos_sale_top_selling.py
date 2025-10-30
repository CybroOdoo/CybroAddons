# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models, _
from odoo.exceptions import ValidationError


class PosSaleTopSelling(models.TransientModel):
    """Get top_selling product,category,customer from pos"""
    _name = 'pos.sale.top.selling'
    _description = 'Point of Sale Top Selling Product/Category/Customer Report'

    start_date = fields.Datetime(string="Start Date",
                                 required=True,
                                 help="Starting date")
    end_date = fields.Datetime(string="End Date",
                               required=True,
                               help="Ending date")
    top_selling = fields.Selection(
        [('products', 'Products'), ('category', 'Categories'),
         ('customers', 'Customers')],
        string='Top Selling', default='products',
        help="Select Top selling categories, products and customers")
    no_of_products = fields.Integer(string="Number of Products",
                                    help="Number of products")
    no_of_categories = fields.Integer(string="No of Categories",
                                      help="Number of categories")
    no_of_customers = fields.Integer(string="Number of Customers",
                                     help="Number of customers")

    def action_generate_report(self):
        """Generate top_selling product, category, or customer report"""
        if self.start_date > self.end_date:
            raise ValidationError(_("The End Date must be greater than the Start Date"))

        data = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'top_selling': self.top_selling,
        }

        # POS Orders within date range
        orders = self.env['pos.order'].search([
            ('date_order', '>=', self.start_date),
            ('date_order', '<=', self.end_date),
            ('state', 'in', ['paid', 'invoiced', 'done'])
        ])

        if not orders:
            raise ValidationError(_("No POS orders found in the selected date range."))

        # -------------------------
        # Top Selling Products
        # -------------------------
        if self.top_selling == 'products':
            product_sales = {}
            for order in orders:
                for line in order.lines:
                    product_name = line.product_id.display_name
                    product_sales[product_name] = product_sales.get(product_name, 0.0) + line.price_subtotal

            sorted_products = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)
            top_products = sorted_products[:self.no_of_products or 10]
            products_list = [{'name': p[0], 'amount': p[1]} for p in top_products]

            data['products'] = products_list
            data['no_of_products'] = self.no_of_products

            return self.env.ref(
                'advanced_pos_reports.pos_top_selling_products_report'
            ).report_action([], data=data)

        # -------------------------
        # Top Selling Categories
        # -------------------------
        elif self.top_selling == 'category':
            category_sales = {}
            for order in orders:
                for line in order.lines:
                    category_name = line.product_id.categ_id.display_name or _('Uncategorized')
                    category_sales[category_name] = category_sales.get(category_name, 0.0) + line.price_subtotal

            sorted_categories = sorted(category_sales.items(), key=lambda x: x[1], reverse=True)
            top_categories = sorted_categories[:self.no_of_categories or 10]
            categories_list = [{'name': c[0], 'amount': c[1]} for c in top_categories]

            data['categories'] = categories_list
            data['no_of_categories'] = self.no_of_categories

            return self.env.ref(
                'advanced_pos_reports.pos_top_selling_category_report'
            ).report_action([], data=data)

        # -------------------------
        # Top Customers
        # -------------------------
        elif self.top_selling == 'customers':
            customer_sales = {}
            for order in orders.filtered(lambda o: o.partner_id):
                customer_name = order.partner_id.name
                customer_sales[customer_name] = customer_sales.get(customer_name, 0.0) + order.amount_total

            sorted_customers = sorted(customer_sales.items(), key=lambda x: x[1], reverse=True)
            top_customers = sorted_customers[:self.no_of_customers or 10]
            customers_list = [{'name': c[0], 'amount': c[1]} for c in top_customers]

            data['customers'] = customers_list
            data['no_of_customers'] = self.no_of_customers

            return self.env.ref(
                'advanced_pos_reports.pos_top_selling_customer_report'
            ).report_action([], data=data)