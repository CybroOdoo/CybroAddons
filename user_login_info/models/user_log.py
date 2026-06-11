# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sruthi Pavithran (<https://www.cybrosys.com>)
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
from odoo import fields, models


class UserLog(models.Model):
    """Model to store user login information and captured images."""
    _name = 'user.log'
    _description = 'User Log'
    _rec_name = 'user_id'
    _order = 'create_date desc'

    user_id = fields.Many2one(
        'res.users', string='User',
        help='The user who attempted the login.',
        ondelete="cascade", readonly=True
    )
    image = fields.Binary(
        string='Captured Image',
        help='Image captured from the user\'s camera during login.',
        attachment=True
    )
    is_secure = fields.Boolean(
        string='Unknown User', default=False,
        help='Indicates if the login attempt was made by an unknown user '
             'or with incorrect credentials.'
    )
