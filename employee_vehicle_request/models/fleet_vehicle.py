# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import fields, models


class FleetVehicle(models.Model):
    """
    Inherited model for extending fleet vehicles with availability tracking.

    This class extends the 'fleet.vehicle' model to add a 'check_availability'
    field to track vehicle availability and a 'reserved_time_ids' field to
    associate reserved time periods for the vehicle.
    """
    _inherit = 'fleet.vehicle'

    check_availability = fields.Boolean(default=True, copy=False,
                                        string="Check Availability",
                                        help="Check availability")
    reserved_time_ids = fields.One2many('fleet.reserved',
                                        'reserved_obj_id',
                                        string='Reserved Time', readonly=True,
                                        ondelete='cascade',
                                        help="Reserved Time")
