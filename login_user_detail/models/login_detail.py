# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
#
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
###############################################################################
from odoo import fields, models


class LoginDetail(models.Model):
    """ Class for the model login_detail contains fields related to
     the model."""
    _name = 'login.detail'
    _description = 'Login Detail'

    name = fields.Char(string="User Name", help="Name of logged in user")
    date_time = fields.Datetime(
        string="Login Date And Time",
        default=lambda self: fields.datetime.now(),
        help="Date and time of log in")
    ip_address = fields.Char(string="IP Address", help="IP address of login")
