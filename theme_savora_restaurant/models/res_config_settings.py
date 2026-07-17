# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
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
from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    """
    Inherit res.config.settings to add restaurant reservation configuration
    fields.
    """
    _inherit = 'res.config.settings'

    reservation_start_time = fields.Float(
        string="Reservation Start Time",
        config_parameter='restaurant.reservation_start_time',
        default=17.0,
        help="Specify the starting time for restaurant reservations."
    )
    reservation_end_time = fields.Float(
        string="Reservation End Time",
        config_parameter='restaurant.reservation_end_time',
        default=23.0,
        help="Specify the ending time for restaurant reservations."
    )
    reservation_slot_interval = fields.Integer(
        string="Slot Interval (Minutes)",
        config_parameter='restaurant.reservation_slot_interval',
        default=30,
        help="Specify the interval between reservation slots in minutes."
    )
