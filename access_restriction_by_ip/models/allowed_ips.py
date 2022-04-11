# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Niyas Raphy(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import api, models, fields, _
from odoo.exceptions import ValidationError
import ipaddress


class ResUsersInherit(models.Model):
    _inherit = 'res.users'

    allowed_ips = fields.One2many('allowed.ips', 'users_ip', string='IP')


class AllowedIPs(models.Model):
    _name = 'allowed.ips'

    users_ip = fields.Many2one('res.users', string='IP')
    ip_address = fields.Char(string='Allowed IP')

    @api.constrains('ip_address')
    def _check_ip(self):
        for rec in self:
            if rec.ip_address:
                try:
                    ipaddress.ip_network(rec.ip_address)
                except ValueError:
                    raise ValidationError(_('Please enter a valid IP address or'
                                            ' subnet mask (%s)' % rec.ip_address))
