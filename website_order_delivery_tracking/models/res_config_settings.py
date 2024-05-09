# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Saneen K (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Model representing res.config.settings"""
    _inherit = 'res.config.settings'

    delivery_tracking_api_key = fields.Char(
        'API Key',
        help='This API key is used to access Odoo and change the delivery'
             ' status',required=True)

    def set_values(self):
        """
        Overrides the base method to set the configured delivery tracking API
        key value in the 'ir.config_parameter' model.
        """
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param(
            'stock.delivery_tracking_api_key', self.delivery_tracking_api_key)
        return res

    def get_values(self):
        """
        Overrides the base method to get the delivery tracking API key value
        from the 'ir.config_parameter' model and include it in the result.
        """
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        delivery_tracking_api_key = params.get_param(
            'stock.delivery_tracking_api_key')
        res.update(
            delivery_tracking_api_key=delivery_tracking_api_key,
        )
        return res
