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
        'salon.chair', string="Booking Chairs", default=lambda self: self.booking_chairs(),
        help="Booking chairs")
    salon_holiday_ids = fields.Many2many('salon.holiday', string="Holidays",
                                         default=lambda self: self.return_holidays(),
                                         help="Holidays of salon")

    def execute(self):
        """Update boolean fields of holiday and chair"""
        chair_model = self.env['salon.chair']
        chair_model.search([
            ('id', 'not in', self.salon_booking_chair_ids.ids),
            ('active_booking_chairs', '=', True),
        ]).write({'active_booking_chairs': False})
        self.salon_booking_chair_ids.write({'active_booking_chairs': True})
        holiday_model = self.env['salon.holiday']
        holiday_model.search([
            ('id', 'not in', self.salon_holiday_ids.ids),
            ('holiday', '=', True),
        ]).write({'holiday': False})
        self.salon_holiday_ids.write({'holiday': True})
