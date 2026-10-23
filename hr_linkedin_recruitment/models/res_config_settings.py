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
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """config settings"""
    _inherit = 'res.config.settings'

    li_username = fields.Char(string="User Name", help="Your Linkedin Username")
    li_password = fields.Char(string="Password", help="Your Linkedin Password")

    def set_values(self):
        """Set config parameter values."""
        super().set_values()
        self.env['ir.config_parameter'].sudo().set_str(
            'recruitment.li_username', self.li_username or '')
        self.env['ir.config_parameter'].sudo().set_str(
            'recruitment.li_password', self.li_password or '')

    def get_values(self):
        """Get config parameter values."""
        res = super().get_values()
        res.update(
            li_username=self.env['ir.config_parameter'].sudo().get_str(
                'recruitment.li_username'),
            li_password=self.env['ir.config_parameter'].sudo().get_str(
                'recruitment.li_password'),
        )
        return res
