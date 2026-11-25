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


class ResUsers(models.Model):
    """This model extends the 'res.users' model to add a 'password_hint' field
     that stores the password hint provided by users during sign-up.
     Fields:
        password_hint (Char): A string field that stores the password hint
        provided by users during sign-up.
     """

    _inherit = 'res.users'

    password_hint = fields.Char(string='Password Hint',
                                help='This field stores the password hint '
                                     'provided during sign-up.')
