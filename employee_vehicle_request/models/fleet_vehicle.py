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
#############################################################################
from odoo import fields, models


class FleetVehicle(models.Model):
    """
    Inherited model for extending fleet vehicles with reserved time tracking.

    This class extends the 'fleet.vehicle' model to add a 'reserved_time_ids'
    field to associate reserved time periods for the vehicle.
    """
    _inherit = 'fleet.vehicle'

    reserved_time_ids = fields.One2many('fleet.reserved',
                                        'reserved_obj_id',
                                        string='Reserved Time', readonly=True,
                                        help="Reserved Time")
