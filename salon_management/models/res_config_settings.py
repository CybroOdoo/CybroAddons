# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohammed Dilshad Tk (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """Inherits 'res.config.settings' to add salon records"""
    _inherit = 'res.config.settings'

    @api.model
    def booking_chairs(self):
        """Returns active chairs for booking"""
        return self.env['salon.chair'].search(
            [('active_booking_chairs', '=', True)])

    @api.model
    def return_holidays(self):
        """Returns holiday"""
        return self.env['salon.holiday'].search([('holiday', '=', True)])

    salon_booking_chair_ids = fields.Many2many(
        'salon.chair', string="Booking Chairs", default=booking_chairs,
        help="Booking chairs")
    salon_holiday_ids = fields.Many2many('salon.holiday', string="Holidays",
                                         default=return_holidays,
                                         help="Holidays of salon")

    def execute(self):
        """Update boolean fields of holiday and chair"""
        book_chair = []
        for chairs in self.salon_booking_chair_ids:
            book_chair.append(chairs.id)
        for chair in self.env['salon.chair'].search([]):
            if chair.id in book_chair:
                chair.active_booking_chairs = True
            else:
                chair.active_booking_chairs = False
        holiday = []
        for days in self.salon_holiday_ids:
            holiday.append(days.id)
        for records in self.env['salon.holiday'].search([]):
            if records.id in holiday:
                records.holiday = True
            else:
                records.holiday = False
