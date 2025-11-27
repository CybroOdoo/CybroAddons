# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
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


class AllowedIPs(models.Model):
    """Class for the model allowed_ips. Contains fields for record users and
    their Allowed IPs."""
    _name = 'allowed.ips'
    _description = "Allowed IPs"

    user_ip_id = fields.Many2one('res.users', string='User',
                                 help='User associated with the allowed IP')
    ip_address = fields.Char(string='Allowed IP', help='The allowed IP address'
                                                       ' for the User.')
