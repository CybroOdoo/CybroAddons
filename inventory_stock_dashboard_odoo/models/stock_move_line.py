# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import api, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    @api.model
    def get_product_moves(self):
        """rpc method of product moves graph
            Returns product move product and quantity_done"""
        company_id = self.env.company.id
        query = ('''select product_template.name,sum(stock_move_line.qty_done) from stock_move_line
                inner join product_product on stock_move_line.product_id = product_product.id
                inner join product_template on product_product.product_tmpl_id = product_template.id
                where stock_move_line.company_id = %s group by product_template.name''' % company_id)
        self._cr.execute(query)
        products_quantity = self._cr.dictfetchall()
        quantity_done = []
        name = []
        for record in products_quantity:
            quantity_done.append(record.get('sum'))
            name.append(record.get('name'))
        value = {'name': name, 'count': quantity_done}
        category_query = '''select product_category.id,product_category.name from stock_move_line
                inner join product_product on stock_move_line.product_id = product_product.id
                inner join product_template on product_product.product_tmpl_id = product_template.id
                inner join product_category on product_template.categ_id = product_category.id
                where stock_move_line.company_id = %s and stock_move_line.state = 'done'
                group by product_category.id''' % company_id
        self._cr.execute(category_query)
        category = self._cr.dictfetchall()
        category_id = []
        category_name = []
        for record in category:
            category_id.append(record.get('id'))
            category_name.append(record.get('name'))
        value1 = {'category_id': category_id, 'category_name': category_name}
        return value, value1

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
            name.append(record.get('name')['en_US'])
        value = {
            'name': name,
            'count': quantity_done,
        }
        return value
