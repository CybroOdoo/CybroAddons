# -- coding: utf-8 --
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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


class SalonWorkingHours(models.Model):
    """'Salon working hours' to store working hours of salon"""
    _name = 'salon.working.hours'
    _description = 'Salon Working Hours'

    name = fields.Char(string="Name", help="Name of working hours", required=True)
    from_time = fields.Float(string="Starting Time", help="Starting time of "
                                                          "salon")
    to_time = fields.Float(string="Closing Time", help="Salon work ending time")
