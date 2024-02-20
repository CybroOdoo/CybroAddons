# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Nikhil M(odoo@cybrosys.com)
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

###############################################################################
import calendar
from odoo import api, models


class ProductTemplate(models.Model):
    """Custom Dashboard for Viewing Product Details.
        This class extends the base model 'product.template' to create a custom dashboard
        for viewing specific product details in a more user-friendly manner."""
    _inherit = 'product.template'

    @api.model
    def get_data(self):
        """Returns data to the tiles of dashboard"""
        obj = self.env['product.template']
        return {
            'product_templates': obj.search_count([]),
            'product_variants': self.env['product.product'].search_count([]),
            'storable': obj.search_count([('detailed_type', '=', 'product')]),
            'consumable': obj.search_count([('detailed_type', '=', 'consu')]),
            'service': obj.search_count([('detailed_type', '=', 'service')]),
            'category': self.env['product.category'].search_count([]),
            'price_list': self.env['product.pricelist'].search_count([]),
            'product_attribute': self.env['product.attribute'].search_count([])
        }

    @api.model
    def get_top_sale_data(self):
        """return the top sale"""
        query = ('''select DISTINCT(product_template.name) as product_name,
                    sum(product_uom_qty) as total_quantity from sale_order_line 
                    inner join product_product on 
                    product_product.id=sale_order_line.product_id
                    inner join product_template on 
                    product_product.product_tmpl_id = product_template.id 
                    where sale_order_line.company_id = '''
                 + str(self.env.company.id) + ''' group by product_template.id ORDER BY 
                 total_quantity DESC Limit 10 ''')
        self._cr.execute(query)
        top_product = self._cr.dictfetchall()
        product_names = [item['product_name'] for item in top_product]
        quantities = [item['total_quantity'] for item in top_product]
        final = [quantities, product_names]
        return final

    @api.model
    def get_top_purchase_data(self):
        """Returns top purchase data"""
        query = ('''select DISTINCT(product_template.name) as product_name,sum(product_qty) as total_quantity from 
        purchase_order_line inner join product_product on product_product.id=purchase_order_line.product_id inner join 
        product_template on product_product.product_tmpl_id = product_template.id where purchase_order_line.company_id = '''
         + str(self.env.company.id) + ''' group by product_template.id ORDER BY total_quantity DESC Limit 10 ''')
        self._cr.execute(query)
        top_product = self._cr.dictfetchall()
        product_names = [item['product_name'] for item in top_product]
        quantities = [item['total_quantity'] for item in top_product]
        final = [quantities, product_names]
        return final

    @api.model
    def get_product_location_analysis(self):
        """Returns the location, location id to the selection"""
        categ_qry = """select id, complete_name from stock_location"""
        self._cr.execute(categ_qry)
        location = self._cr.dictfetchall()
        location_name = [item['complete_name'] for item in location]
        location_id = [item['id'] for item in location]
        return {'location_id': location_id, 'location_name': location_name}

    @api.model
    def get_products(self):
        """Returns the product, product name to the selection"""
        new_data = self.env['product.template'].search_read(fields=['id', 'name'])
        product_names = [item['name'] for item in new_data]
        product_ids = [item['id'] for item in new_data]
        return {'product_id': product_ids, 'product_name': product_names}

    @api.model
    def get_prod_details(self, data):
        """Returns the monthly analysis of product movement"""
        query = ("""select product_template.name as name,
                sum(stock_move_line.qty_done),EXTRACT(month from 
                stock_move_line.date) from stock_move_line inner join 
                product_product on stock_move_line.product_id = 
                product_product.id inner join product_template on 
                product_product.product_tmpl_id = product_template.id 
                where stock_move_line.company_id = %s and 
                stock_move_line.product_id = %s group by 
                product_template.name,stock_move_line.date"""
                % (self.env.company.id, data))
        self._cr.execute(query)
        product_move = self._cr.dictfetchall()
        month = []
        for rec in product_move:
            month.append(int(rec['date_part']))
            rec.update({
                'count': rec['sum'],
                'dates': calendar.month_name[int(rec['date_part'])],
                'month': int(rec['date_part'])
            })
        for rec in range(1, 13):
            if rec not in month:
                product_move.append({'count': 0,'dates': calendar.month_name[rec],'month': rec})
        cr = sorted(product_move, key=lambda i: i['month'])
        count = [item['count'] for item in cr]
        months = [item['dates'] for item in cr]
        return {'count': count,'dates': months}

    @api.model
    def get_product_qty_by_loc(self, args):
        """Returns product qty based on the location selected"""
        query = ('''select sl.complete_name, pt.name as name, sq.quantity from 
                stock_quant sq inner join stock_location sl on sq.location_id = 
                sl.id inner join product_product pp on sq.product_id = pp.id 
                inner join product_template pt on pp.product_tmpl_id = pt.id 
                where sq.company_id = '%s' and sl.id = '%s' group by 
                sl.complete_name,pt.name, sq.quantity '''
                 % (self.env.company.id, int(args)))
        self._cr.execute(query)
        product_qty = self._cr.dictfetchall()
        product_names = [item['name'] for item in product_qty]
        quantities = [item['quantity'] for item in product_qty]
        return {
            'products': product_names,
            'quantity': quantities,
        }
