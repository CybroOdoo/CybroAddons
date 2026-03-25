# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:  Faiz KC (odoo@cybrosys.com)
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
