# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#############################################################################
from odoo import fields, models


class LoginDetail(models.Model):
    """ Class for the model login_detail contains fields related to
     the model."""
    _name = 'login.detail'
    _description = 'Login Detail'
    _order = 'date_time desc'

    user_id = fields.Many2one('res.users', string="User", index=True,
                              ondelete='set null', readonly=True,
                              help="User who logged in")
    name = fields.Char(string="User Name",
                       help="Name of the logged-in user")
    date_time = fields.Datetime(
        string="Login Date and Time",
        default=fields.Datetime.now,
        help="Date and time of login")
    ip_address = fields.Char(string="IP Address", help="IP address of login")
