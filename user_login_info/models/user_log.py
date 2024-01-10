# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu KP (<https://www.cybrosys.com>)
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
from odoo import models, fields


class UserLog(models.Model):
    """This model used to create the user login records"""
    _name = 'user.log'
    _description = 'User Log'
    _rec_name = 'user_id'

    user_id = fields.Many2one('res.users', string='User',
                              help='Logged in user name',
                              ondelete="cascade", readonly=True)
    image = fields.Binary(string='Image', help='Logged user image',
                          readonly=True)
    secure = fields.Boolean(string='Unknown User', default=False,
                            help='Will show this field if the user enter '
                                 'wrong credential')
