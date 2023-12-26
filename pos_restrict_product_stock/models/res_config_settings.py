# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri v  (odoo@cybrosys.com)
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
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """Inherited res configuration setting for adding fields for
                restricting out-of-stock products"""
    _inherit = 'res.config.settings'

    is_display_stock = fields.Boolean(string="Display Stock in POS",
                                      readonly=False,
                                      help="Enable if you want to show the "
                                           "quantity of products.")
    is_restrict_product = fields.Boolean(
        string="Restrict Product Out of Stock in POS", readonly=False,
        help="Enable if you want restrict of stock product from POS")
    stock_type = fields.Selection([('qty_on_hand', 'Qty on Hand'),
                                   ('virtual_qty', 'Virtual Qty'),
                                   ('both', 'Both')], string="Stock Type",
                                  readonly=False,
                                  help="In which quantity type you"
                                       "have to restrict and display in POS")

    @api.model
    def set_values(self):
        """ Set values for the fields """
        self.env['ir.config_parameter'].sudo(). \
            set_param('pos_restrict_product_stock.is_display_stock',
                      self.is_display_stock)
        self.env['ir.config_parameter'].sudo(). \
            set_param('pos_restrict_product_stock.is_restrict_product',
                      self.is_restrict_product)
        self.env['ir.config_parameter'].sudo(). \
            set_param('pos_restrict_product_stock.stock_type',
                      self.stock_type)
        return super().set_values()

    def get_values(self):
        """Getting the values from the transient model"""
        res = super().get_values()
        params = self.env['ir.config_parameter'].sudo().get_param
        is_display_stock = params('pos_restrict_product_stock.'
                                  'is_display_stock')
        is_restrict_product = params('pos_restrict_product_stock.'
                                     'is_restrict_product')
        stock_type = params('pos_restrict_product_stock.'
                            'stock_type')
        res.update(
            is_display_stock=is_display_stock,
            is_restrict_product=is_restrict_product,
            stock_type=stock_type
        )
        return res
