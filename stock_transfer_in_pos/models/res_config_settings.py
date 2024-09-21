# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
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
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """ Inheriting model for adding a field to settings that allow to transfer
    stock from pos session """
    _inherit = 'res.config.settings'

    is_stock_transfer = fields.Boolean(
        string="Enable Stock Transfer",
        help="Enable if you want to transfer stock from PoS session")

    def get_values(self):
        """ Supering the getter to get the is_stock_transfer field """
        res = super(ResConfigSettings, self).get_values()
        res.update(
            is_stock_transfer=self.env['ir.config_parameter'].sudo().get_param(
                'stock_transfer_in_pos.is_stock_transfer')
        )
        return res

    def set_values(self):
        """ Supering the setter to set the is_stock_transfer field """
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'stock_transfer_in_pos.is_stock_transfer',
            self.is_stock_transfer or False)
        return res
