# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sruthi Pavithran (odoo@cybrosys.com)
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

    start_date = fields.Datetime(required=True,
                                 string="Start Date",
                                 help="Starting date")
    end_date = fields.Datetime(required=True,
                               string="End Date",
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
        """Generate top_selling product,category,customer report from pos"""
        if self.start_date > self.end_date:
            raise ValidationError(_("The End Date must be greater than the "
                                    "Start Date"))
        data = {
            'start_date': self.start_date, 'end_date': self.end_date,
            'top_selling': self.top_selling
        }
        if self.top_selling == 'products':
            data['no_of_products'] = self.no_of_products
            return self.env.ref(
                'advanced_pos_reports.pos_top_selling_products_report'
            ).report_action([], data=data)
        elif self.top_selling == 'category':
            data['no_of_categories'] = self.no_of_categories
            return self.env.ref(
                'advanced_pos_reports.pos_top_selling_category_report'
            ).report_action([], data=data)
        elif self.top_selling == 'customers':
            data['no_of_customers'] = self.no_of_customers
            return self.env.ref(
                'advanced_pos_reports.pos_top_selling_customer_report'
            ).report_action([], data=data)
