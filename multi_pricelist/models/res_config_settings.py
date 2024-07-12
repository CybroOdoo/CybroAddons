# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
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
################################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """This class inherits res config settings model to add the settings
    for multiple price lists"""
    _inherit = 'res.config.settings'

    multi_pricelist = fields.Boolean(string="Multiple Pricelists",
                                     help="Multiple price lists"
                                          "for the same sale order")

    @api.model
    def get_values(self):
        """Supering the get_values method to get multi_price list field."""
        res = super(ResConfigSettings, self).get_values()
        multi_pricelist = self.env[
            'ir.config_parameter'].sudo().get_param(
            'multi_pricelist.multi_pricelist')
        res.update(
            multi_pricelist=multi_pricelist,
        )
        return res

    def set_values(self):
        """Supering the set_values method to set multi_price list field."""
        super(ResConfigSettings, self).set_values()
        param = self.env['ir.config_parameter'].sudo()
        param.set_param('multi_pricelist.multi_pricelist',
                        self.multi_pricelist)
