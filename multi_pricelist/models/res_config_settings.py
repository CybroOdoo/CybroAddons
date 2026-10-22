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
#############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """ This class inherits res.config.settings model to add the settings
    for multiple price lists """
    _inherit = 'res.config.settings'

    multi_pricelist = fields.Boolean(
        string="Multiple Pricelists",
        help="Allow a different pricelist to be applied to each line of the "
             "same sale order.")

    @api.model
    def get_values(self):
        """ Extend get_values to load the multi pricelist setting """
        res = super().get_values()
        value = self.env['ir.config_parameter'].sudo().get_str(
            'multi_pricelist.multi_pricelist')
        res['multi_pricelist'] = value in ('True', 'true', '1')
        return res

    def set_values(self):
        """ Extend set_values to store the multi pricelist setting """
        res = super().set_values()
        self.env['ir.config_parameter'].sudo().set_str(
            'multi_pricelist.multi_pricelist',
            'True' if self.multi_pricelist else 'False')
        return res
