# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Saneen K (odoo@cybrosys.com)
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


class ResConfigInherit(models.TransientModel):
    """Inherit the res.config.settings for adding the field for enabling the
     product restriction and for choosing the required quantities"""
    _inherit = 'res.config.settings'

    product_restriction = fields.Boolean(string='Out Of Stock Product'
                                                ' Restriction',
                                         help='Enable Out Of Stock Product '
                                              'Restriction')
    check_stock = fields.Selection([('on_hand_quantity', 'On Hand Quantity'),
                                    ('forecast_quantity', 'Forecast Quantity')],
                                   string="Based On",
                                   help='Choose the type of restriction')

    @api.model
    def get_values(self):
        """get values from the fields"""
        res = super(ResConfigInherit, self).get_values()
        res.update(
            product_restriction=self.env['ir.config_parameter'].sudo(
            ).get_param('sale_stock_restrict.product_restriction'),
            check_stock=self.env['ir.config_parameter'].sudo().get_param(
                'sale_stock_restrict.check_stock')
        )
        return res

    def set_values(self):
        """Set values in the fields"""
        super(ResConfigInherit, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'sale_stock_restrict.product_restriction', self.product_restriction)
        self.env['ir.config_parameter'].sudo().set_param(
            'sale_stock_restrict.check_stock', self.check_stock)
