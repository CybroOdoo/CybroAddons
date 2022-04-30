# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    serial_selection = fields.Selection([('global', 'Global'), ('product_wise', 'Product Wise')],
                                        default='global', string="Serial number Selection Method")

    digit = fields.Integer(string="Number of Digits")
    prefix = fields.Char(string="Prefix")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        serial_selection = params.get_param('serial_selection')
        digit = params.get_param('digit')
        prefix = params.get_param('prefix')
        res.update(serial_selection=serial_selection, digit=digit, prefix=prefix)
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        parms = self.env['ir.config_parameter'].sudo()
        parms.set_param("serial_selection", self.serial_selection)
        parms.set_param("digit", self.digit)
        parms.set_param("prefix", self.prefix)
