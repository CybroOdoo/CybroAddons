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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models

TIME_SELECTION = [
    (str(hour), f"{hour % 12 or 12}:00 {'AM' if hour < 12 else 'PM'}")
    for hour in range(24)
]


class SlotTime(models.Model):
    """Slot time model"""
    _name = 'slot.time'
    _description = 'Delivery time'

    name = fields.Char(string='Slot', help="Slot Name", required=True)
    slot_type = fields.Selection(
        [('home', 'Home Hours'), ('office', 'Office Hours')],
        help="Slot will be shown based on this slot type")
    time_from = fields.Selection(TIME_SELECTION, help="From time",
                                 required=True)
    time_to = fields.Selection(TIME_SELECTION, help="To time", required=True)
