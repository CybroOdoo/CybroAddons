# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import calendar
from datetime import datetime
from collections import OrderedDict
from odoo import api, models


class ProductTemplate(models.Model):
    """The ProductTemplate model inherited to function for creating the
    Template Dashboard values"""
    _inherit = 'product.template'

    @api.model
    def get_data(self):
        """Returns data to the tiles of dashboard"""
        return {
            'product_templates': self.search_count([]),
            'product_variants': self.env['product.product'].search_count([]),
            'storable': self.search_count([('detailed_type', '=', 'product')]),
            'consumable': self.search_count([('detailed_type', '=', 'consu')]),
            'service': self.search_count([('detailed_type', '=', 'service')]),
            'category': self.env['product.category'].search_count([]),
            'price_list': self.env['product.pricelist'].search_count([]),
            'product_attribute': self.env['product.attribute'].search_count([]),
        }

    @api.model
    def get_top_sale_data(self):
        """return the top sale"""
        query = '''select DISTINCT(product_template.name ->> 'en_US') as product_name,sum(product_uom_qty) as total_quantity from 
                       sale_order_line inner join product_product on product_product.id=sale_order_line.product_id inner join 
                       product_template on product_product.product_tmpl_id = product_template.id where sale_order_line.company_id = ''' + str(
            self.env.company.id) + ''' group by product_template.id ORDER 
                       BY total_quantity DESC Limit 10 '''
        self._cr.execute(query)
        top_product = self._cr.dictfetchall()
        total_quantity = [record.get('total_quantity') for record in top_product]
        product_name = [record.get('product_name') for record in top_product]
        final = [total_quantity, product_name]
        return final

    @api.model
    def get_top_purchase_data(self):
        """Returns top purchase data"""
        query = ('''select DISTINCT(product_template.name ->> 'en_US') as product_name,sum(product_qty) as total_quantity from 
                               purchase_order_line inner join product_product on product_product.id=purchase_order_line.product_id inner join 
                               product_template on product_product.product_tmpl_id = product_template.id where purchase_order_line.company_id = '''
                 + str(self.env.company.id) + ''' group by product_template.id 
                               ORDER BY total_quantity DESC Limit 10 ''')
        self._cr.execute(query)
        top_product = self._cr.dictfetchall()
        final = [
            [record.get('total_quantity') for record in top_product],
            [record.get('product_name') for record in top_product]
        ]
        return final

    @api.model
    def get_product_location_analysis(self):
        """Returns the location, location id to the selection"""
        categ_qry = """select id, complete_name from stock_location"""
        self._cr.execute(categ_qry)
        location = self._cr.dictfetchall()
        location_id = []
        location_name = []
        for record in location:
            location_id.append(record.get('id'))
            location_name.append(record.get('complete_name'))
        value1 = {'location_id': location_id, 'location_name': location_name}
        return value1

    @api.model
    def get_products(self):
        """Returns the product, product name to the selection"""
        data = self.env['product.template'].search([])
        product_id = []
        product_name = []
        for record in data:
            product_id.append(record.id)
            product_name.append(self.env['product.template'].search([('id', '=', record.id)]).name)
        value1 = {'product_id': product_id, 'product_name': product_name}
        return value1

    @api.model
    def get_years(self):
        """To get last 5 years from the current year"""
        current_year = datetime.now().year
        last_five_years = [current_year - year for year in range(5)]
        return last_five_years

    @api.model
    def get_prod_details(self, data, year):
        """Returns the monthly analysis of product movement"""
        query = """select product_template.name as name,sum(stock_move_line.quantity), stock_move_line.date as date_part from stock_move_line
                                inner join product_product on product_product.id = stock_move_line.product_id
                                inner join product_template on product_product.product_tmpl_id = product_template.id
                                where stock_move_line.company_id = %s and product_template.id = %s group by product_template.name,
                                stock_move_line.date""" % (self.env.company.id, data)
        self._cr.execute(query)
        product_moves = self._cr.dictfetchall()
        product_move = []
        for move in product_moves:
            if str(move['date_part'].year) == year:
                product_move.append(move)
        month = []
        for rec in product_move:
            date_part = rec.get('date_part')
            month.append(int(date_part.month))
            rec.update({
                'count': rec['sum'],
                'dates': calendar.month_name[int(date_part.month)],
                'month': int(date_part.month)
            })
        for rec in range(1, 13):
            if rec not in month:
                product_move.append({
                    'count': 0,
                    'dates': calendar.month_name[rec],
                    'month': rec
                })
        count = []
        months = []
        cr = sorted(product_move, key=lambda i: i['month'])
        month_of_num = 0
        total_count = 0
        for rec in cr:
            if month_of_num == rec['month']:
                total_count += rec['count']
                if rec['count'] > 0:
                    rec.update({'count': total_count})
            else:
                month_of_num = rec['month']
                total_count = rec['count']
        # OrderedDict to maintain insertion order
        result = OrderedDict()
        for item in cr:
            # Check if month already exists
            if item['month'] not in result:
                result[item['month']] = item
            else:
                # Update if count is higher
                if item['count'] > result[item['month']]['count']:
                    result[item['month']] = item
        # Convert back to list
        result = list(result.values())
        for rec in result:
            count.append(rec['count'])
            months.append(rec['dates'])
        return {
            'count': count,
            'dates': months
        }

    @api.model
    def product_move_by_category(self, args):
        """rpc method of product moves by category
            Returns category name and quantity_done"""
        category_id = int(args)
        company_id = self.env.company.id
        query = ('''select product_template.name,sum(stock_move_line.qty_done) from stock_move_line
            inner join product_product on stock_move_line.product_id = product_product.id
            inner join product_template on product_product.product_tmpl_id = product_template.id
            inner join product_category on product_template.categ_id = product_category.id
            where stock_move_line.company_id = %s and product_category.id = %s group by product_template.name''' %
                 (company_id, category_id))
        self._cr.execute(query)
        product_move = self._cr.dictfetchall()
        quantity_done = []
        name = []
        for record in product_move:
            quantity_done.append(record.get('sum'))
            name.append(record.get('name'))
        value = {
            'name': name,
            'count': quantity_done,
        }
        return value

    @api.model
    def get_product_qty_by_loc(self, args):
        """Returns product qty based on the location selected"""
        query = ('''
                    select sl.complete_name, pt.name as name, sq.quantity
                    from stock_quant sq
                    inner join stock_location sl on sq.location_id = sl.id
                    inner join product_product pp on sq.product_id = pp.id
                    inner join product_template pt on pp.product_tmpl_id = pt.id
                    where sq.company_id = '%s' and sl.id = '%s'
                    group by sl.complete_name,pt.name, sq.quantity
                ''' % (self.env.company.id, int(args)))
        self._cr.execute(query)
        product_qty = self._cr.dictfetchall()
        product = [rec['name'] for rec in product_qty]
        quantity = [rec['quantity'] for rec in product_qty]
        return {
            'products': product,
            'quantity': quantity,
        }
