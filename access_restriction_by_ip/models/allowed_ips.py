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
import ipaddress

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AllowedIPs(models.Model):
    """Class for the model allowed_ips. Contains fields for record users and
    their Allowed IPs."""
    _name = 'allowed.ips'
    _description = "Allowed IPs"
    _rec_name = 'ip_address'

    user_ip_id = fields.Many2one('res.users', string='User',
                                 required=True, ondelete='cascade',
                                 help='User associated with the allowed IP')
    ip_address = fields.Char(string='Allowed IP', required=True,
                             help='The allowed IP address for the User.')

    _user_ip_unique = models.Constraint(
        'UNIQUE(user_ip_id, ip_address)',
        'This IP address is already allowed for the user.',
    )

    @api.constrains('ip_address')
    def _check_ip_address(self):
        """Only valid IPv4 / IPv6 addresses can be saved."""
        for record in self:
            try:
                ipaddress.ip_address((record.ip_address or '').strip())
            except ValueError:
                raise ValidationError(self.env._(
                    "'%s' is not a valid IP address.", record.ip_address))
