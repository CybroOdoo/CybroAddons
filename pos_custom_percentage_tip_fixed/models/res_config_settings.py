"""pos custom tips"""
# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """this class used to add fields in the settings model"""
    _inherit = 'res.config.settings'

    custom_tip_percentage = fields.Float(string="Custom Percentage",
                                        help="enter the percentage custom tips")

    @api.model
    def set_values(self):
        """ Set values for the fields """
        self.env['ir.config_parameter'].sudo(). \
            set_param('pos_custom_percentage_tip_fixed.custom_tip_percentage',
                      self.custom_tip_percentage)
        return super(ResConfigSettings, self).set_values()

    def get_values(self):
        """Getting the values from the transient model"""
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo().get_param
        custom_tip_percentage = params('pos_custom_percentage_tip_fixed.'
                                       'custom_tip_percentage')
        res.update(
            custom_tip_percentage=custom_tip_percentage
        )
        return res
