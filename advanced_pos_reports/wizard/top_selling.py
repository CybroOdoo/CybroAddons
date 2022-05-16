# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class PosTopSelling(models.TransientModel):
    _name = 'pos.sale.top.selling'
    _description = 'Point of Sale Top Selling Product/Category/Customer Report'

    start_date = fields.Datetime()
    end_date = fields.Datetime()
    top_selling = fields.Selection([('products', 'Products'), ('category', 'Categories'), ('customers', 'Customers')],
                                   string='Top Selling', default='products')
    no_of_products = fields.Integer()
    no_of_categories = fields.Integer()
    no_of_customers = fields.Integer()

    def generate_report(self):
        data = {'start_date': self.start_date, 'end_date': self.end_date, 'top_selling': self.top_selling}
        if self.top_selling == 'products':
            data['no_of_products'] = self.no_of_products
            return self.env.ref('advanced_pos_reports.pos_top_selling_products_report').report_action([], data=data)
        elif self.top_selling == 'category':
            data['no_of_categories'] = self.no_of_categories
            return self.env.ref('advanced_pos_reports.pos_top_selling_category_report').report_action([], data=data)
        elif self.top_selling == 'customers':
            data['no_of_customers'] = self.no_of_customers
            return self.env.ref('advanced_pos_reports.pos_top_selling_customer_report').report_action([], data=data)