# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """config settings"""
    _inherit = 'res.config.settings'

    li_username = fields.Char(string="User Name", help="Your Linkedin Username")
    li_password = fields.Char(string="Password", help="Your Linkedin Password")

    def set_values(self):
        """super the config to set the value"""
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'recruitment.li_username', self.li_username)
        self.env['ir.config_parameter'].sudo().set_param(
            'recruitment.li_password', self.li_password)

    def get_values(self):
        """super the config to get the value"""
        res = super(ResConfigSettings, self).get_values()
        res.update(
            li_username=self.env['ir.config_parameter'].sudo().get_param(
                'recruitment.li_username'),
            li_password=self.env['ir.config_parameter'].sudo().get_param(
                'recruitment.li_password'),
        )
        return res
