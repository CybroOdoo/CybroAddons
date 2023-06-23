# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)

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
#############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    generate_token = fields.Boolean(string="Generate Token",
                                    help="This will generate separate token "
                                         "for all Take Away orders.")
    pos_token = fields.Integer(help="The token will be start from 1.",
                               string="Token")
    takeaway = fields.Boolean(string="POS Takeaways",
                              help="This will enable the Take Away feature "
                                   "on POS.")

    def get_values(self):
        """supering the getter to get the takeaway, generate_token
        and pos_token fields."""
        res = super(ResConfigSettings, self).get_values()
        res.update(
            takeaway=self.env['ir.config_parameter'].sudo().get_param(
                'pos_takeaway.takeaway'),
            generate_token=self.env['ir.config_parameter'].sudo().get_param(
                'pos_takeaway.generate_token'),
            pos_token=self.env['ir.config_parameter'].sudo().get_param(
                'pos_takeaway.pos_token')
        )
        return res

    def set_values(self):
        """supering the setter to set the takeaway, generate_token
                and pos_token fields."""
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'pos_takeaway.takeaway',
            self.takeaway or False)
        self.env['ir.config_parameter'].sudo().set_param(
            'pos_takeaway.generate_token',
            self.generate_token or False)
        self.env['ir.config_parameter'].sudo().set_param(
            'pos_takeaway.pos_token',
            self.pos_token or 0)
        return res
