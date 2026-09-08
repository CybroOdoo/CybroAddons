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
from odoo import api, fields, models


class WmServiceZone(models.Model):
    """Geographic or operational zone used to automatically match collection points to routes."""
    _name = 'wm.service.zone'
    _description = 'Service Zone'
    _order = 'name'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', help='Short code, e.g. used on route names/reports')
    color = fields.Integer(string='Color')
    default_vehicle_id = fields.Many2one(
        'fleet.vehicle', string='Default Vehicle',
        help='Vehicle used when a new route is auto-created for this zone, if available and roadworthy.')
    default_driver_id = fields.Many2one(
        'res.partner', string='Default Driver',
        help='Driver used when a new route is auto-created for this zone.')
    max_stops_per_route = fields.Integer(
        string='Max Stops per Route', default=25,
        help='Once a route for this zone/day reaches this many stops, a new route is created instead of adding more.')
    active = fields.Boolean(string='Active', default=True)
    collection_point_ids = fields.One2many('wm.collection.point', 'zone_id', string='Collection Points')
    collection_point_count = fields.Integer(string='Collection Points', compute='_compute_collection_point_count', store=True)

    @api.onchange('default_vehicle_id')
    def _onchange_default_vehicle_id(self):
        """
        Automatically fetch the assigned driver from the selected default vehicle.
        """
        if self.default_vehicle_id and self.default_vehicle_id.driver_id:
            self.default_driver_id = self.default_vehicle_id.driver_id
        elif not self.default_vehicle_id:
            self.default_driver_id = False

    @api.depends('collection_point_ids')
    def _compute_collection_point_count(self):
        """
        Compute the total number of associated collection point records linked
        to this WmServiceZone to update smart buttons and summary badges.
        """
        for zone in self:
            zone.collection_point_count = len(zone.collection_point_ids)
