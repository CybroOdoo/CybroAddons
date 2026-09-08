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
import json
import logging
import math
from datetime import datetime, time

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


def _haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance in kilometers between two points on
    Earth.
    """
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def _solve_tsp_shortest_path(lines_with_coords):
    """
    Given a list of tuples (line_record, lat, lon),
    returns a reordered list of line_records minimizing total travel distance
    using Nearest Neighbor heuristic followed by 2-opt local search optimization.
    """
    if len(lines_with_coords) <= 2:
        return [item[0] for item in lines_with_coords]

    n = len(lines_with_coords)
    dist_matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                dist_matrix[i][j] = _haversine_distance(
                    lines_with_coords[i][1], lines_with_coords[i][2],
                    lines_with_coords[j][1], lines_with_coords[j][2]
                )

    # 1. Nearest Neighbor starting from point 0
    unvisited = set(range(1, n))
    current = 0
    path = [0]
    while unvisited:
        next_node = min(unvisited, key=lambda node: dist_matrix[current][node])
        path.append(next_node)
        unvisited.remove(next_node)
        current = next_node

    # 2. 2-opt local search optimization to eliminate edge crossings
    improved = True

    def calculate_total_dist(p):
        """
        Sum the distances between ordered collection points on this route using
        configured geo-coordinates, computing the estimated total route
        distance for driver briefings.
        """
        return sum(dist_matrix[p[k]][p[k + 1]] for k in range(len(p) - 1))

    best_dist = calculate_total_dist(path)
    while improved:
        improved = False
        for i in range(1, n - 1):
            for j in range(i + 1, n):
                new_path = path[:i] + path[i:j + 1][::-1] + path[j + 1:]
                new_dist = calculate_total_dist(new_path)
                if new_dist < best_dist - 1e-6:
                    path = new_path
                    best_dist = new_dist
                    improved = True
                    break
            if improved:
                break

    return [lines_with_coords[idx][0] for idx in path]


class SurveyUserInputExt(models.Model):
    """Extends Survey User Input with driver vehicle inspection workflow integration."""
    _inherit = 'survey.user_input'

    route_id = fields.Many2one('wm.route', string='Route')


class WmRoute(models.Model):
    """Waste collection route grouping ordered collection stops, assigned vehicle, driver, and schedule."""
    _name = 'wm.route'
    _description = 'Collection Route'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'wm.audit.mixin']

    name = fields.Char(string='Reference', help='Provides information about reference', required=True, copy=False, readonly=True, index=True, default=lambda self: 'New')
    sequence = fields.Integer(string='Sequence', help='Provides information about sequence', default=10)
    zone_id = fields.Many2one('wm.service.zone', string='Zone', tracking=True)
    use_route_zones = fields.Boolean(compute='_compute_use_settings')
    date = fields.Date(string='Date', help='Provides information about date', required=True, default=fields.Date.context_today)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)

    def _compute_use_settings(self):
        """
        Load route module feature flags (map integration, vehicle inspection
        requirements) from system configuration to control route planning and
        dispatch features.
        """
        use_zones = self.env['ir.config_parameter'].sudo().get_param('wm_collection.use_route_zones', 'False') in ('True', '1')
        for route in self:
            route.use_route_zones = use_zones

    valid_vehicle_ids = fields.Many2many('fleet.vehicle', compute='_compute_valid_vehicle_ids')
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', help='Provides information about vehicle')
    driver_id = fields.Many2one('res.partner', string='Driver', help='Provides information about driver')
    state = fields.Selection([
        ('to_start', 'To Start'),
        ('dispatched', 'Dispatched'),
        ('running', 'Running'),
        ('completed', 'Completed'),
    ], string='Status', default='to_start', tracking=True)
    is_ready_to_dispatch = fields.Boolean(
        string='Ready to Dispatch',
        compute='_compute_is_ready_to_dispatch',
        store=True,
        tracking=True,
        help="Indicates whether all prerequisites for route dispatching are met."
    )
    collection_order_ids = fields.One2many('wm.collection.order', 'route_id', string='Collection Orders')
    collection_order_count = fields.Integer(string='Collection Orders Count', compute='_compute_collection_order_count', store=True)
    waste_batch_ids = fields.One2many('waste.batch', 'route_id', string='Waste Batches')
    line_ids = fields.One2many('wm.route.line', 'route_id', string='Route Lines', help='Provides information about route lines')
    selected_point_ids = fields.Many2many('wm.collection.point', compute='_compute_selected_point_ids')
    estimated_duration = fields.Float(string='Estimated Duration', help='Provides information about estimated duration')
    route_map_data = fields.Text(string='Route Map Data', help='Provides information about route map data', compute='_compute_route_map_data')
    driver_change_history_ids = fields.One2many('wm.driver.change.history', 'route_id', string='Driver Change History')
    driver_history_count = fields.Integer(string='Driver Changes', compute='_compute_driver_history_count', store=True)

    inspection_ids = fields.One2many('survey.user_input', 'route_id', domain=[('checklist_type', 'in', ['pre_trip', 'post_trip'])], string='Inspections')
    inspection_count = fields.Integer(compute='_compute_inspection_count', string='Inspection Count', store=True)
    is_inspected = fields.Boolean(
        compute='_compute_is_inspected',
        store=True,
        readonly=False,
        string='Inspection Passed',
        help='Indicates whether the latest vehicle pre-trip inspection passed. Can be toggled to re-enable inspection.'
    )
    fill_level_percentage = fields.Float(string='Fill Level (%)', compute='_compute_fill_level_percentage', store=True)

    @api.onchange('zone_id')
    def _onchange_zone_id(self):
        """
        When a service zone is selected on the route, automatically assign
        the zone's default vehicle and driver if configured.
        """
        if self.zone_id:
            if self.zone_id.default_vehicle_id:
                self.vehicle_id = self.zone_id.default_vehicle_id
                self.driver_id = self.zone_id.default_vehicle_id.driver_id or self.zone_id.default_driver_id
            elif self.zone_id.default_driver_id:
                self.driver_id = self.zone_id.default_driver_id

    @api.onchange('vehicle_id')
    def _onchange_vehicle_id(self):
        """
        Method to default the route driver from the selected vehicle.
        """
        self.driver_id = self.vehicle_id.driver_id if self.vehicle_id else False

    @api.depends('inspection_ids')
    def _compute_inspection_count(self):
        """
        Count the vehicle maintenance checklist inspections linked to this route.
        """
        for route in self:
            route.inspection_count = len(route.inspection_ids)

    @api.depends('inspection_ids.state', 'inspection_ids.checklist_type', 'inspection_ids.scoring_success', 'inspection_ids.create_date', 'vehicle_id')
    def _compute_is_inspected(self):
        """
        Determine whether the latest vehicle pre-trip inspection passed for this route,
        enabling pre-dispatch inspection enforcement.
        """
        for route in self:
            done_pre_trips = route.inspection_ids.filtered(
                lambda i: i.checklist_type == 'pre_trip' and i.state == 'done'
            ).sorted(key=lambda i: (i.create_date or fields.Datetime.now(), i.id), reverse=True)
            latest_pre_trip = done_pre_trips[:1]
            if latest_pre_trip:
                route.is_inspected = bool(getattr(latest_pre_trip, 'scoring_success', True))
            else:
                maint_pre_trips = self.env['wm.vehicle.maintenance.checklist'].search([
                    ('vehicle_id', '=', route.vehicle_id.id),
                    ('checklist_type', '=', 'pre_trip'),
                    ('state', '=', 'checked')
                ], limit=1) if route.vehicle_id else False
                route.is_inspected = bool(maint_pre_trips)

    @api.depends('collection_order_ids.confirmed_weight', 'vehicle_id.wm_capacity_weight')
    def _compute_fill_level_percentage(self):
        """
        Estimate the current vehicle fill level as a percentage by summing
        collected waste weights on the route relative to the assigned vehicle's
        maximum payload capacity.
        """
        for route in self:
            if route.vehicle_id and route.vehicle_id.wm_capacity_weight > 0:
                total_confirmed = sum(route.collection_order_ids.mapped('confirmed_weight'))
                route.fill_level_percentage = (total_confirmed / route.vehicle_id.wm_capacity_weight) * 100
            else:
                route.fill_level_percentage = 0.0

    @api.depends(
        'state', 'vehicle_id', 'driver_id', 'line_ids',
        'collection_order_ids.partner_id', 'collection_order_ids.collection_point_id',
        'collection_order_ids.scheduled_start', 'collection_order_ids.scheduled_end',
        'is_inspected'
    )
    def _compute_is_ready_to_dispatch(self):
        """
        Determine if the route has all prerequisites met for dispatch: an
        assigned driver, a valid vehicle with a current inspection, and at
        least one confirmed collection order.
        """
        for route in self:
            if route.state != 'to_start':
                route.is_ready_to_dispatch = False
                continue
            has_vehicle = bool(route.vehicle_id)
            has_driver = bool(route.driver_id)
            has_stops = bool(route.line_ids)
            has_pretrip = not route.vehicle_id or route.is_inspected

            orders_valid = bool(route.collection_order_ids)
            for order in route.collection_order_ids:
                if not (order.partner_id and order.collection_point_id and order.scheduled_start and order.scheduled_end):
                    orders_valid = False
                    break

            route.is_ready_to_dispatch = has_vehicle and has_driver and has_stops and has_pretrip and orders_valid

    @api.model
    def _cron_auto_assign_orders_to_routes(self):
        """
        Daily cron (00:15) to group draft collection orders by zone and date,
        assigning them to under-capacity routes or creating new ones.
        """
        use_zones = self.env['ir.config_parameter'].sudo().get_param('wm_collection.use_route_zones', 'False') in ('True', '1')
        if not use_zones:
            return

        draft_orders = self.env['wm.collection.order'].search([
            ('state', '=', 'draft'),
            ('route_id', '=', False),
            ('collection_point_id.zone_id', '!=', False)
        ])
        if not draft_orders:
            return

        today = fields.Date.context_today(self)
        grouped_orders = {}
        for order in draft_orders:
            zone = order.collection_point_id.zone_id
            sched_date = order.scheduled_start.date() if order.scheduled_start else today
            key = (zone, sched_date)
            grouped_orders.setdefault(key, []).append(order)

        routes_to_optimize = self.env['wm.route']

        for (zone, sched_date), orders in grouped_orders.items():
            max_stops = zone.max_stops_per_route or 25
            existing_routes = self.search([
                ('zone_id', '=', zone.id),
                ('date', '=', sched_date),
                ('state', '=', 'to_start')
            ])

            current_route = False
            for r in existing_routes:
                if len(r.line_ids) < max_stops:
                    current_route = r
                    break

            if not current_route:
                current_route = self.create({
                    'name': 'New',
                    'zone_id': zone.id,
                    'date': sched_date,
                    'vehicle_id': zone.default_vehicle_id.id if zone.default_vehicle_id else False,
                    'driver_id': zone.default_driver_id.id if zone.default_driver_id else False,
                    'state': 'to_start',
                })

            for order in orders:
                if len(current_route.line_ids) >= max_stops:
                    current_route = self.create({
                        'name': 'New',
                        'zone_id': zone.id,
                        'date': sched_date,
                        'vehicle_id': zone.default_vehicle_id.id if zone.default_vehicle_id else False,
                        'driver_id': zone.default_driver_id.id if zone.default_driver_id else False,
                        'state': 'to_start',
                    })

                order.write({
                    'route_id': current_route.id,
                    'vehicle_id': current_route.vehicle_id.id if current_route.vehicle_id else order.vehicle_id.id,
                    'driver_id': current_route.driver_id.id if current_route.driver_id else order.driver_id.id,
                })
                if not current_route.line_ids.filtered(lambda l: l.collection_point_id == order.collection_point_id):
                    seq = max(current_route.line_ids.mapped('sequence') or [0]) + 10
                    self.env['wm.route.line'].create({
                        'route_id': current_route.id,
                        'collection_point_id': order.collection_point_id.id,
                        'sequence': seq
                    })
            routes_to_optimize |= current_route

        for route in routes_to_optimize:
            route.action_optimize_route()

    @api.model
    def _cron_auto_dispatch_ready_routes(self):
        """
        Hourly cron evaluating all routes in 'to_start' state and
        auto-dispatching those that are ready.
        """
        to_start_routes = self.search([('state', '=', 'to_start')])
        for route in to_start_routes:
            route._compute_is_ready_to_dispatch()

        ready_routes = self.search([
            ('state', '=', 'to_start'),
            ('is_ready_to_dispatch', '=', True)
        ])

        enabled = self.env['ir.config_parameter'].sudo().get_param('wm_collection.auto_dispatch_enabled', 'False') == 'True'
        if enabled and ready_routes:
            for route in ready_routes:
                route.action_dispatch_route()
                for order in route.collection_order_ids.filtered(lambda o: o.state == 'draft'):
                    order.action_dispatch()

    def action_inspect_vehicle(self):
        """
        Open the vehicle pre-trip inspection checklist wizard for the assigned
        vehicle, enforcing inspection completion before route dispatch is
        permitted.
        """
        self.ensure_one()
        survey = self.env['survey.survey'].search([('title', 'ilike', 'Pre-Trip')], limit=1)
        if survey and self.vehicle_id:
            checklist = self.env['survey.user_input'].create({
                'survey_id': survey.id,
                'checklist_type': 'pre_trip',
                'vehicle_id': self.vehicle_id.id,
                'route_id': self.id,
                'partner_id': self.driver_id.id if self.driver_id else self.env.user.partner_id.id,
            })
            return {
                'type': 'ir.actions.act_window',
                'name': 'Pre-Trip Inspection',
                'res_model': 'survey.user_input',
                'res_id': checklist.id,
                'view_mode': 'form',
                'target': 'current',
            }

    def action_view_inspections(self):
        """
        Open the list of vehicle inspection checklists associated with this
        route, allowing the dispatcher to verify pre-trip inspection compliance
        before dispatch.
        """
        self.ensure_one()
        return {
            'name': _('Inspections'),
            'type': 'ir.actions.act_window',
            'res_model': 'survey.user_input',
            'view_mode': 'list,form',
            'domain': [('route_id', '=', self.id), ('checklist_type', 'in', ['pre_trip', 'post_trip'])],
            'context': {'default_route_id': self.id},
        }

    def _check_route_rights(self):
        """
        Validate that the current user has the 'Dispatcher' or 'Fleet Manager'
        role before allowing route state transitions, preventing unauthorised
        dispatch or cancellation.
        """
        if not (self.env.user.has_group('wm_base.group_wm_dispatcher') or self.env.user.has_group('wm_base.group_wm_driver') or self.env.user.has_group('wm_base.group_wm_ops_manager') or self.env.is_admin()):
            raise UserError(_("You do not have permission to manage routes."))

    def action_dispatch_route(self):
        """
        Validate vehicle availability and driver assignment, then transition
        the route from 'planned' to 'dispatched', notifying the driver and
        updating fleet status.
        """
        self._check_route_rights()
        for route in self:
            if not route.line_ids:
                raise ValidationError(_("You cannot dispatch a route without any collection points. Please add at least one collection point in the Route Lines tab."))

            if route.vehicle_id and not route.is_inspected:
                raise ValidationError(_("Cannot dispatch route '%s': Vehicle '%s' has not passed pre-trip inspection. Please inspect the vehicle before dispatching.") % (route.name, route.vehicle_id.name))

            route.state = 'dispatched'

            # Move all collection orders for all collection points linked to this route to dispatched
            point_ids = route.line_ids.mapped('collection_point_id').ids
            if point_ids:
                domain = [
                    ('state', '=', 'draft'),
                    '|',
                        ('route_id', '=', route.id),
                        ('collection_point_id', 'in', point_ids)
                ]
            else:
                domain = [('route_id', '=', route.id), ('state', '=', 'draft')]

            orders = self.env['wm.collection.order'].search(domain)
            for order in orders:
                order_vals = {'state': 'dispatched', 'route_id': route.id}
                if route.vehicle_id:
                    order_vals['vehicle_id'] = route.vehicle_id.id
                if route.driver_id:
                    order_vals['driver_id'] = route.driver_id.id
                order.with_context(programmatic_state_change=True).write(order_vals)

    def action_start_route(self):
        """
        Record the actual route start time, transition the route to
        'in_progress', and update all linked collection orders to 'dispatched'
        state.
        """
        self._check_route_rights()
        for route in self:
            route.state = 'running'
            point_ids = route.line_ids.mapped('collection_point_id').ids
            if point_ids:
                domain = [
                    ('state', 'in', ('draft', 'dispatched')),
                    '|',
                        ('route_id', '=', route.id),
                        ('collection_point_id', 'in', point_ids)
                ]
            else:
                domain = [('route_id', '=', route.id), ('state', 'in', ('draft', 'dispatched'))]

            orders = self.env['wm.collection.order'].search(domain)
            for order in orders:
                order_vals = {'state': 'in_progress', 'route_id': route.id}
                if route.vehicle_id:
                    order_vals['vehicle_id'] = route.vehicle_id.id
                if route.driver_id:
                    order_vals['driver_id'] = route.driver_id.id
                order.with_context(programmatic_state_change=True).write(order_vals)

    def action_complete_route(self):
        """
        Finalise the route by validating that all collection orders are
        completed or missed, recording actual end time, computing distance, and
        transitioning to 'completed'.
        """
        self._check_route_rights()
        for route in self:
            domain = [('route_id', '=', route.id), ('state', 'in', ('draft', 'dispatched', 'in_progress'))]
            pending_orders = self.env['wm.collection.order'].search(domain)
            if pending_orders:
                raise ValidationError(_(
                    "Cannot complete route '%(route_name)s': %(count)d collection order(s) are still pending. "
                    "All collection orders on the route must be marked as Completed, Missed, or Cancelled before completing the route."
                ) % {
                    'route_name': route.name,
                    'count': len(pending_orders),
                })

            route.state = 'completed'
            route.action_create_route_category_batches()
            if route.vehicle_id:
                survey = self.env['survey.survey'].search([('title', 'ilike', 'Post-Trip')], limit=1)
                if survey:
                    self.env['survey.user_input'].create({
                        'survey_id': survey.id,
                        'checklist_type': 'post_trip',
                        'vehicle_id': route.vehicle_id.id,
                        'route_id': route.id,
                        'partner_id': route.driver_id.id if route.driver_id else self.env.user.partner_id.id,
                    })

    def action_create_route_category_batches(self):
        """
        Create consolidated category-level Waste Batches for the entire route
        across all completed collection orders.
        """
        self.ensure_one()
        completed_orders = self.collection_order_ids.filtered(lambda o: o.state == 'completed')
        if not completed_orders:
            return self.env['waste.batch']

        lines_by_category = {}
        for order in completed_orders:
            for line in order.order_line_ids:
                if line.category_id:
                    lines_by_category.setdefault(line.category_id, []).append((order, line))

        warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1) or self.env['stock.warehouse'].search([], limit=1)
        location = warehouse.lot_stock_id if warehouse and warehouse.lot_stock_id else self.env['stock.location'].search([('usage', '=', 'internal')], limit=1)

        created_batches = self.env['waste.batch']
        for category, items in lines_by_category.items():
            orders_involved = self.env['wm.collection.order'].concat(*list({_ord for _ord, line in items}))

            # Search for an existing open (Draft) route batch for this category
            existing_batch = self.env['waste.batch'].search([
                ('route_id', '=', self.id),
                ('category_id', '=', category.id),
                ('status', '=', 'draft'),
                ('batch_type', '=', 'collection'),
            ], limit=1)

            if existing_batch:
                # Identify newly completed orders that haven't been linked to this batch yet
                new_orders = orders_involved - existing_batch.collection_order_ids
                if new_orders:
                    new_items = [item for item in items if item[0] in new_orders]
                    add_weight = sum(line.weight for _ord, line in new_items)

                    existing_batch.write({
                        'draft_quantity': existing_batch.draft_quantity + add_weight,
                        'intake_weight': existing_batch.intake_weight + add_weight,
                        'collection_order_ids': [(4, o.id) for o in new_orders],
                    })

                    for _ord, line in new_items:
                        if line.product_id:
                            batch_line = existing_batch.line_ids.filtered(lambda bl: bl.product_id == line.product_id)
                            if batch_line:
                                batch_line[0].write({'quantity': batch_line[0].quantity + (line.weight or 1.0)})
                            else:
                                self.env['waste.batch.line'].create({
                                    'batch_id': existing_batch.id,
                                    'product_id': line.product_id.id,
                                    'quantity': line.weight or 1.0,
                                    'category_id': category.id,
                                })

                all_orders = existing_batch.collection_order_ids
                if len(all_orders) == 1:
                    existing_batch.collection_order_id = all_orders.id
                else:
                    existing_batch.collection_order_id = False

                created_batches |= existing_batch
            else:
                total_weight = sum(line.weight for _ord, line in items)
                product_qty = {}
                for _ord, line in items:
                    if line.product_id:
                        product_qty[line.product_id] = product_qty.get(line.product_id, 0.0) + (line.weight or 1.0)

                batch_lines = []
                for prod, qty in product_qty.items():
                    batch_lines.append((0, 0, {
                        'product_id': prod.id,
                        'quantity': qty,
                        'category_id': category.id,
                    }))

                batch_vals = {
                    'route_id': self.id,
                    'collection_order_ids': [(6, 0, orders_involved.ids)],
                    'category_id': category.id,
                    'draft_quantity': total_weight,
                    'intake_weight': total_weight,
                    'intake_date': fields.Datetime.now(),
                    'warehouse_id': warehouse.id if warehouse else False,
                    'location_id': location.id if location else False,
                    'status': 'draft',
                    'batch_type': 'collection',
                    'sorting_status': 'unsorted',
                }
                if len(orders_involved) == 1:
                    batch_vals['collection_order_id'] = orders_involved.id
                if batch_lines:
                    batch_vals['line_ids'] = batch_lines

                batch = self.env['waste.batch'].create(batch_vals)
                created_batches |= batch

        return created_batches

    def action_cancel_route(self):
        """
        Cancel the route and reset all linked collection orders back to
        'scheduled' state, releasing the vehicle and driver for reassignment.
        """
        self._check_route_rights()
        for route in self:
            route.state = 'to_start'

    @api.onchange('vehicle_id', 'driver_id', 'date')
    def _onchange_check_double_booking(self):
        """
        Method to warn on double booking of vehicle or driver on the same day.
        """
        if not self.date:
            return

        domain = [('date', '=', self.date)]
        if self._origin and self._origin.id:
            domain.append(('id', '!=', self._origin.id))

        warnings = []

        if self.vehicle_id:
            vehicle_routes = self.env['wm.route'].search(domain + [('vehicle_id', '=', self.vehicle_id.id)])
            if vehicle_routes:
                warnings.append(_("Vehicle '%s' is already booked on %s.") % (self.vehicle_id.name, self.date))

        if self.driver_id:
            driver_routes = self.env['wm.route'].search(domain + [('driver_id', '=', self.driver_id.id)])
            if driver_routes:
                warnings.append(_("Driver '%s' is already booked on %s.") % (self.driver_id.name, self.date))

        if warnings:
            return {
                'warning': {
                    'title': _("Double Booking Conflict"),
                    'message': "\n".join(warnings)
                }
            }

    @api.depends('date')
    def _compute_valid_vehicle_ids(self):
        """
        Filter available fleet vehicles to those with a valid waste-transport
        licence and sufficient payload capacity for the collections on this
        route.
        """
        for route in self:
            try:
                checklists = self.env['survey.user_input'].search([('checklist_type', '=', 'pre_trip'), ('state', '=', 'done')])
                route.valid_vehicle_ids = checklists.mapped('vehicle_id')
            except Exception as e:
                _logger.warning("Failed to compute valid vehicle IDs from pre-trip survey: %s", e)
                route.valid_vehicle_ids = self.env['fleet.vehicle'].search([])

    @api.depends('line_ids', 'line_ids.sequence', 'line_ids.collection_point_id',
                 'line_ids.collection_point_id.latitude', 'line_ids.collection_point_id.longitude',
                 'line_ids.collection_point_id.name', 'line_ids.collection_point_id.contact_address')
    def _compute_route_map_data(self):
        """
        Compile an ordered list of collection point coordinates and metadata
        into a JSON-serializable structure for rendering on the interactive
        route map view.
        """
        for route in self:
            valid_lines = []
            for line in route.line_ids:
                pt = line.collection_point_id
                if pt and pt.latitude and pt.longitude:
                    valid_lines.append((line, pt.latitude, pt.longitude))

            if valid_lines:
                ordered_lines = _solve_tsp_shortest_path(valid_lines)
            else:
                ordered_lines = [l for l in route.line_ids.sorted(key=lambda x: x.sequence)]

            route_point_ids = set()
            route_points = []
            idx = 1
            for line in ordered_lines:
                pt = line.collection_point_id
                if pt and pt.latitude and pt.longitude:
                    route_point_ids.add(pt.id)
                    route_points.append({
                        'index': idx,
                        'name': pt.name,
                        'address': pt.contact_address or '',
                        'lat': pt.latitude,
                        'lng': pt.longitude,
                        'id': pt.id,
                        'is_route_point': True,
                    })
                    idx += 1

            data = {
                'route_points': route_points,
                'other_points': [],
            }
            route.route_map_data = json.dumps(data)

    def action_optimize_route(self):
        """
        Optimizes the order of route lines to achieve the shortest travel path.
        """
        for route in self:
            if route.state in ('dispatched', 'running', 'completed') and not self.env.context.get('bypass_sequence_lock'):
                raise UserError(_("Cannot re-optimize or re-sequence route '%s' because its status is '%s'. Route sequence is locked for active driver dispatch.") % (route.name, route.state))

            valid_lines = []
            invalid_lines = []
            for line in route.line_ids:
                pt = line.collection_point_id
                if pt and pt.latitude and pt.longitude:
                    valid_lines.append((line, pt.latitude, pt.longitude))
                else:
                    invalid_lines.append(line)

            if valid_lines:
                ordered_lines = _solve_tsp_shortest_path(valid_lines)
                all_lines = ordered_lines + invalid_lines

                # Re-assign sequence numbers (10, 20, 30...)
                seq = 10
                for line in all_lines:
                    line.sequence = seq
                    seq += 10

                # Compute total estimated distance & duration
                total_distance_km = 0.0
                for k in range(len(valid_lines) - 1):
                    p1 = ordered_lines[k].collection_point_id
                    p2 = ordered_lines[k + 1].collection_point_id
                    total_distance_km += _haversine_distance(p1.latitude, p1.longitude, p2.latitude, p2.longitude)

                # Estimate duration: average speed 30 km/h + 15 min stop per point
                driving_hours = total_distance_km / 30.0 if total_distance_km > 0 else 0.0
                stop_hours = len(valid_lines) * 0.25
                route.estimated_duration = round(driving_hours + stop_hours, 2)

                route.message_post(body=f"Route optimized for shortest path. Total estimated distance: {total_distance_km:.2f} km.")

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Route Optimized',
                'message': 'Collection points re-ordered for the shortest path!',
                'sticky': False,
                'type': 'success',
                'next': {'type': 'ir.actions.act_window_close'}
            }
        }

    def action_add_collection_point(self, point_id, optimize=True):
        """
        Append a selected collection point to the route's ordered stop list,
        recalculating the estimated total distance and updating the map data
        field.
        """
        self.ensure_one()
        point = self.env['wm.collection.point'].browse(point_id)
        if not point.exists():
            return False
        existing_line = self.line_ids.filtered(lambda l: l.collection_point_id.id == point_id)
        if not existing_line:
            max_seq = max(self.line_ids.mapped('sequence') or [0])
            self.env['wm.route.line'].create({
                'route_id': self.id,
                'collection_point_id': point.id,
                'sequence': max_seq + 10,
            })

            # Check if an existing unassigned or active collection order exists for this point today
            target_date = self.date or fields.Date.today()
            start_dt = datetime.combine(target_date, time.min)
            end_dt = datetime.combine(target_date, time.max)

            existing_order = self.env['wm.collection.order'].search([
                ('collection_point_id', '=', point.id),
                ('state', 'in', ('draft', 'dispatched')),
                '|',
                    ('scheduled_start', '=', False),
                    '&', ('scheduled_start', '>=', start_dt), ('scheduled_start', '<=', end_dt),
            ], limit=1)

            if existing_order:
                order_update = {'route_id': self.id}
                if self.vehicle_id:
                    order_update['vehicle_id'] = self.vehicle_id.id
                if self.driver_id:
                    order_update['driver_id'] = self.driver_id.id
                existing_order.write(order_update)
            else:
                order_vals = {
                    'partner_id': point.partner_id.id if point.partner_id else False,
                    'collection_point_id': point.id,
                    'route_id': self.id,
                    'vehicle_id': self.vehicle_id.id if self.vehicle_id else False,
                    'driver_id': self.driver_id.id if self.driver_id else False,
                    'scheduled_start': datetime.combine(target_date, time(9, 0, 0)),
                    'state': 'draft',
                }

                if point.category_ids:
                    lines = []
                    for cat in point.category_ids:
                        materials = cat.material_ids or self.env['product.product'].search([('wm_waste_category_id', '=', cat.id)])
                        if materials:
                            for mat in materials:
                                lines.append((0, 0, {
                                    'category_id': cat.id,
                                    'product_id': mat.id,
                                    'price': cat.price or mat.list_price or 0.0,
                                    'weight': 0.0,
                                }))
                        else:
                            fallback_product = self.env['product.product'].search([('is_waste_material', '=', True)], limit=1)
                            if fallback_product:
                                lines.append((0, 0, {
                                    'category_id': cat.id,
                                    'product_id': fallback_product.id,
                                    'price': cat.price or fallback_product.list_price or 0.0,
                                    'weight': 0.0,
                                }))
                    if lines:
                        order_vals['order_line_ids'] = lines

                self.env['wm.collection.order'].create(order_vals)

            if optimize and self.state == 'to_start':
                self.action_optimize_route()
        return True

    def action_remove_collection_point(self, point_id):
        """
        Remove a collection point from the route's stop list, recalculating
        distance and verifying that the route has at least one remaining stop.
        """
        self.ensure_one()
        lines = self.line_ids.filtered(lambda l: l.collection_point_id.id == point_id)
        if lines:
            lines.unlink()

            draft_orders = self.env['wm.collection.order'].search([
                ('route_id', '=', self.id),
                ('collection_point_id', '=', point_id),
                ('state', '=', 'draft')
            ])
            if draft_orders:
                draft_orders.unlink()

            if self.state == 'to_start':
                self.action_optimize_route()
        return True

    def action_view_route_map(self):
        """
        Open the interactive collection route map view, displaying all ordered
        stop markers, the driver's current estimated position, and navigation
        waypoints.
        """
        self.ensure_one()
        if self.state == 'to_start':
            self.action_optimize_route()
        return {
            'type': 'ir.actions.client',
            'tag': 'wm_collection.route_map_client_action',
            'name': 'Route Map: %s' % self.name,
            'params': {
                'route_id': self.id,
            },
            'context': self.env.context,
        }

    @api.depends('line_ids.collection_point_id')
    def _compute_selected_point_ids(self):
        """
        Derive the list of already-selected collection point IDs from the
        route's stop lines, used to filter the add-stop domain to prevent
        duplicate entries.
        """
        for route in self:
            route.selected_point_ids = route.line_ids.mapped('collection_point_id')

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create to auto-generate the route sequence reference, apply
        default vehicle and driver assignments from zone configuration, and log
        the creation event.
        """
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('wm.route') or 'New'
        return super().create(vals_list)

    def write(self, vals):
        """ Prevent modifying essential route details once completed. """
        if not self.env.su and not self.env.context.get('programmatic_state_change'):
            restricted_fields = {'line_ids', 'zone_id', 'date', 'vehicle_id', 'driver_id'}
            if restricted_fields.intersection(vals.keys()):
                for route in self:
                    if route.state == 'completed':
                        raise UserError(_(
                            "Cannot modify route '%(name)s' because it is already completed.",
                            name=route.name,
                        ))
        return super().write(vals)

    def unlink(self):
        """ Prevent deleting running or completed routes. """
        for route in self:
            if route.state in ('running', 'completed'):
                raise UserError(_(
                    "Cannot delete route '%(name)s' because it is in '%(state)s' status.",
                    name=route.name,
                    state=dict(self._fields['state'].selection).get(route.state, route.state),
                ))
        return super().unlink()

    def action_change_driver_wizard(self):
        """
        Open the Change Driver wizard pre-populated with the current route
        driver, allowing supervisors to reassign routes mid-operation with a
        documented reason.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Change Driver'),
            'res_model': 'wm.change.driver.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_route_id': self.id,
            },
        }

    @api.depends('driver_change_history_ids')
    def _compute_driver_history_count(self):
        """
        Compute the total number of associated driver history records linked to
        this WmRoute to update smart buttons and summary badges.
        """
        for route in self:
            route.driver_history_count = len(route.driver_change_history_ids)

    def action_view_driver_history(self):
        """
        Display the full driver change history log for this route, showing each
        reassignment event with timestamps and supervisor authorisation
        details.
        """
        self.ensure_one()
        return {
            'name': _('Driver History'),
            'type': 'ir.actions.act_window',
            'res_model': 'wm.driver.change.history',
            'view_mode': 'list',
            'domain': [('route_id', '=', self.id)],
            'context': dict(self.env.context, create=False, edit=False),
        }

    @api.depends('collection_order_ids')
    def _compute_collection_order_count(self):
        """
        Compute the total number of associated collection order records linked
        to this WmRoute to update smart buttons and summary badges.
        """
        for route in self:
            route.collection_order_count = len(route.collection_order_ids)

    def action_view_collection_orders(self):
        """
        Open the list of all collection orders assigned to this route, allowing
        dispatchers to monitor completion status and outstanding pickups.
        """
        self.ensure_one()
        action = {
            'name': _('Collection Orders — %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'wm.collection.order',
            'view_mode': 'list,form',
            'domain': [('route_id', '=', self.id)],
            'context': {
                'default_route_id': self.id,
                'default_driver_id': self.driver_id.id if self.driver_id else False,
                'default_vehicle_id': self.vehicle_id.id if self.vehicle_id else False,
            },
        }
        if len(self.collection_order_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': self.collection_order_ids.id,
            })
        return action
