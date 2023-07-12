# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sreenath K, Shafna K (odoo@cybrosys.com)
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
################################################################################
from odoo import fields, models


class HrAttendances(models.Model):
    """Inherits HR Attendance model"""
    _inherit = 'hr.attendance'

    checkin_address = fields.Char(string='Check In Address', store=True,
                                  help="Check in address of the User")
    checkout_address = fields.Char(string='Check Out Address', store=True,
                                   help="Check out address of the User")
    checkin_latitude = fields.Char(string='Check In Latitude', store=True,
                                   help="Check in latitude of the User")
    checkout_latitude = fields.Char(string='Check Out Latitude', store=True,
                                    help="Check out latitude of the User")
    checkin_longitude = fields.Char(string='Check In Longitude', store=True,
                                    help="Check in longitude of the User")
    checkout_longitude = fields.Char(string='Check Out Longitude', store=True,
                                     help="Check out longitude of the User")
    checkin_location = fields.Char(string='Check In Location Link', store=True,
                                   help="Check in location link of the User")
    checkout_location = fields.Char(string='Check Out Location Link', store=True,
                                    help="Check out location link of the User")
