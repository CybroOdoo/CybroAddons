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
import calendar
from datetime import datetime
from odoo import api, models


class ProductTemplate(models.Model):
    """ The ProductTemplate model inherited to function for creating the
    Template Dashboard values. """
    _inherit = 'product.template'

    @api.model
    def get_data(self):
        """ Return aggregated product statistics for dashboard tiles. """
        return {
            'product_templates': self.search_count([]),
            'product_variants': self.env['product.product'].search_count([]),
            'combo': self.search_count([('type', '=', 'combo')]),
            'goods': self.search_count([('type', '=', 'consu')]),
            'service': self.search_count([('type', '=', 'service')]),
            'category': self.env['product.category'].search_count([]),
            'price_list': self.env['product.pricelist'].search_count([]),
            'product_attribute': self.env['product.attribute'].search_count([]),
        }

    @api.model
    def get_top_sale_data(self):
        """  Returns the top 10 best-selling products for the current company.
        Calculates total sold quantity per product.
        Used for sales dashboard and reporting. """
        query = '''
            select DISTINCT(product_template.name ->> 'en_US') as product_name,
                sum(product_uom_qty) as total_quantity
            from sale_order_line
            inner join product_product
                on product_product.id=sale_order_line.product_id
            inner join product_template 
                on product_product.product_tmpl_id = product_template.id
            where sale_order_line.company_id = ''' + str(
                self.env.company.id) + ''' group by product_template.id
            ORDER BY total_quantity DESC Limit 10 
        '''
        self.env.cr.execute(query)
        top_product = self.env.cr.dictfetchall()
        total_quantity = [record.get('total_quantity') for record in top_product]
        product_name = [record.get('product_name') for record in top_product]
        final = [total_quantity, product_name]
        return final

    @api.model
    def get_top_purchase_data(self):
        """  Returns the top 10 most purchased products for the current company.
        Computes total purchased quantity per product.
        Used for purchase analysis and reporting. """
        query = ('''
            select DISTINCT(product_template.name ->> 'en_US') as product_name,
                sum(product_qty) as total_quantity
            from purchase_order_line
            inner join product_product 
                on product_product.id=purchase_order_line.product_id
            inner join product_template 
                on product_product.product_tmpl_id = product_template.id
            where purchase_order_line.company_id = ''' + str(
                self.env.company.id) + '''
            group by product_template.id 
            ORDER BY total_quantity DESC Limit 10 ''')
        self.env.cr.execute(query)
        top_product = self.env.cr.dictfetchall()
        final = [
            [record.get('total_quantity') for record in top_product],
            [record.get('product_name') for record in top_product]
        ]
        return final

    @api.model
    def get_product_location_analysis(self):
        """ Fetches stock locations with their IDs and names.
        Prioritizes internal storage locations that contain stock. """
        try:
            quants = self.env['stock.quant']._read_group(
                domain=[
                    ('location_id.usage', '=', 'internal'),
                    ('quantity', '>', 0),
                ],
                groupby=['location_id'],
                aggregates=['quantity:sum'],
                order='quantity:sum desc',
            )
            locations_with_stock = [loc for loc, _qty in quants if loc]
        except Exception:
            locations_with_stock = []

        stock_loc_ids = {loc.id for loc in locations_with_stock}
        other_locs = self.env['stock.location'].search([
            ('usage', '=', 'internal'),
            ('id', 'not in', list(stock_loc_ids)),
        ], order='complete_name asc')

        all_locations = locations_with_stock + list(other_locs)
        if not all_locations:
            all_locations = self.env['stock.location'].search([
                ('usage', '=', 'internal')
            ], order='complete_name asc')
        if not all_locations:
            all_locations = self.env['stock.location'].search([], order='complete_name asc')

        return {
            'location_id': [loc.id for loc in all_locations],
            'location_name': [loc.complete_name for loc in all_locations]
        }

    @api.model
    def get_products(self):
        """ Retrieves all products with their IDs and names.
        Formats product data for selection fields.
        Used for product-based filtering and analysis. """
        products = self.env['product.template'].search_read(
            [], ['id', 'name'], order='name asc'
        )
        return {
            'product_id': [p['id'] for p in products],
            'product_name': [p['name'] for p in products],
        }

    @api.model
    def get_years(self):
        """Return a list of the last five years, including the current year."""
        current_year = datetime.now().year
        last_five_years = [current_year - year for year in range(5)]
        return last_five_years

    @api.model
    def get_prod_details(self, data, year):
        """ Returns detailed month-wise stock movement for a selected product
        in the given year. It aggregates stock move quantities and ensures all
        months are represented. """
        if not data or not year:
            return {
                'count': [0] * 12,
                'dates': [calendar.month_abbr[m] for m in range(1, 13)]
            }
        query = """
            SELECT EXTRACT(MONTH FROM sml.date)::int AS month_num,
                   SUM(sml.quantity) AS total_qty
            FROM stock_move_line sml
            INNER JOIN product_product pp ON sml.product_id = pp.id
            WHERE sml.company_id = %s
              AND pp.product_tmpl_id = %s
              AND EXTRACT(YEAR FROM sml.date)::int = %s
            GROUP BY month_num
            ORDER BY month_num
        """
        self.env.cr.execute(query, [self.env.company.id, int(data), int(year)])
        results = dict(self.env.cr.fetchall())
        months = [calendar.month_abbr[m] for m in range(1, 13)]
        counts = [float(results.get(m, 0.0)) for m in range(1, 13)]
        return {
            'count': counts,
            'dates': months,
        }

    @api.model
    def product_move_by_category(self, args):
        """ Rpc method of product moves by category. Returns category name and
        quantity_done. """
        if not args:
            return {'name': [], 'count': []}
        category_id = int(args)
        query = """
            SELECT pt.name AS name, SUM(sml.quantity) AS quantity
            FROM stock_move_line sml
            INNER JOIN product_product pp ON sml.product_id = pp.id
            INNER JOIN product_template pt ON pp.product_tmpl_id = pt.id
            WHERE sml.company_id = %s AND pt.categ_id = %s
            GROUP BY pt.name
        """
        self.env.cr.execute(query, [self.env.company.id, category_id])
        product_move = self.env.cr.dictfetchall()
        return {
            'name': [record['name'] for record in product_move],
            'count': [float(record['quantity']) for record in product_move],
        }

    @api.model
    def get_product_qty_by_loc(self, args):
        """ Retrieves product-wise available quantity for a selected stock location.
        Queries stock quants to aggregate quantities per product for the given
        location and returns structured data for reporting or charts. """
        if not args:
            return {'products': [], 'quantity': []}
        try:
            loc_id = int(args)
        except (ValueError, TypeError):
            return {'products': [], 'quantity': []}

        try:
            quants = self.env['stock.quant']._read_group(
                domain=[
                    ('location_id', '=', loc_id),
                    ('quantity', '>', 0),
                ],
                groupby=['product_id'],
                aggregates=['quantity:sum'],
                order='quantity:sum desc',
                limit=15
            )
            products = []
            quantities = []
            for prod, qty_sum in quants:
                if prod:
                    products.append(prod.display_name or prod.name or '')
                    quantities.append(float(qty_sum))
            return {
                'products': products,
                'quantity': quantities,
            }
        except Exception:
            lang = self.env.user.lang or 'en_US'
            query = """
                SELECT COALESCE(pt.name->>%s, pt.name->>'en_US', pt.name::text) AS product_name,
                       SUM(sq.quantity) AS quantity
                FROM stock_quant sq
                INNER JOIN stock_location sl ON sq.location_id = sl.id
                INNER JOIN product_product pp ON sq.product_id = pp.id
                INNER JOIN product_template pt ON pp.product_tmpl_id = pt.id
                WHERE sl.id = %s AND sq.quantity > 0
                GROUP BY pt.id, pt.name
                ORDER BY quantity DESC
                LIMIT 15
            """
            self.env.cr.execute(query, [lang, loc_id])
            product_qty = self.env.cr.dictfetchall()
            return {
                'products': [rec['product_name'] for rec in product_qty],
                'quantity': [float(rec['quantity']) for rec in product_qty],
            }
