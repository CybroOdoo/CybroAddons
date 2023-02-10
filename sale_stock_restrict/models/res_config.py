#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import fields, models, api


class ResConfigInherit(models.TransientModel):
    _inherit = 'res.config.settings'

    product_restriction = fields.Boolean(
        string='Out Of Stock Product Restriction',
        help='Enable Out Of Stock Product Restriction')
    check_stock = fields.Selection(
        [('on_hand_quantity', 'On Hand Ouantity'),
         ('forecast_quantity', 'Forecast Ouantity')], string="Based On",
        help='Choose the type of restriction')

    @api.model
    def get_values(self):
        """get values from the fields"""
        res = super(ResConfigInherit, self).get_values()
        params = self.env['ir.config_parameter'].sudo().get_param
        product_restriction = params('sale_stock_restrict.product_restriction')
        check_stock = params('sale_stock_restrict.check_stock')
        res.update(
            product_restriction=product_restriction,
            check_stock=check_stock
        )
        return res

    def set_values(self):
        """Set values in the fields"""
        super(ResConfigInherit, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'sale_stock_restrict.product_restriction', self.product_restriction)
        self.env['ir.config_parameter'].sudo().set_param(
            'sale_stock_restrict.check_stock', self.check_stock)
