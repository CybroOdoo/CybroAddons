# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from datetime import datetime
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class TimeSlots(models.Model):
    """
        Time slots model for managing different time slots for show.
    """
    _name = 'time.slots'
    _description = 'Time Slots'

    name = fields.Char(string='Time Slot', default='New',
                       readonly=True, help='Mention the name of the Time slots')
    movie_time = fields.Char(string='Movie Time', help='Mention the slot time')

    _sql_constraints = [
        ('name_uniq', 'unique(name)', "Name should be unique")
    ]

    @api.model
    def create(self, vals):
        """Supering create function to update name."""
        if vals['movie_time']:
            vals['name'] = datetime.strptime(vals['movie_time'], "%H:%M").strftime("%I:%M %p")
            vals['movie_time'] = vals['movie_time'].replace(":", ".")
        else:
            raise ValidationError('Please mention time!!')
        return super().create(vals)

    @api.model
    def write(self, vals):
        """Supering write function to update name."""
        if vals['movie_time']:
            vals['name'] = datetime.strptime(vals['movie_time'],
                                             "%H:%M").strftime("%I:%M %p")
            vals['movie_time'] = vals['movie_time'].replace(":", ".")
        res = super(TimeSlots, self).write(vals)
        return res
