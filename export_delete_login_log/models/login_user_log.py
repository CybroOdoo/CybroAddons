# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
from itertools import chain
from odoo import fields, models

USER_PRIVATE_FIELDS = ['password']
concat = chain.from_iterable


class LoginLog(models.Model):
    """Model to log information about user login"""
    _name = 'login.log'
    _description = 'Login Log'

    name = fields.Char(string="User Name", readonly=True,
                       help="The name of the user who logged in.")
    date_time = fields.Datetime(string="Login Date And Time",
                                default=lambda self: fields.datetime.now(),
                                readonly=True,
                                help="The exact date and time when the user "
                                     "successfully logged in. "
                                )
    ip_address = fields.Char(string="IP Address", readonly=True,
                             help="The IP address from which the user logged in.")
    geo_loc = fields.Char(string="Latitude / Longitude", readonly=True,
                          help="Data is fetched using users IP address so the "
                               "it may not be 100% precise")
    address = fields.Char(string="Address", readonly=True,
                          help="Data is fetched using users IP address so the "
                               "it may not be 100% precise")
    postal_code = fields.Char(string="Postal Code", readonly=True,
                              help="Data is fetched using users IP address so "
                                   "the it may not be 100% precise")
    time_zone = fields.Char(string="Time Zone", readonly=True,
                            help="Data is fetched using users IP address so "
                                 "the it may not be 100% precise")
    remark = fields.Text(string="Remarks",
                         help="Remark is added when there is an error in the "
                              "IP Address or other values, Error Reason: "
                              "\n1) RateLimited: Free daily quota exceeded"
                              "\n2) Invalid IP Address: The IP address used "
                              "by the User is Invalid"
                              "\n3) Reserved IP Address: The IP address used "
                              "by the User is Reserved")
