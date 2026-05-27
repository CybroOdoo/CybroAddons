# -*- coding: utf-8 -*-
#############################################################################
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

    name = fields.Char(
        string='Time Slot',
        default='New',
        readonly=True,
        help='Mention the name of the Time slots'
    )
    movie_time = fields.Char(
        string='Movie Time',
        help='Mention the slot time'
    )

    _name_uniq = models.Constraint('unique(name)', "Name should be unique")

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to update name based on movie_time."""
        for vals in vals_list:
            movie_time = vals.get('movie_time')
            if not movie_time:
                raise ValidationError('Please mention time!!')

            # Convert 24h → 12h format
            try:
                vals['name'] = datetime.strptime(movie_time, "%H:%M").strftime("%I:%M %p")
            except ValueError:
                raise ValidationError("Invalid time format! Use HH:MM")

            # Convert ":" → "." for storing
            vals['movie_time'] = movie_time.replace(":", ".")

        return super().create(vals_list)

    def write(self, vals):
        """Override write to update name when movie_time changes."""
        movie_time = vals.get('movie_time')
        if movie_time:
            try:
                vals['name'] = datetime.strptime(movie_time, "%H:%M").strftime("%I:%M %p")
            except ValueError:
                raise ValidationError("Invalid time format! Use HH:MM")

            vals['movie_time'] = movie_time.replace(":", ".")

        return super(TimeSlots, self).write(vals)
