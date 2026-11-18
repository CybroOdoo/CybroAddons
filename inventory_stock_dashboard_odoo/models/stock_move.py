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
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models

from .dashboard_utils import check_dashboard_access, localized_name

DEAD_STOCK_PERIODS = {'day': 'days', 'week': 'weeks', 'month': 'months'}


class StockMove(models.Model):
    """ Extends 'stock.move' and provides methods for retrieving data for
    dashboard."""
    _inherit = "stock.move"

    def _get_top_products(self, since):
        """ Returns the ten most delivered products and their done quantity
        since the given date.

        :param datetime since: start of the period.
        """
        check_dashboard_access(self.env)
        self.env.flush_all()
        self.env.cr.execute(
            """SELECT product_template.name,
                SUM(stock_move_line.quantity_product_uom) AS total_qty
            FROM stock_move_line
            INNER JOIN stock_move
                ON stock_move_line.move_id = stock_move.id
            INNER JOIN stock_picking
                ON stock_move.picking_id = stock_picking.id
            INNER JOIN stock_picking_type
                ON stock_picking.picking_type_id = stock_picking_type.id
            INNER JOIN product_product
                ON stock_move_line.product_id = product_product.id
            INNER JOIN product_template
                ON product_template.id = product_product.product_tmpl_id
            WHERE stock_move.state = 'done'
                AND stock_move.company_id = %s
                AND stock_picking_type.code = 'outgoing'
                AND stock_move.date >= %s
            GROUP BY product_template.id, product_template.name
            ORDER BY total_qty DESC, product_template.id
            LIMIT 10""",
            (self.env.company.id, since))
        top_product = self.env.cr.dictfetchall()
        return {
            'products': [localized_name(record['name'], self.env.lang)
                         for record in top_product],
            'count': [float(record['total_qty']) for record in top_product],
        }

    def _get_location_moves(self, since):
        """ Returns the source locations and the number of stock moves done
        from them since the given date.

        :param datetime since: start of the period.
        """
        check_dashboard_access(self.env)
        self.env.flush_all()
        self.env.cr.execute(
            """SELECT stock_location.complete_name,
                COUNT(stock_move.id) AS move_count
            FROM stock_move
            INNER JOIN stock_location
                ON stock_move.location_id = stock_location.id
            WHERE stock_move.state = 'done'
                AND stock_move.company_id = %s
                AND stock_move.date >= %s
            GROUP BY stock_location.complete_name
            ORDER BY move_count DESC, stock_location.complete_name""",
            (self.env.company.id, since))
        location_moves = self.env.cr.dictfetchall()
        return {
            'name': [record['complete_name'] for record in location_moves],
            'count': [record['move_count'] for record in location_moves],
        }

    @api.model
    def get_the_top_products(self):
        """ Returns top ten products and done quantity."""
        return self._get_top_products(
            fields.Datetime.now() - relativedelta(days=10))

    @api.model
    def top_products_last_ten(self):
        """ Returns top ten products and done quantity for last 10 days."""
        return self._get_top_products(
            fields.Datetime.now() - relativedelta(days=10))

    @api.model
    def top_products_last_thirty(self):
        """ Returns top ten products and done quantity for last 30 days."""
        return self._get_top_products(
            fields.Datetime.now() - relativedelta(days=30))

    @api.model
    def top_products_last_three_months(self):
        """ Returns top ten products and done quantity for last 3 months."""
        return self._get_top_products(
            fields.Datetime.now() - relativedelta(months=3))

    @api.model
    def top_products_last_year(self):
        """ Returns top ten products and done quantity for last year."""
        return self._get_top_products(
            fields.Datetime.now() - relativedelta(years=1))

    @api.model
    def stock_move_last_ten_days(self, option=None):
        """ Returns location name and number of stock moves of the stock moves
        graph for the last ten days."""
        return self._get_location_moves(
            fields.Datetime.now() - relativedelta(days=10))

    @api.model
    def this_month(self, option=None):
        """ Returns location name and number of stock moves of the stock moves
        graph for the current month."""
        return self._get_location_moves(
            fields.Datetime.now().replace(
                day=1, hour=0, minute=0, second=0, microsecond=0))

    @api.model
    def last_three_month(self, option=None):
        """ Returns location name and number of stock moves of the stock moves
        graph for the last three months."""
        return self._get_location_moves(
            fields.Datetime.now() - relativedelta(months=3))

    @api.model
    def last_year(self, option=None):
        """ Returns location name and number of stock moves of the stock moves
        graph for the last year."""
        return self._get_location_moves(
            fields.Datetime.now() - relativedelta(months=12))

    @api.model
    def get_dead_of_stock(self):
        """ Returns the products that were not delivered during the period set
        in the settings, with their on-hand quantity. Returns None when the
        graph is disabled."""
        check_dashboard_access(self.env)
        params = self.env['ir.config_parameter'].sudo()
        sett_dead_stock_bool = params.get_str(
            "inventory_stock_dashboard_odoo.dead_stock_bol", default="")
        sett_dead_stock_quantity = params.get_str(
            "inventory_stock_dashboard_odoo.dead_stock", default="")
        sett_dead_stock_type = params.get_str(
            "inventory_stock_dashboard_odoo.dead_stock_type", default="")
        if sett_dead_stock_bool != "True" or not sett_dead_stock_quantity:
            return None
        period = {DEAD_STOCK_PERIODS.get(sett_dead_stock_type, 'days'):
                  int(sett_dead_stock_quantity)}
        since = fields.Datetime.now() - relativedelta(**period)
        self.env.flush_all()
        # One row per product: the quantities of all the internal locations
        # and lots are summed.
        self.env.cr.execute(
            """SELECT stock_quant.product_id,
                SUM(stock_quant.quantity) AS total_qty
            FROM stock_quant
            INNER JOIN stock_location
                ON stock_quant.location_id = stock_location.id
            INNER JOIN product_product
                ON stock_quant.product_id = product_product.id
            WHERE stock_quant.company_id = %(company)s
                AND stock_location.usage = 'internal'
                AND product_product.create_date < %(since)s
                AND NOT EXISTS (
                    SELECT 1 FROM stock_move
                    INNER JOIN stock_picking
                        ON stock_move.picking_id = stock_picking.id
                    INNER JOIN stock_picking_type
                        ON stock_picking.picking_type_id
                            = stock_picking_type.id
                    WHERE stock_move.product_id = stock_quant.product_id
                        AND stock_move.company_id = %(company)s
                        AND stock_move.state = 'done'
                        AND stock_picking_type.code = 'outgoing'
                        AND stock_move.date >= %(since)s)
            GROUP BY stock_quant.product_id
            HAVING SUM(stock_quant.quantity) > 0
            ORDER BY total_qty DESC, stock_quant.product_id""",
            {'company': self.env.company.id, 'since': since})
        result = self.env.cr.dictfetchall()
        products = self.env['product.product'].sudo().browse(
            [record['product_id'] for record in result])
        names = {product.id: product.display_name for product in products}
        return {
            'product_name': [names[record['product_id']]
                             for record in result],
            'total_quantity': [float(record['total_qty'])
                               for record in result],
        }
