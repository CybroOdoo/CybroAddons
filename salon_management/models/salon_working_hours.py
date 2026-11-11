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
from odoo import fields, models


def _time_selection():
    """Generate AM/PM time slots every 30 minutes for a full day."""
    slots = []
    for h in range(24):
        for m in (0, 30):
            if h == 0:
                label = '12:%02d AM' % m
            elif h < 12:
                label = '%d:%02d AM' % (h, m)
            elif h == 12:
                label = '12:%02d PM' % m
            else:
                label = '%d:%02d PM' % (h - 12, m)
            slots.append((label, label))
    return slots


class SalonWorkingHours(models.Model):
    """'Salon working hours' to store working hours of salon"""
    _name = 'salon.working.hours'
    _description = 'Salon Working Hours'

    name = fields.Char(help="Name of working hours",
                       required=True)
    from_time = fields.Selection(
        selection=_time_selection(),
        string="Starting Time",
        default='9:00 AM',
        help="Starting time of salon")
    to_time = fields.Selection(
        selection=_time_selection(),
        string="Closing Time",
        default='6:00 PM',
        help="Salon work ending time")
