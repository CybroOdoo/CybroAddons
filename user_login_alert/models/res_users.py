# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohammed Dilshad Tk (odoo@cybrosys.com)
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
from odoo import fields, models


class ResUsers(models.Model):
    """Inherits 'res.users' to add fields"""
    _inherit = 'res.users'

    last_logged_ip = fields.Char(string='IP', help="User lastly login Ip "
                                                   "address")
    last_logged_browser = fields.Char(string='Browser',
                                      help="User lastly login browser")
    last_logged_os = fields.Char(string='OS',
                                 help="User lastly login Operating system")
