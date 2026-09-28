# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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

import logging
from odoo import models, api

_logger = logging.getLogger(__name__)


class StockQuant(models.Model):
    """
    Extends stock.quant to trigger real-time stock sync to CS-Cart upon inventory changes.
    """
    _inherit = 'stock.quant'

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create to trigger CS-Cart real-time stock sync on new quants.
        """
        records = super(StockQuant, self).create(vals_list)
        if not self.env.context.get('cs_cart_skip_stock_sync'):
            records._trigger_cs_cart_stock_sync()
        return records

    def write(self, vals):
        """
        Override write to trigger CS-Cart real-time stock sync on quant updates.
        """
        res = super(StockQuant, self).write(vals)
        if not self.env.context.get('cs_cart_skip_stock_sync'):
            self._trigger_cs_cart_stock_sync()
        return res

    def _trigger_cs_cart_stock_sync(self):
        """
        Trigger CS-Cart inventory update for all affected products.
        """
        products = self.mapped('product_id')
        if products:
            products._trigger_cs_cart_stock_sync_from_products()


class StockMove(models.Model):
    """
    Extends stock.move to trigger real-time stock sync to CS-Cart upon stock movements.
    """
    _inherit = 'stock.move'

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create to trigger CS-Cart real-time stock sync on new stock moves.
        """
        records = super(StockMove, self).create(vals_list)
        if not self.env.context.get('cs_cart_skip_stock_sync'):
            records._trigger_cs_cart_stock_sync()
        return records

    def write(self, vals):
        """
        Override write to trigger CS-Cart real-time stock sync on stock move changes.
        """
        res = super(StockMove, self).write(vals)
        if not self.env.context.get('cs_cart_skip_stock_sync'):
            self._trigger_cs_cart_stock_sync()
        return res

    def unlink(self):
        """
        Override unlink to trigger CS-Cart real-time stock sync when stock moves are removed.
        """
        products = self.mapped('product_id')
        res = super(StockMove, self).unlink()
        if products and not self.env.context.get('cs_cart_skip_stock_sync'):
            products._trigger_cs_cart_stock_sync_from_products()
        return res

    def _trigger_cs_cart_stock_sync(self):
        """
        Trigger CS-Cart inventory update for products affected by stock move.
        """
        products = self.mapped('product_id')
        if products:
            products._trigger_cs_cart_stock_sync_from_products()
