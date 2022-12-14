# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-November Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import logging
import subprocess
import sys
from odoo import models, fields

py_v = "python%s.%s" % (sys.version_info.major, sys.version_info.minor)

_logger = logging.getLogger(__name__)
try:
    from getmac import get_mac_address as gma
except ImportError:
    _logger.info('\n There was no such module named -getmac- installed')
    _logger.info('xxxxxxxxxxxxxxxx installing getmac xxxxxxxxxxxxxx')
    subprocess.check_call([py_v, "-m", "pip", "install", "--user", "getmac"])
    from getmac import get_mac_address as gma


class ResUsers(models.Model):
    _inherit = 'res.users'

    mac_address_ids = fields.One2many('mac.address', 'res_user_id',
                                      string='Allowed MAC IDs')
    mac_address_login_toggle = fields.Boolean(default=False,
                                              string="Enable MAC Address Login Validation")
    current_mac_address = fields.Char(compute='_get_mac',
                                      string="Your Public Mac address")

    def _get_mac(self):
        for rec in self:
            rec.current_mac_address = gma()

    def enable_validation(self):
        for rec in self:
            if not rec.mac_address_login_toggle:
                rec.mac_address_login_toggle = True

    def disable_validation(self):
        for rec in self:
            if rec.mac_address_login_toggle:
                rec.mac_address_login_toggle = False


class MacAddress(models.Model):
    _name = 'mac.address'

    name = fields.Char(string="Description")
    mac_address = fields.Char(string="MAC Address")
    res_user_id = fields.Many2one('res.users')
