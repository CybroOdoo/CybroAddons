# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class WMContainer(models.Model):
    """Extends Container Type with collection point allocation and tracking."""
    _inherit = 'wm.container.type'

    collection_point_id = fields.Many2one('wm.collection.point', string='Collection Point')


class FleetVehicle(models.Model):
    """Extends Fleet Vehicle with waste payload capacity, container type, and route tracking."""
    _inherit = 'fleet.vehicle'

    wm_capacity_volume = fields.Float(string='Volume Capacity (m³)', help='Maximum volume capacity of the vehicle in m³')
    wm_capacity_weight = fields.Float(string='Weight Capacity (kg)', help='Maximum payload weight capacity in kg')
    wm_container_id = fields.Many2one('wm.container.type', string='Container Type', help='Primary container type fitted on vehicle')
    pollution_cert_expiry = fields.Date(string='Pollution Certificate Expiry', help='Expiry date of pollution certificate')
    fitness_cert_expiry = fields.Date(string='Fitness Certificate Expiry', help='Expiry date of fitness certificate')
    insurance_expiry = fields.Date(string='Insurance Policy Expiry', help='Expiry date of vehicle insurance policy')
    wm_is_running = fields.Boolean(string='Is Running', help='Provides information about is running', compute='_compute_wm_is_running')

    def _compute_wm_is_running(self):
        """
        Determine whether this fleet vehicle is currently assigned to an active
        (dispatched or in-progress) waste collection route, locking it from
        concurrent route assignment.
        """
        for vehicle in self:
            running_routes = self.env['wm.route'].search_count([
                ('vehicle_id', '=', vehicle.id),
                ('state', '=', 'running')
            ])
            running_orders = self.env['wm.collection.order'].search_count([
                ('vehicle_id', '=', vehicle.id),
                ('state', 'in', ['dispatched', 'in_progress'])
            ])
            vehicle.wm_is_running = bool(running_routes > 0 or running_orders > 0)
