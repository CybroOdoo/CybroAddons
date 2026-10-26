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
import re

from odoo import _, api, fields, models

# Whole-word match so that e.g. "Normal" / "Not applicable" do not count as
# a failed 'no' answer.
_FAILED_ANSWER_RE = re.compile(r'\b(?:fail\w*|no|bad|defect\w*|damaged)\b', re.IGNORECASE)


class SurveyUserInput(models.Model):
    """Extends Survey User Input with vehicle maintenance checklist linkage."""
    _inherit = 'survey.user_input'

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')
    checklist_type = fields.Selection([
        ('pre_trip', 'Pre-Trip'),
        ('post_trip', 'Post-Trip')
    ], string='Checklist Type')

    @api.onchange('checklist_type')
    def _onchange_checklist_type(self):
        """
        Reload the default inspection item lines when the checklist type
        (pre-trip / post-trip) changes, populating the appropriate vehicle
        condition assessment fields.
        """
        if self.checklist_type:
            title_search = 'Pre-Trip' if self.checklist_type == 'pre_trip' else 'Post-Trip'
            survey = self.env['survey.survey'].search([('title', 'ilike', title_search)], limit=1)
            if survey:
                self.survey_id = survey.id

    @api.onchange('vehicle_id', 'checklist_type')
    def _onchange_check_pending_post_trip(self):
        """
        Warn the dispatcher when a vehicle has an open pre-trip checklist
        without a corresponding completed post-trip report, flagging potential
        regulatory non-compliance.
        """
        if self.vehicle_id and self.checklist_type == 'pre_trip':
            pending_post_trip = self.env['survey.user_input'].search([
                ('vehicle_id', '=', self.vehicle_id.id),
                ('checklist_type', '=', 'post_trip'),
                ('state', '!=', 'done')
            ], limit=1)

            if pending_post_trip:
                return {
                    'warning': {
                        'title': _("Pending Post-Trip Checklist"),
                        'message': _("Vehicle '%s' has an unfinished Post-Trip checklist! It is highly recommended to complete it before starting a new Pre-Trip inspection.") % self.vehicle_id.name
                    }
                }

    def action_start_survey(self):
        """
        Launch the pre-operation vehicle inspection survey wizard,
        pre-populating the vehicle and driver fields from the current checklist
        record.
        """
        self.ensure_one()
        if self.partner_id != self.env.user.partner_id:
            self.partner_id = self.env.user.partner_id
        return {
            'type': 'ir.actions.act_url',
            'name': "Start Checklist",
            'target': 'self',
            'url': '/survey/start/%s?answer_token=%s' % (self.survey_id.access_token, self.access_token)
        }

    def _mark_done(self):
        """
        Transition the vehicle maintenance checklist to 'done', recording the
        completion timestamp, operator signature, and any defects noted during
        inspection.
        """
        res = super()._mark_done()
        for record in self:
            if record.checklist_type == 'pre_trip' and record.vehicle_id:
                has_failed_critical = False
                failed_items = []
                if hasattr(record, 'scoring_success') and not record.scoring_success:
                    has_failed_critical = True

                for line in record.user_input_line_ids:
                    is_failed = False
                    if (line.answer_score == 0.0 and line.question_id.question_type in ('simple_choice', 'multiple_choice')) or (line.suggested_answer_id and _FAILED_ANSWER_RE.search(line.suggested_answer_id.value or '')) or (line.value_char_box and _FAILED_ANSWER_RE.search(line.value_char_box)):
                        is_failed = True

                    if is_failed:
                        has_failed_critical = True
                        q_title = line.question_id.title if hasattr(line.question_id, 'title') and line.question_id.title else (line.question_id.name if hasattr(line.question_id, 'name') else 'Safety Item')
                        failed_items.append(q_title)

                if has_failed_critical:
                    vehicle = record.vehicle_id

                    # 1. Update vehicle status to 'maintenance'
                    vehicle_vals = {}
                    if 'state' in vehicle._fields:
                        vehicle_vals['state'] = 'maintenance'

                    downgrade_state = self.env['fleet.vehicle.state'].sudo().search([('name', 'ilike', 'maintenance')], limit=1)
                    if not downgrade_state:
                        downgrade_state = self.env['fleet.vehicle.state'].sudo().search([('name', 'ilike', 'downgrade')], limit=1)
                    if downgrade_state and 'state_id' in vehicle._fields:
                        vehicle_vals['state_id'] = downgrade_state.id

                    if vehicle_vals:
                        vehicle.sudo().write(vehicle_vals)

                    # 2. Auto-create Service Request (fleet.vehicle.log.services)
                    if 'fleet.vehicle.log.services' in self.env:
                        service_type = self.env['fleet.service.type'].sudo().search([('name', 'ilike', 'inspection')], limit=1)
                        if not service_type:
                            service_type = self.env['fleet.service.type'].sudo().search([], limit=1)

                        desc_items = "\n- ".join(failed_items) if failed_items else "Safety checks failed during Pre-Trip inspection."
                        desc = f"AUTOMATED INSPECTION FAILURE TRIGGER:\nPre-Trip Inspection failed for {vehicle.name}.\n\nFailed Items:\n- {desc_items}"

                        service_vals = {
                            'vehicle_id': vehicle.id,
                            'description': desc,
                        }
                        if service_type:
                            service_vals['service_type_id'] = service_type.id
                        if 'date' in self.env['fleet.vehicle.log.services']._fields:
                            service_vals['date'] = fields.Date.context_today(self)
                        if 'state' in self.env['fleet.vehicle.log.services']._fields:
                            service_vals['state'] = 'running'

                        service_log = self.env['fleet.vehicle.log.services'].sudo().create(service_vals)

                        if hasattr(vehicle, 'message_post'):
                            failed_summary = ", ".join(failed_items) if failed_items else "Pre-Trip Failure"
                            vehicle.message_post(
                                body=f"<strong>AUTOMATED SERVICE TRIGGER:</strong> Pre-Trip Inspection failed ({failed_summary}). Service Log #{service_log.id} created."
                            )

                    # 3. Auto-reassign driver's pending route to a standby vehicle
                    if 'wm.route' in self.env:
                        pending_routes = self.env['wm.route'].sudo().search([
                            ('vehicle_id', '=', vehicle.id),
                            ('state', 'in', ('to_start', 'dispatched'))
                        ])
                        for route in pending_routes:
                            standby = record._find_standby_vehicle(vehicle, route)

                            if standby:
                                old_name = vehicle.name
                                # Programmatic reassignment: must not be blocked
                                # by the "already inspected" guard on route.write.
                                route.with_context(programmatic_state_change=True).write({
                                    'vehicle_id': standby.id,
                                    'is_inspected': False,
                                })
                                if route.collection_order_ids:
                                    route.collection_order_ids.with_context(
                                        programmatic_state_change=True).write({'vehicle_id': standby.id})
                                route.message_post(
                                    body=f"<strong>AUTOMATED ROUTE REASSIGNMENT:</strong> Vehicle '{old_name}' failed Pre-Trip Inspection. Route automatically reassigned to standby vehicle <strong>{standby.name}</strong>."
                                )
                            else:
                                route.message_post(
                                    body=f"<strong>WARNING:</strong> Vehicle '{vehicle.name}' failed Pre-Trip Inspection. No standby vehicle was available; manual vehicle reassignment is required."
                                )
                else:
                    vehicle = record.vehicle_id
                    vehicle_vals = {}
                    if 'state' in vehicle._fields and vehicle.state != 'available':
                        vehicle_vals['state'] = 'available'

                    if 'state_id' in vehicle._fields and vehicle.state_id and ('maintenance' in (vehicle.state_id.name or '').lower() or 'downgrade' in (vehicle.state_id.name or '').lower()):
                        available_state = self.env['fleet.vehicle.state'].sudo().search([
                            ('name', 'ilike', 'registered')
                        ], limit=1)
                        if not available_state:
                            available_state = self.env['fleet.vehicle.state'].sudo().search([
                                ('name', 'not ilike', 'maintenance'),
                                ('name', 'not ilike', 'downgrade')
                            ], limit=1)
                        if available_state:
                            vehicle_vals['state_id'] = available_state.id

                    if vehicle_vals:
                        vehicle.sudo().write(vehicle_vals)

                    if hasattr(vehicle, 'message_post'):
                        vehicle.message_post(
                            body=f"<strong>PRE-TRIP INSPECTION PASSED:</strong> Vehicle '{vehicle.name}' passed all inspection criteria and is ready for service."
                        )
        return res

    def _find_standby_vehicle(self, failed_vehicle, route):
        """Return a vehicle that can take over *route*, or an empty recordset.

        Excludes vehicles already on another open route that day, vehicles
        with an open service log and vehicles in a maintenance/downgrade
        fleet state.
        """
        Vehicle = self.env['fleet.vehicle'].sudo()
        domain = [
            ('id', '!=', failed_vehicle.id),
            ('company_id', '=', failed_vehicle.company_id.id if failed_vehicle.company_id else False),
        ]
        if 'state' in Vehicle._fields:
            domain.append(('state', '=', 'available'))
        busy = self.env['wm.route'].sudo().search([
            ('id', '!=', route.id),
            ('date', '=', route.date),
            ('state', '!=', 'completed'),
            ('vehicle_id', '!=', False),
        ]).vehicle_id
        if 'fleet.vehicle.log.services' in self.env:
            Services = self.env['fleet.vehicle.log.services'].sudo()
            if 'state' in Services._fields:
                busy |= Services.search([('state', 'in', ('new', 'running'))]).vehicle_id
        if busy:
            domain.append(('id', 'not in', busy.ids))
        for candidate in Vehicle.search(domain):
            state_name = (candidate.state_id.name or '').lower() if 'state_id' in Vehicle._fields else ''
            if 'maintenance' in state_name or 'downgrade' in state_name:
                continue
            return candidate
        return Vehicle


class WMChecklistItem(models.Model):
    """A single inspection criterion (e.g. 'Brake check') within a vehicle maintenance checklist type."""
    _name = 'wm.checklist.item'
    _description = 'Checklist Item'

    name = fields.Char(string='Name', help='Provides information about name', required=True)
    checklist_type = fields.Selection([
        ('pre_trip', 'Pre-Trip'),
        ('post_trip', 'Post-Trip')
    ], string='Checklist Type', required=True, default='pre_trip')
    active = fields.Boolean(default=True, string='Active', help='Provides information about active')


class WMChecklistLine(models.Model):
    """A completed response line for one checklist item on a vehicle maintenance inspection record."""
    _name = 'wm.checklist.line'
    _description = 'Checklist Line'

    checklist_id = fields.Many2one('wm.vehicle.maintenance.checklist', string='Checklist', help='Provides information about checklist', ondelete='cascade')
    item_id = fields.Many2one('wm.checklist.item', string='Item', help='Provides information about item', required=True)
    is_passed = fields.Boolean(string='Checked', help='Provides information about checked', default=False)
    notes = fields.Char(string='Notes', help='Provides information about notes')


class WMVehicleMaintenanceChecklist(models.Model):
    """Vehicle pre-trip or post-trip maintenance inspection record linked to a route and driver."""
    _name = 'wm.vehicle.maintenance.checklist'
    _description = 'Vehicle Maintenance Checklist'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Reference', help='Provides information about reference', required=True, copy=False, default='New', tracking=True)
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', help='Provides information about vehicle', required=True, tracking=True)
    checklist_type = fields.Selection([
        ('pre_trip', 'Pre-Trip'),
        ('post_trip', 'Post-Trip')
    ], string='Checklist Type', required=True, tracking=True)
    line_ids = fields.One2many('wm.checklist.line', 'checklist_id', string='Checklist Lines', help='Provides information about checklist lines')
    inspector_id = fields.Many2one('res.users', string='Inspector', help='Provides information about inspector', default=lambda self: self.env.user, required=True, tracking=True)
    date = fields.Date(string='Date', help='Provides information about date', default=fields.Date.context_today, tracking=True, copy=False)
    state = fields.Selection([
        ('tocheck', 'To Check'),
        ('checked', 'Checked')
    ], string='Status', default='tocheck', tracking=True, copy=False)

    def _trigger_route_inspection_recompute(self, vehicles, exclude_routes=None):
        """Recompute the pre-trip status of open routes using *vehicles*.

        ``wm.route.is_inspected`` falls back to maintenance checklists done
        since the vehicle's previous route, which it cannot express as an
        ``@api.depends`` path.
        """
        if not vehicles or 'wm.route' not in self.env:
            return
        Route = self.env['wm.route'].sudo()
        domain = [
            ('vehicle_id', 'in', vehicles.ids),
            ('state', 'in', ('to_start', 'dispatched')),
        ]
        if exclude_routes:
            domain.append(('id', 'not in', exclude_routes.ids))
        routes = Route.search(domain)
        if routes:
            self.env.add_to_compute(Route._fields['is_inspected'], routes)
            self.env.add_to_compute(Route._fields['is_ready_to_dispatch'], routes)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        self._trigger_route_inspection_recompute(
            records.filtered(lambda c: c.checklist_type == 'pre_trip' and c.state == 'checked').vehicle_id)
        return records

    def write(self, vals):
        old_vehicles = self.filtered(lambda c: c.checklist_type == 'pre_trip').vehicle_id
        res = super().write(vals)
        if {'state', 'date', 'vehicle_id', 'checklist_type'} & set(vals):
            self._trigger_route_inspection_recompute(
                old_vehicles | self.filtered(lambda c: c.checklist_type == 'pre_trip').vehicle_id)
        return res

    def unlink(self):
        vehicles = self.filtered(lambda c: c.checklist_type == 'pre_trip').vehicle_id
        res = super().unlink()
        self._trigger_route_inspection_recompute(vehicles)
        return res
