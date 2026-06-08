# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Swaraj R(odoo@cybrosys.com)
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
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class TimetablePeriod(models.Model):
    """Manages the period details """
    _name = 'timetable.period'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Timetable Period'

    name = fields.Char(string="Name", required=True, help="Enter Period Name")
    time_from = fields.Float(string='From', required=True,
                             help="Start and End time of Period.")
    time_to = fields.Float(string='To', required=True,
                           help="Start and End time of Period.")
    company_id = fields.Many2one(
        'res.company', string='Company', help="Current company",
        default=lambda self: self.env.company)

    @api.constrains('time_from', 'time_to')
    def _check_time_range(self):
        """ Function to check the time range of the period """
        for record in self:
            if record.time_from < 9 or record.time_to > 19:
                raise ValidationError(
                    "The time must be between 09:00 and 19:00."
                )
            if record.time_from >= record.time_to:
                raise ValidationError(
                    "The start time must be less than the end time."
                )
