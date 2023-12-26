# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohamed Muzammil VP(odoo@cybrosys.com)
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
from odoo import fields, models


class FleetVehicleLogServices(models.Model):
    """Inherit fleet service add sub service types"""
    _inherit = 'fleet.vehicle.log.services'

    fleet_service_id = fields.Many2one(
        'fleet.vehicle.log.services', help='Fleet service',
        string='Fleet service')
    sub_service_ids = fields.One2many(
        'fleet.service.inspection', 'service_id', help='Sub Service Lines',
        string='Sub Service Lines')
    inspection_reference_id = fields.Many2one(
        'fleet.vehicle.log.services', string='Inspection Reference',
        help='Inspection Reference')
    inspection_name = fields.Char(
        string='Inspection', help='Vehicle Inspection name')
