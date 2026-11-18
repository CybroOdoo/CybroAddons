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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, models

from .dashboard_utils import check_dashboard_access, localized_name


class StockMoveLine(models.Model):
    """ Extends 'stock.move.line' and provides methods for retrieving data for
    dashboard."""
    _inherit = "stock.move.line"

    @api.model
    def get_product_moves(self):
        """ Returns the categories that have done product moves."""
        check_dashboard_access(self.env)
        self.env.flush_all()
        products = self.env['stock.move.line']._read_group(
            [('company_id', '=', self.env.company.id),
             ('state', '=', 'done')],
            groupby=['product_id'])
        categories = self.env['product.product'].browse(
            [product.id for [product] in products]
        ).categ_id.sorted('complete_name')
        return {
            'category_id': categories.ids,
            'category_name': categories.mapped('complete_name'),
        }

    @api.model
    def product_move_by_category(self, option):
        """ Returns the products of a category and their done quantity.

        :param option: id of the product category.
        """
        check_dashboard_access(self.env)
        if option is None:
            return {'name': [], 'count': []}
        self.env.flush_all()
        self.env.cr.execute(
            """SELECT product_template.name,
                SUM(stock_move_line.quantity_product_uom) AS total_qty
            FROM stock_move_line
            INNER JOIN product_product
                ON stock_move_line.product_id = product_product.id
            INNER JOIN product_template
                ON product_product.product_tmpl_id = product_template.id
            WHERE stock_move_line.company_id = %s
                AND stock_move_line.state = 'done'
                AND product_template.categ_id = %s
            GROUP BY product_template.id, product_template.name
            ORDER BY total_qty DESC, product_template.id""",
            (self.env.company.id, int(option)))
        product_move = self.env.cr.dictfetchall()
        return {
            'name': [localized_name(record['name'], self.env.lang)
                     for record in product_move],
            'count': [float(record['total_qty']) for record in product_move],
        }
