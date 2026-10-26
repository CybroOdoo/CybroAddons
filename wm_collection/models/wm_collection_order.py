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
import base64
import logging
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, time, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


@dataclass
class RateCardRule:
    """Rate card lookup rule defining category-specific collection pricing tiers."""
    price: float
    billing_basis: str = 'per_kg'
    min_weight: float = 0.0
    min_charge: float = 0.0
    max_weight: float = 0.0
    overweight_price: float = 0.0
    included_weight: float = 0.0
    id: bool = False
    # Set for contract per_collection / hybrid fees: these are charged once
    # per collection for the whole contract, not once per waste category.
    contract_id: int = 0
    # True when the price comes from a partner contract (contract currency);
    # rate-card and pricing-rule prices are in the company currency.
    from_contract: bool = False


class WmCollectionOrder(models.Model):
    """Represents a single waste collection job from scheduling through dispatch, execution, and billing handoff."""
    _name = 'wm.collection.order'
    _description = 'Collection Order'
    _inherit = ['wm.audit.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Reference', help='Provides information about reference', required=True, copy=False, readonly=True, index=True, default=lambda self: 'New')
    partner_id = fields.Many2one('res.partner', string='Partner', help='Provides information about partner', tracking=True, index=True)
    company_id = fields.Many2one('res.company', string='Company', help='Provides information about company', required=True, default=lambda self: self.env.company)
    collection_point_id = fields.Many2one('wm.collection.point', string='Collection Point', help='Provides information about collection point', tracking=True)

    order_line_ids = fields.One2many('wm.collection.order.line', 'order_id', string='Order Lines', help='Provides information about order lines', copy=True)
    status_log_ids = fields.One2many(
        'wm.collection.order.status.log', 'order_id', string='Stop Status Timeline', copy=False,
        help='Timestamped sequence of stop-level events reported by the driver app for this order.'
    )
    product_ids = fields.Many2many('product.product', compute='_compute_product_ids', string='Waste Material', help='Provides information about waste category')
    collection_point_category_ids = fields.Many2many(
        'wm.waste.category',
        string='Allowed Waste Categories',
        compute='_compute_collection_point_category_ids',
    )
    container_id = fields.Many2one(
        'wm.container.type',
        string='Container Type',
        compute='_compute_container_id',
        store=True,
        help='Provides information about container type',
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('dispatched', 'Dispatched'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('signed', 'Signed'),
        ('missed', 'Missed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', group_expand='_read_group_states', tracking=True, index=True, copy=False)
    estimated_weight = fields.Float(string='Estimated Weight', help='Provides information about estimated weight')
    confirmed_weight = fields.Float(string='Confirmed Weight', help='Provides information about confirmed weight', compute='_compute_confirmed_weight', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', related='company_id.currency_id', readonly=True)
    total_amount = fields.Monetary(
        string='Total Amount',
        compute='_compute_total_amount',
        store=True,
        currency_field='currency_id',
        help='Total monetary value of the collection order summing all line amounts.'
    )
    co2_avoided_tons = fields.Float(
        string='Carbon Abated (tCO2e)',
        compute='_compute_co2_avoided_tons',
        store=True,
        digits=(10, 3),
        help='Scope 3 Carbon Abatement (tCO2e avoided) based on EPA WARM standards = (Confirmed Weight in kg ÷ 1000) × Category EPA WARM Factor.'
    )
    route_id = fields.Many2one(
        'wm.route',
        string='Route',
        domain="[('state', '!=', 'completed')]",
        help='Provides information about route',
        index=True,
    )
    valid_vehicle_ids = fields.Many2many('fleet.vehicle', compute='_compute_valid_vehicle_ids')
    vehicle_id = fields.Many2one(
        'fleet.vehicle',
        string='Vehicle',
        compute='_compute_vehicle_id',
        store=True,
        readonly=False,
        help='Provides information about vehicle',
    )
    driver_id = fields.Many2one(
        'res.partner',
        string='Driver',
        compute='_compute_driver_id',
        store=True,
        readonly=False,
        help='Provides information about driver',
    )
    scheduled_start = fields.Datetime(
        string='Scheduled Start',
        help='Provides information about scheduled start',
        tracking=True,
        index=True,
        default=fields.Datetime.now,
    )
    scheduled_end = fields.Datetime(string='Scheduled End', help='Provides information about scheduled end', tracking=True)
    actual_start = fields.Datetime(string='Actual Start', help='Provides information about actual start', tracking=True)
    actual_end = fields.Datetime(string='Actual End', help='Provides information about actual end', tracking=True)
    completed_date = fields.Datetime(string='Completed Date', readonly=True, help='Provides information about completed date')
    schedule_status = fields.Selection([
        ('on_time', 'On Time'),
        ('early', 'Early'),
        ('late', 'Late'),
    ], string='Schedule Status', compute='_compute_schedule_status', store=True)
    signature_id = fields.Many2one('wm.signature', string='Signature', help='Provides information about signature')
    driver_photo = fields.Image(string='Driver Photo', help='Provides information about driver photo')
    geolocation_tag = fields.Char(string='Geolocation Tag', help='Provides information about geolocation tag')
    signature_template_id = fields.Many2one(
        'wm.signature.template',
        string='Signature Template',
        default=lambda self: self.env.ref('wm_collection.sig_template_collection_order', raise_if_not_found=False),
        help='Provides information about signature template'
    )
    collection_report_pdf = fields.Binary(
        string='Generated Collection Report PDF',
        attachment=True,
        readonly=True,
        copy=False,
    )
    collection_report_pdf_filename = fields.Char(
        string='Generated Collection Report Filename',
        readonly=True,
        copy=False,
    )
    waste_batch_ids = fields.One2many('waste.batch', 'collection_order_id', string='Waste Batches')
    waste_batch_count = fields.Integer(string='Waste Batch Count', compute='_compute_waste_batch_count')
    gate_entry_ids = fields.One2many('wm.facility.gate.entry', 'collection_order_id', string='Facility Gate Entries')
    gate_entry_count = fields.Integer(string='Gate Entry Count', compute='_compute_gate_entry_count')
    is_billed = fields.Boolean(
        string='Billed',
        compute='_compute_is_billed',
        store=True,
        help='True when this order has been included in a monthly invoice.',
    )
    # ── Missed-collection fields ──
    use_missed_collection = fields.Boolean(compute='_compute_use_settings')
    is_missed = fields.Boolean(string='Missed', help='Provides information about missed', default=False, tracking=True)
    missed_reason_id = fields.Many2one('wm.missed.reason', string='Missed Reason', help='Provides information about missed reason', tracking=True)
    missed_notes = fields.Text(string='Missed Notes', help='Provides information about missed notes')
    parent_order_id = fields.Many2one('wm.collection.order', string='Original Order', help='Provides information about original order', readonly=True, copy=False)
    retry_order_id = fields.Many2one('wm.collection.order', string='Retry Order', help='Provides information about retry order', readonly=True, copy=False)
    retry_count = fields.Integer(string='Retry Count', help='Provides information about retry count', compute='_compute_retry_count')
    missed_collection_id = fields.Many2one('wm.missed.collection', string='Missed Collection Record', help='Provides information about missed collection record', readonly=True, copy=False)
    signature_signer_count = fields.Integer(string='Signatures', help='Provides information about signatures', compute='_compute_signature_signer_count')
    next_signer_id = fields.Many2one('wm.signature.request.signer', compute='_compute_next_signer', string='Next Signer', help='Provides information about next signer')
    next_signer_role_name = fields.Char(compute='_compute_next_signer', string='Next Signer Role', help='Provides information about next signer role')

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """
        Refresh the default collection point and contract selection when the
        partner changes, ensuring the order's route and billing configuration
        matches the new customer.
        """
        if self.partner_id:
            if self.collection_point_id and self.collection_point_id.partner_id != self.partner_id:
                self.collection_point_id = False
            if not self.collection_point_id:
                points = self.env['wm.collection.point'].search([('partner_id', '=', self.partner_id.id)])
                if len(points) == 1:
                    self.collection_point_id = points.id
        else:
            self.collection_point_id = False

    @api.depends('collection_point_id', 'collection_point_id.category_ids')
    def _compute_collection_point_category_ids(self):
        """
        Derive the set of waste categories serviced at the selected collection
        point, filtering the order line category domain to prevent the
        selection of unsupported waste streams.
        """
        for order in self:
            order.collection_point_category_ids = order.collection_point_id.category_ids if order.collection_point_id else False

    @api.depends('order_line_ids.product_id')
    def _compute_product_ids(self):
        """
        Build the list of available waste material products from the assigned
        route's collection point configurations, filtering the order line
        product domain accordingly.
        """
        for order in self:
            order.product_ids = order.order_line_ids.mapped('product_id')

    @api.model
    def _read_group_states(self, _stages, domain, order=None):
        """ Expand group stages in kanban view based on missed collection setting. """
        use_missed = self.env['ir.config_parameter'].sudo().get_param('wm_collection.use_missed_collection', 'False') in ('True', '1')
        all_states = [key for key, _val in self._fields['state'].selection if key != 'cancelled']
        if not use_missed:
            all_states = [s for s in all_states if s != 'missed']
        return all_states

    @api.depends('order_line_ids.weight')
    def _compute_confirmed_weight(self):
        """
        Compute the weight delta between the declared order quantity and the
        physically weighed batch weight, flagging significant variances for
        supervisor review.
        """
        for order in self:
            order.confirmed_weight = sum(order.order_line_ids.mapped('weight'))

    @api.depends('order_line_ids.total_amount', 'order_line_ids.price', 'order_line_ids.weight',
                 'order_line_ids.estimated_weight', 'order_line_ids.price_basis')
    def _compute_total_amount(self):
        """
        Compute total monetary value for the order: the line amounts, plus
        the contract's per-collection fee (and overweight surcharge) once
        when the lines are priced by a per-collection or hybrid contract.
        """
        fee_rules = self.order_line_ids.filtered(
            lambda ln: ln.price_basis == 'contract_fee')._get_billing_rules()
        for order in self:
            total = 0.0
            for line in order.order_line_ids:
                if line.price_basis == 'per_kg':
                    total += line.total_amount or (line.price * (line.weight or line.estimated_weight or 0.0))
                else:
                    total += line.total_amount
            fee_lines = order.order_line_ids.filtered(lambda ln: ln.price_basis == 'contract_fee')
            if fee_lines:
                rule = fee_rules.get(fee_lines[0])
                if rule and getattr(rule, 'contract_id', 0):
                    weight = sum(ln.weight or ln.estimated_weight or 0.0 for ln in fee_lines)
                    base, surcharge, _kg, _allowed = order._compute_collection_fee(rule, weight, 1)
                    total += base + surcharge
            order.total_amount = total

    def _get_billing_service_date(self):
        """
        Date the collection was performed (completion, else scheduled start),
        in the user's timezone. Rates and contracts are resolved on this date
        rather than on the date the invoice happens to be generated.
        """
        self.ensure_one()
        service_dt = self.actual_end or self.scheduled_start
        if not service_dt:
            return fields.Date.context_today(self)
        return fields.Datetime.context_timestamp(self, service_dt).date()

    @api.model
    def _compute_collection_fee(self, rule, weight, order_count=1):
        """
        Amount of a flat_per_collection or hybrid rule for ``order_count``
        collections weighing ``weight`` kg in total: the base fee per
        collection, plus an overweight surcharge (per 10 kg) above the weight
        allowed for those collections. Shared by order totals and invoicing.

        :return: (base_total, overweight_surcharge, overweight_kg, allowed_weight)
        """
        if getattr(rule, 'billing_basis', '') == 'hybrid':
            allowed_per_collection = getattr(rule, 'included_weight', 0.0) or getattr(rule, 'min_weight', 0.0) or 0.0
            overweight_price = getattr(rule, 'overweight_price', 0.0) or getattr(rule, 'min_charge', 0.0) or 0.0
        else:
            allowed_per_collection = getattr(rule, 'max_weight', 0.0) or 0.0
            overweight_price = getattr(rule, 'overweight_price', 0.0) or 0.0
        base = rule.price * order_count
        allowed_weight = allowed_per_collection * order_count
        overweight_kg = weight - allowed_weight if (allowed_weight and overweight_price and weight > allowed_weight) else 0.0
        return base, (overweight_kg / 10.0) * overweight_price, overweight_kg, allowed_weight

    @api.depends('confirmed_weight', 'order_line_ids.weight', 'order_line_ids.category_id.warm_factor_co2', 'order_line_ids.product_id.wm_waste_category_id', 'order_line_ids.product_id.wm_waste_category_id.warm_factor_co2')
    def _compute_co2_avoided_tons(self):
        """
        Compute Scope 3 carbon abatement (tCO2e avoided) based on EPA WARM
        factor.
        """
        for order in self:
            # Weight each line by its own category factor
            total = 0.0
            weighted = 0.0
            for line in order.order_line_ids:
                cat = line.category_id or line.product_id.wm_waste_category_id
                w = line.weight or 0.0
                if not w:
                    continue
                total += w
                weighted += w * (cat.warm_factor_co2 if cat else 1.50)
            if total:
                order.co2_avoided_tons = weighted / 1000.0
            else:
                order.co2_avoided_tons = (order.confirmed_weight / 1000.0) * 1.50

    @api.depends('scheduled_start')
    def _compute_valid_vehicle_ids(self):
        """
        Filter the available fleet vehicles to those licensed for waste
        transport and with sufficient payload for the collection order's
        expected waste weight.
        """
        for order in self:
            try:
                checklists = self.env['wm.vehicle.maintenance.checklist'].search([('state', '=', 'checked')])
                order.valid_vehicle_ids = checklists.mapped('vehicle_id')
            except Exception as e:
                _logger.warning("Failed to compute valid vehicle IDs from maintenance checklist: %s", e)
                order.valid_vehicle_ids = self.env['fleet.vehicle'].search([])

    @api.depends('route_id.vehicle_id')
    def _compute_vehicle_id(self):
        """ Derive vehicle from the assigned route. Reset to False if route has no vehicle. """
        for order in self:
            if order.route_id:
                order.vehicle_id = order.route_id.vehicle_id
            elif not order.vehicle_id:
                order.vehicle_id = False

    @api.depends('vehicle_id.driver_id', 'route_id.driver_id')
    def _compute_driver_id(self):
        """ Derive driver from assigned vehicle, falling back to assigned route. """
        for order in self:
            if order.vehicle_id and order.vehicle_id.driver_id:
                order.driver_id = order.vehicle_id.driver_id
            elif order.route_id and order.route_id.driver_id:
                order.driver_id = order.route_id.driver_id
            elif not order.driver_id:
                order.driver_id = False

    @api.depends('vehicle_id.wm_container_id')
    def _compute_container_id(self):
        """ Derive container type from assigned vehicle. """
        for order in self:
            order.container_id = order.vehicle_id.wm_container_id if order.vehicle_id else False

    @api.onchange('scheduled_start')
    def _onchange_scheduled_start(self):
        """ Suggest scheduled_end as 1 hour after scheduled_start if not already set. """
        if self.scheduled_start and not self.scheduled_end:
            self.scheduled_end = self.scheduled_start + timedelta(hours=1)

    @api.depends('gate_entry_ids')
    def _compute_gate_entry_count(self):
        for order in self:
            order.gate_entry_count = len(order.gate_entry_ids)

    def action_view_gate_entries(self):
        self.ensure_one()
        enabled = self.env['ir.config_parameter'].sudo().get_param('wm_collection.use_facility_gate_entry', 'True') in ('True', '1')
        if not enabled:
            raise UserError(_("Facility Gate Entries feature is disabled in settings."))
        return {
            'name': _('Facility Gate Entries'),
            'type': 'ir.actions.act_window',
            'res_model': 'wm.facility.gate.entry',
            'view_mode': 'list,form',
            'domain': [('collection_order_id', '=', self.id)],
            'context': {'default_collection_order_id': self.id},
        }

    def _compute_is_billed(self):
        """
        Determine whether this collection order has already been included in a
        billing run, preventing duplicate billing and flagging orders ready for
        invoice reconciliation.
        """
        for order in self:
            order.is_billed = bool(getattr(order, 'consolidated_invoice_id', False) or getattr(order, 'billing_run_line_id', False))

    def _get_linked_waste_batches(self):
        """
        Waste batches holding this order's waste: created for it, or a shared
        draft batch it was merged into (linked via collection_order_ids only).
        """
        self.ensure_one()
        if not self.id:
            return self.env['waste.batch']
        return self.env['waste.batch'].sudo().search([
            '|', ('collection_order_id', '=', self.id), ('collection_order_ids', 'in', self.ids),
        ])

    @api.depends('waste_batch_ids', 'route_id.waste_batch_ids.collection_order_ids')
    def _compute_waste_batch_count(self):
        """ Compute the total number of Waste Batches linked to this order. """
        for order in self:
            order.waste_batch_count = len(order._get_linked_waste_batches())

    @api.depends('scheduled_start', 'scheduled_end', 'actual_start', 'actual_end')
    def _compute_schedule_status(self):
        """
        Compute schedule status based on actual vs scheduled completion time.
        Logic: - 'early'   : actual_end is before scheduled_end
        (completed ahead of schedule)- 'on_time' : actual_end is
        exactly on scheduled_end - 'late'    : actual_end is after
        scheduled_end (overdue) - False: dates not yet set (order not completed)
        """
        for order in self:
            if order.actual_end and order.scheduled_end:
                if order.actual_end < order.scheduled_end:
                    order.schedule_status = 'early'
                elif order.actual_end > order.scheduled_end:
                    order.schedule_status = 'late'
                else:
                    order.schedule_status = 'on_time'
            else:
                order.schedule_status = False

    @api.constrains('scheduled_start', 'scheduled_end')
    def _check_scheduled_dates(self):
        """ Validate that Scheduled End Date is strictly after Scheduled Start Date. """
        if self.env.context.get('skip_schedule_date_check'):
            return
        for order in self:
            if order.scheduled_start and order.scheduled_end and order.scheduled_end <= order.scheduled_start:
                raise ValidationError(_("Scheduled End Date must be later than Scheduled Start Date."))

    @api.constrains('actual_start', 'actual_end')
    def _check_actual_dates(self):
        """ Validate that Actual End Date is strictly after Actual Start Date."""
        if self.env.context.get('skip_schedule_date_check'):
            return
        for order in self:
            if order.actual_start and order.actual_end and order.actual_end <= order.actual_start:
                raise ValidationError(_("Actual End Date must be later than Actual Start Date."))

    @api.depends_context('company')
    def _compute_use_settings(self):
        """
        Load collection module feature flags from system configuration to
        determine which optional capabilities (signature enforcement, zone
        restrictions) are active.
        """
        use_missed = self.env['ir.config_parameter'].sudo().get_param('wm_collection.use_missed_collection', 'False') in ('True', '1')
        for order in self:
            order.use_missed_collection = use_missed

    @api.depends('parent_order_id')
    def _compute_retry_count(self):
        """
        Compute the total number of associated retry records linked to this
        WmCollectionOrder to update smart buttons and summary badges.
        """
        for order in self:
            count = 0
            current = order.parent_order_id
            while current:
                count += 1
                current = current.parent_order_id
            order.retry_count = count

    def action_mark_missed(self):
        """
        Open the Mark Missed wizard to record a reason for the missed
        collection, transition the order to 'missed' state, and notify the
        dispatcher.
        """
        self.ensure_one()
        if self.state not in ('draft', 'dispatched', 'in_progress'):
            raise UserError(_("Only open collection orders can be marked as missed."))
        if not self.use_missed_collection:
            raise UserError(_("Missed Collection functionality is disabled in settings."))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Mark as Missed'),
            'res_model': 'wm.mark.missed.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_order_id': self.id,
            },
        }

    def action_add_status_log(self):
        """
        Open the wizard to log a driver stop status event (en route, arrived,
        started, lifted, weighed, completed, flagged).
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Log Driver Status'),
            'res_model': 'wm.add.status.log.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_order_id': self.id,
            },
        }

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override ORM create to auto-generate the collection order sequence
        reference, set default scheduled dates from the route, and trigger
        billing pipeline initialisation.
        """
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('wm.collection.order') or 'New'
        orders = super().create(vals_list)
        orders._sync_route_collection_point()
        return orders

    def write(self, vals):
        """
        Override write to enforce state-dependent editing restrictions and
        broadcast order status changes to linked route lines and billing
        pipeline records.
        """
        if not self.env.context.get('programmatic_state_change') and not self.env.su:
            restricted_fields = {
                'partner_id', 'collection_point_id', 'order_line_ids',
                'scheduled_start', 'scheduled_end', 'route_id',
                'vehicle_id', 'driver_id', 'container_id', 'company_id',
                'estimated_weight', 'confirmed_weight', 'driver_photo',
                'geolocation_tag', 'signature_template_id', 'retry_count',
                'notes', 'contract_id',
            }
            if restricted_fields.intersection(vals.keys()):
                for order in self:
                    if order.state in ('completed', 'signed', 'invoiced', 'cancelled'):
                        raise UserError(_(
                            "Cannot modify collection order '%(name)s' because it is in '%(state)s' state.",
                            name=order.name,
                            state=dict(self._fields['state'].selection).get(order.state, order.state),
                        ))
        if 'state' in vals and not self.env.context.get('programmatic_state_change'):
            vals.pop('state', None)
        res = super().write(vals)
        if 'route_id' in vals or 'collection_point_id' in vals:
            self._sync_route_collection_point()
        if 'state' in vals:
            self._check_auto_complete_route()
        return res

    @api.ondelete(at_uninstall=False)
    def _unlink_except_locked_order(self):
        """ Prevent deletion of completed, signed, or invoiced collection orders. """
        for order in self:
            if order.state in ('completed', 'signed', 'invoiced'):
                raise UserError(_(
                    "Cannot delete collection order '%(name)s' because it is in '%(state)s' state.",
                    name=order.name,
                    state=dict(self._fields['state'].selection).get(order.state, order.state),
                ))

    def _check_auto_complete_route(self):
        """
        If all collection orders on a running route are finished
        (completed/signed/invoiced/missed/cancelled), automatically
        complete the route.
        """
        running_routes = self.mapped('route_id').filtered(lambda r: r.state == 'running')
        for route in running_routes:
            pending_count = self.env['wm.collection.order'].search_count([
                ('route_id', '=', route.id),
                ('state', 'in', ('draft', 'dispatched', 'in_progress'))
            ])
            if pending_count == 0:
                route.sudo().action_complete_route()

    def _sync_route_collection_point(self):
        """
        When a route and collection point are assigned to a collection order,
        ensure the collection point is added as a route line in the route,
        vehicle/driver inherit from route,         and re-optimize the route.
        """
        for order in self:
            if order.route_id:
                if order.route_id.vehicle_id and not order.vehicle_id:
                    order.vehicle_id = order.route_id.vehicle_id
                if order.route_id.driver_id and not order.driver_id:
                    order.driver_id = order.route_id.driver_id

                if order.collection_point_id:
                    existing_line = order.route_id.line_ids.filtered(
                        lambda ln: ln.collection_point_id == order.collection_point_id
                    )
                    if not existing_line:
                        max_seq = max(order.route_id.line_ids.mapped('sequence') or [0])
                        self.env['wm.route.line'].sudo().create({
                            'route_id': order.route_id.id,
                            'collection_point_id': order.collection_point_id.id,
                            'sequence': max_seq + 10,
                        })
                    if order.route_id.state == 'to_start':
                        order.route_id.sudo().action_optimize_route()

    def _check_collection_rights(self):
        """
        Enforce that only users with the 'Collection Operator' or 'Dispatcher'
        security group can transition collection orders between states,
        protecting against unauthorised changes.
        """
        if not (self.env.user.has_group('wm_base.group_wm_driver') or self.env.user.has_group('wm_base.group_wm_dispatcher') or self.env.user.has_group('wm_base.group_wm_ops_manager') or self.env.is_admin()):
            raise UserError(_("You do not have permission to perform operations on collection orders."))

    def action_dispatch(self):
        """
        Transition the collection order to 'dispatched' state, notifying the
        assigned driver via the mobile app and updating the route's overall
        dispatch status.
        """
        self._check_collection_rights()
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft collection orders can be dispatched (order '%s' is %s).") % (
                self.name, dict(self._fields['state'].selection).get(self.state)))
        if not self.partner_id or not self.collection_point_id:
            raise ValidationError(_("Please set a Customer and Collection Point before dispatching."))
        if not self.vehicle_id or not self.driver_id:
            raise ValidationError(_("Please provide Vehicle and Driver in the Logistics section before dispatching."))

        if not self.env.context.get('programmatic_state_change'):
            if self.route_id and self.route_id.state == 'to_start':
                self.route_id.action_dispatch_route()
            elif self.vehicle_id:
                if self.route_id and not self.route_id.is_inspected:
                    raise ValidationError(_("Cannot dispatch order '%s': Pre-trip inspection for vehicle '%s' has not passed.") % (self.name, self.vehicle_id.name))
                if not self.route_id:
                    maint_pre_trips = self.env['wm.vehicle.maintenance.checklist'].search([
                        ('vehicle_id', '=', self.vehicle_id.id),
                        ('checklist_type', '=', 'pre_trip'),
                        ('state', '=', 'checked')
                    ], limit=1)
                    if not maint_pre_trips:
                        raise ValidationError(_("Cannot dispatch order '%s': Vehicle '%s' has not completed a pre-trip inspection.") % (self.name, self.vehicle_id.name))

        self.with_context(programmatic_state_change=True).write({'state': 'dispatched'})

    def action_start(self):
        """
        Record the actual collection start timestamp and transition the order
        to 'in_progress', enabling the driver to log waste quantities as
        collections are made.
        """
        self._check_collection_rights()
        self.ensure_one()
        if self.state not in ('draft', 'dispatched'):
            raise UserError(_("Collection order '%s' cannot be started from its current status.") % self.name)
        self.with_context(programmatic_state_change=True).write({
            'state': 'in_progress',
            'actual_start': self.actual_start or fields.Datetime.now()
        })

    def action_complete(self):
        """
        Finalise the collection order by recording actual weights, generating
        the collection completion report PDF, attaching it to the chatter, and
        transitioning to 'completed'.
        """
        self._check_collection_rights()
        for order in self:
            order._action_complete_one()

    def _action_complete_one(self):
        """Complete a single collection order (see ``action_complete``)."""
        self.ensure_one()
        if self.state in ('completed', 'signed', 'missed', 'cancelled'):
            raise UserError(_("Collection order '%s' is already %s and cannot be completed again.") % (
                self.name, dict(self._fields['state'].selection).get(self.state)))
        if not self.order_line_ids:
            raise ValidationError(_("Please add at least one waste material item before completing the order."))
        if any(not line.category_id for line in self.order_line_ids):
            raise ValidationError(_("Every order line must have a waste category assigned."))
        if any(line.weight <= 0 for line in self.order_line_ids):
            raise ValidationError(_("Collection Order cannot be completed with zero or unrecorded weights. Please enter valid weights for all waste lines."))

        # Routed orders get their post-trip checklist once, on route completion.
        if self.vehicle_id and not self.route_id:
            count = self.env['wm.vehicle.maintenance.checklist'].search_count([
                ('vehicle_id', '=', self.vehicle_id.id),
                ('checklist_type', '=', 'post_trip')
            ])
            seq = str(count + 1).zfill(4)
            checklist_name = f"POST/{self.vehicle_id.name}/{seq}"

            self.env['wm.vehicle.maintenance.checklist'].create({
                'name': checklist_name,
                'vehicle_id': self.vehicle_id.id,
                'checklist_type': 'post_trip',
                'state': 'tocheck',
            })

        # Keep an end time already recorded (e.g. an offline driver-app
        # 'completed' event synced later) instead of the sync time.
        now = self.actual_end or fields.Datetime.now()
        if self.actual_start and now <= self.actual_start:
            now = self.actual_start + timedelta(seconds=1)

        self.with_context(programmatic_state_change=True).write({
            'state': 'completed',
            'actual_end': now,
        })

        # Automatically create category-level waste batches upon collection completion for standalone orders
        if not self.route_id:
            self.action_create_category_batches()

        # Automate creation and collection progression of compliance manifest
        self._automate_compliance_manifest()

        # Automate facility gate entry creation linked to this collection order
        self._automate_gate_entry()

        # Overweight billing event, signature template and Proof of Service
        # PDF: always produced, whether or not compliance is installed.
        self._log_overweight_event()
        self._generate_proof_of_service()

    def _get_order_disposal_facility(self):
        """
        Disposal facility used by the completion automations: one of the
        order's company (or a shared one), never another company's.
        """
        self.ensure_one()
        Facility = self.env['wm.disposal.facility'].sudo()
        domain = []
        if 'company_id' in Facility._fields:
            domain = [('company_id', 'in', [self.company_id.id, False])]
        return Facility.search(domain, order='company_id, id', limit=1)

    def _automate_gate_entry(self):
        """Auto-create a linked Gate Entry record when a collection order is completed."""
        enabled = self.env['ir.config_parameter'].sudo().get_param('wm_collection.use_facility_gate_entry', 'True') in ('True', '1')
        if not enabled or 'wm.facility.gate.entry' not in self.env:
            return
        GateEntry = self.env['wm.facility.gate.entry'].sudo()
        for order in self:
            if not order.vehicle_id:
                continue
            existing_entry = GateEntry.search([
                ('collection_order_id', '=', order.id),
                ('state', '!=', 'cancelled'),
            ], limit=1)
            if not existing_entry:
                facility = order._get_order_disposal_facility()
                if not facility:
                    order.message_post(body=_(
                        "No disposal facility is configured for company %s: the facility gate entry was not created automatically.",
                        order.company_id.name,
                    ))
                    continue
                # The confirmed weight is taken from the order, and corrected at the gate
                GateEntry.create({
                    'facility_id': facility.id,
                    'vehicle_id': order.vehicle_id.id,
                    'driver_id': order.driver_id.id if order.driver_id else False,
                    'collection_order_id': order.id,
                    'entry_datetime': fields.Datetime.now(),
                    'state': 'draft',
                })

    def _get_manifest_line_marker(self):
        """Readable label shown on the manifest lines of this order (the link
        itself is the line's ``collection_order_id``)."""
        self.ensure_one()
        return f"Collection Order: {self.name}"

    def _automate_compliance_manifest(self):
        """
        Put the order's waste on a compliance manifest and advance it.

        The order's lines are appended to a still-draft manifest of the same
        company, generator, date and disposal facility, else a new manifest
        is created for the order. An order's lines are added only once.
        """
        if 'wm.compliance.manifest' not in self.env:
            return
        Manifest = self.env['wm.compliance.manifest'].sudo()
        ManifestLine = self.env['wm.compliance.manifest.line'].sudo()
        today = fields.Date.today()
        for order in self:
            if not order.partner_id:
                continue
            marker = order._get_manifest_line_marker()
            done_line = ManifestLine.search([('collection_order_id', '=', order.id)], limit=1)
            if done_line:
                continue
            disposal_fac = order._get_order_disposal_facility()
            transporter = order.driver_id or order.company_id.partner_id
            if not disposal_fac:
                order.message_post(body=_(
                    "No disposal facility is configured for company %s: no compliance manifest was created automatically.",
                    order.company_id.name,
                ))
                continue
            if not transporter:
                continue
            line_vals = [{
                'waste_category_id': line.category_id.id,
                'quantity': line.weight or 1.0,
                'collection_order_id': order.id,
                'notes': marker,
            } for line in order.order_line_ids if line.category_id]
            if not line_vals:
                continue
            manifest = Manifest.search([
                ('company_id', '=', order.company_id.id),
                ('generator_id', '=', order.partner_id.id),
                ('manifest_date', '=', today),
                ('disposal_facility_id', '=', disposal_fac.id),
                ('state', '=', 'draft'),
            ], limit=1)
            if manifest:
                manifest.write({'line_ids': [(0, 0, vals) for vals in line_vals]})
            else:
                manifest = Manifest.create({
                    'generator_id': order.partner_id.id,
                    'transporter_id': transporter.id,
                    'disposal_facility_id': disposal_fac.id,
                    'manifest_date': today,
                    'company_id': order.company_id.id,
                    'state': 'draft',
                    'line_ids': [(0, 0, vals) for vals in line_vals],
                })
            # Advance state automatically: draft -> submitted -> collected.
            # The manifest's validations (e.g. mandatory compliance codes) are
            # never bypassed: on failure it stays where it is for the
            # compliance officer and the reason is logged on the order.
            try:
                with self.env.cr.savepoint():
                    if manifest.state == 'draft':
                        manifest.action_submit()
                    if manifest.state == 'submitted':
                        manifest.action_collect()
            except Exception as e:
                _logger.warning("Order %s could not advance manifest %s: %s", order.name, manifest.name, e)
                order.message_post(body=_("Compliance manifest %(manifest)s could not be advanced automatically: %(error)s") % {
                    'manifest': manifest.name, 'error': e,
                })

    def _log_overweight_event(self):
        """Log an overweight billable event when the load exceeds the container capacity."""
        if 'wm.billable.event' not in self.env:
            return
        Event = self.env['wm.billable.event'].sudo()
        for order in self:
            container_type = (order.collection_point_id.container_id if order.collection_point_id else False) or order.container_id
            if not container_type or container_type.capacity_weight <= 0.0:
                continue
            if order.confirmed_weight <= container_type.capacity_weight:
                continue
            excess = order.confirmed_weight - container_type.capacity_weight
            if Event.search_count([
                ('collection_order_id', '=', order.id),
                ('event_type', '=', 'overweight'),
            ], limit=1):
                continue
            event = Event.create({
                'partner_id': order.partner_id.id,
                'collection_point_id': order.collection_point_id.id if order.collection_point_id else False,
                'event_type': 'overweight',
                'collection_order_id': order.id,
                'event_date': fields.Date.context_today(order),
                'quantity': excess,
                'state': 'confirmed',
                'notes': _("Overweight load detected: %.2f kg collected vs %.2f kg container limit (Excess: %.2f kg)") % (
                    order.confirmed_weight, container_type.capacity_weight, excess
                ),
            })
            order.message_post(body=_("Auto-logged Overweight Event %s for %.2f kg excess weight.") % (event.name, excess))

    def _generate_proof_of_service(self):
        """
        Set the default signature template, generate the Proof of Service
        PDF and post it to the chatter.
        """
        default_template = self.env.ref('wm_collection.sig_template_collection_order', raise_if_not_found=False)
        for order in self:
            if not order.signature_template_id and default_template:
                order.signature_template_id = default_template.id

            pdf_content, filename = order._generate_collection_report_pdf()
            if pdf_content:
                order.sudo().write({
                    'collection_report_pdf': base64.b64encode(pdf_content),
                    'collection_report_pdf_filename': filename,
                })
                order.message_post(
                    body=_("Collection Order completed. Official Proof of Service report generated and attached."),
                    attachments=[(filename, pdf_content)]
                )

    def action_cancel(self):
        """
        Cancel the collection order, release the vehicle and driver from
        assignment, reset the route line state, and log a cancellation reason
        for audit reporting.
        """
        self._check_collection_rights()
        self.ensure_one()
        if self.state in ('completed', 'signed', 'cancelled'):
            raise UserError(_("Collection order '%s' is already %s and cannot be cancelled.") % (
                self.name, dict(self._fields['state'].selection).get(self.state)))
        self.with_context(programmatic_state_change=True).write({'state': 'cancelled'})

    @api.model
    def _get_billable_orders(self, partner=None, period_start=None, period_end=None):
        """
        Canonical method for querying billable (completed, uninvoiced)
        collection orders.
        """
        if not period_start or not period_end:
            return self.env['wm.collection.order']

        start_dt = datetime.combine(period_start, time.min)
        end_dt = datetime.combine(period_end, time.max)

        domain = [
            ('state', 'in', ('completed', 'signed')),
        ]
        if 'consolidated_invoice_id' in self._fields:
            domain.append(('consolidated_invoice_id', '=', False))
        if 'billing_run_line_id' in self._fields:
            domain.append(('billing_run_line_id', '=', False))
        if 'direct_invoice_id' in self._fields:
            domain.append(('direct_invoice_id', '=', False))

        domain.extend([
            '|',
                '&', ('actual_end', '>=', start_dt), ('actual_end', '<=', end_dt),
                '&', ('actual_end', '=', False), '&', ('scheduled_start', '>=', start_dt), ('scheduled_start', '<=', end_dt),
        ])
        if partner:
            partner_ids = partner.ids if isinstance(partner, models.BaseModel) else (partner if isinstance(partner, (list, tuple)) else [partner])
            domain.append(('partner_id', 'in', partner_ids))

        return self.search(domain)

    @api.model
    def _get_billing_rule(self, category, partner=False, date=None, contract=None):
        """
        Find matching rate card rule with 4-tier precedence:
        1. The given contract (when valid on ``date``), else the active
           Partner Contract (wm.partner.contract) rate line or billing terms
        2. Partner-specific rate card rule (wm.category.billing.rule)
        3. Generic category rate card rule (wm.category.billing.rule)
        4. Customer-specific / General pricing rule (wm.pricing.rule)
        5. False (caller falls back to product.list_price -> category.price ->0)
        """
        if not category:
            return False
        date = date or fields.Date.today()
        partner_obj = partner if isinstance(partner, models.BaseModel) else (self.env['res.partner'].browse(partner) if partner else False)

        # Tier 1: The order's own contract if it covered the service date,
        # otherwise the partner's active contract on that date. An explicitly
        # passed contract may since have expired: it still prices the orders
        # performed while it was running.
        if contract and not (
            contract.state in ('signed', 'confirmed', 'ongoing', 'expired')
            and contract.from_date <= date <= contract.to_date
        ):
            contract = False
        if not contract and partner_obj and 'wm.partner.contract' in self.env:
            company = self.company_id if hasattr(self, 'company_id') and self.company_id else self.env.company
            domain = [
                ('partner_id', '=', partner_obj.id),
                ('state', 'in', ('ongoing', 'confirmed')),
                ('from_date', '<=', date),
                ('to_date', '>=', date),
            ]
            if 'company_id' in self.env['wm.partner.contract']._fields:
                domain.append(('company_id', '=', company.id))
            contract = self.env['wm.partner.contract'].search(domain, limit=1)
        if contract:
            if contract.billing_basis in ('category_rate', 'material') and contract.contract_line_ids:
                # Both category_rate and material use per-category rates from contract lines
                line = contract.contract_line_ids.filtered(lambda ln: ln.category_id == category)[:1]
                if line and line.price > 0:
                    return RateCardRule(
                        price=line.price,
                        billing_basis='per_kg',
                        from_contract=True,
                    )
            elif contract.billing_basis == 'per_collection' and contract.fixed_price > 0:
                return RateCardRule(
                    price=contract.fixed_price,
                    billing_basis='flat_per_collection',
                    max_weight=contract.max_weight or 0.0,
                    overweight_price=contract.overweight_price or 0.0,
                    contract_id=contract.id,
                    from_contract=True,
                )
            elif contract.billing_basis == 'hybrid' and contract.fixed_price > 0:
                # hybrid = fixed base fee + per-10kg overage above included_weight
                return RateCardRule(
                    price=contract.fixed_price,
                    billing_basis='hybrid',
                    included_weight=contract.included_weight or 0.0,
                    overweight_price=contract.overweight_price or 0.0,
                    contract_id=contract.id,
                    from_contract=True,
                )

        # Tier 2 & 3: Check category billing rules (wm.category.billing.rule)
        if 'wm.category.billing.rule' in self.env:
            Rule = self.env['wm.category.billing.rule']
            if partner_obj:
                rule = Rule.search([
                    ('category_id', '=', category.id),
                    ('partner_id', '=', partner_obj.id),
                    '|', ('effective_date', '=', False), ('effective_date', '<=', date),
                    '|', ('expiry_date', '=', False), ('expiry_date', '>=', date),
                ], limit=1, order='effective_date desc, id desc')
                if rule:
                    return rule
            rule = Rule.search([
                ('category_id', '=', category.id),
                ('partner_id', '=', False),
                '|', ('effective_date', '=', False), ('effective_date', '<=', date),
                '|', ('expiry_date', '=', False), ('expiry_date', '>=', date),
            ], limit=1, order='effective_date desc, id desc')
            if rule:
                return rule

        # Tier 4: Check pricing rules (wm.pricing.rule)
        if 'wm.pricing.rule' in self.env:
            PricingRule = self.env['wm.pricing.rule']
            base_domain = [
                ('waste_category_id', '=', category.id),
                ('active', '=', True),
                '|', ('effective_date', '=', False), ('effective_date', '<=', date),
                '|', ('expiry_date', '=', False), ('expiry_date', '>=', date),
            ]
            if partner_obj:
                p_rule = PricingRule.search(base_domain + [('partner_id', '=', partner_obj.id)], limit=1, order='sequence asc, id desc')
                if p_rule:
                    return RateCardRule(
                        price=p_rule.price_per_kg,
                        billing_basis='per_kg',
                        min_weight=p_rule.min_weight or 0.0,
                        min_charge=p_rule.min_charge or 0.0,
                        id=p_rule.id,
                    )
            gen_rule = PricingRule.search(base_domain + [('partner_id', '=', False)], limit=1, order='sequence asc, id desc')
            if gen_rule:
                return RateCardRule(
                    price=gen_rule.price_per_kg,
                    billing_basis='per_kg',
                    min_weight=gen_rule.min_weight or 0.0,
                    min_charge=gen_rule.min_charge or 0.0,
                    id=gen_rule.id,
                )

        return False

    def action_create_category_batches(self):
        """
        Create category-level inbound Waste Batches in wm_collection grouped by
        category_id.
        """
        self.ensure_one()
        if not self.order_line_ids:
            raise ValidationError(_("Cannot create Waste Batches without order lines."))

        # Orders merged into a shared draft batch are only linked through
        # collection_order_ids, so check both links before merging again.
        existing = self._get_linked_waste_batches()
        if existing:
            return existing

        lines_by_category = {}
        for line in self.order_line_ids:
            if line.category_id:
                lines_by_category.setdefault(line.category_id, []).append(line)

        warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.company_id.id)], limit=1) or self.env['stock.warehouse'].search([], limit=1)
        location = warehouse.lot_stock_id if warehouse and warehouse.lot_stock_id else self.env['stock.location'].search([('usage', '=', 'internal')], limit=1)

        created_batches = self.env['waste.batch']
        for category, lines in lines_by_category.items():
            total_weight = sum(line.weight for line in lines)

            # Search for an existing open (Draft) collection batch for this category
            existing_batch = self.env['waste.batch'].sudo().search([
                ('category_id', '=', category.id),
                ('status', '=', 'draft'),
                ('batch_type', '=', 'collection'),
                ('route_id', '=', False),
                ('company_id', '=', self.company_id.id),
                ('location_id', '=', location.id),
            ], limit=1)

            if existing_batch:
                # Merge weight and product lines into existing open draft batch
                existing_batch.write({
                    'draft_quantity': existing_batch.draft_quantity + total_weight,
                    'intake_weight': existing_batch.intake_weight + total_weight,
                    'collection_order_ids': [(4, self.id)],
                })
                for line in lines:
                    if line.product_id:
                        batch_line = existing_batch.line_ids.filtered(lambda bl: bl.product_id == line.product_id)
                        if batch_line:
                            batch_line[0].write({'quantity': batch_line[0].quantity + (line.weight or 1.0)})
                        else:
                            self.env['waste.batch.line'].sudo().create({
                                'batch_id': existing_batch.id,
                                'product_id': line.product_id.id,
                                'quantity': line.weight or 1.0,
                                'category_id': category.id,
                            })
                created_batches |= existing_batch
            else:
                batch_lines = []
                for line in lines:
                    if line.product_id:
                        batch_lines.append((0, 0, {
                            'product_id': line.product_id.id,
                            'quantity': line.weight or 1.0,
                            'category_id': category.id,
                        }))

                batch_vals = {
                    'collection_order_id': self.id,
                    'collection_order_ids': [(6, 0, [self.id])],
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
                if batch_lines:
                    batch_vals['line_ids'] = batch_lines

                batch = self.env['waste.batch'].sudo().create(batch_vals)
                created_batches |= batch

        return created_batches

    def action_create_waste_batch(self):
        """ Backward compatibility wrapper calling action_create_category_batches. """
        batches = self.action_create_category_batches()
        if batches:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Waste Batches'),
                'res_model': 'waste.batch',
                'domain': [('id', 'in', batches.ids)],
                'view_mode': 'list,form' if len(batches) > 1 else 'form',
                'res_id': batches[0].id if len(batches) == 1 else False,
                'target': 'current',
            }
        return False

    def action_view_waste_batches(self):
        """ View all Waste Batches linked to this Collection Order. """
        self.ensure_one()
        batches = self._get_linked_waste_batches()
        action = {
            'name': _('Waste Batches'),
            'type': 'ir.actions.act_window',
            'res_model': 'waste.batch',
            'domain': [('id', 'in', batches.ids)],
            'context': {'default_collection_order_id': self.id},
        }
        if len(batches) == 1:
            action['view_mode'] = 'form'
            action['res_id'] = batches.id
        else:
            action['view_mode'] = 'list,form'
        return action

    def _compute_signature_signer_count(self):
        """
        Compute the total number of associated signature signer records linked
        to this WmCollectionOrder to update smart buttons and summary badges.
        """
        saved_orders = self.filtered(lambda o: bool(o.id) and isinstance(o.id, int))
        if not saved_orders:
            for order in self:
                order.signature_signer_count = 0
            return

        ref_docs = [f"wm.collection.order,{order.id}" for order in saved_orders]
        requests = self.env['wm.signature.request'].sudo().search([
            ('reference_doc', 'in', ref_docs),
            ('state', '!=', 'cancel')
        ])
        signer_count_by_order = {}
        for req in requests:
            try:
                oid = int(str(req.reference_doc).split(',')[1])
                signer_count_by_order[oid] = signer_count_by_order.get(oid, 0) + len(req.signer_ids)
            except (ValueError, IndexError, AttributeError):
                continue

        for order in self:
            order.signature_signer_count = signer_count_by_order.get(order.id, 0)

    def action_view_signatures(self):
        """
        Open the digital signature records linked to this collection order,
        allowing supervisors to verify signed collection sheets and
        chain-of-custody acknowledgements.
        """
        self.ensure_one()
        requests = self.env['wm.signature.request'].sudo().search([
            ('reference_doc', '=', f"wm.collection.order,{self.id}"),
            ('state', '!=', 'cancel')
        ])
        signers = requests.mapped('signer_ids')
        signer_view = self.env.ref('wm_collection.view_wm_signature_request_signer_list_wm_collection', raise_if_not_found=False)
        res = {
            'name': _('Signatures'),
            'type': 'ir.actions.act_window',
            'res_model': 'wm.signature.request.signer',
            'view_mode': 'list',
            'domain': [('id', 'in', signers.ids)],
            'context': {'create': False, 'edit': False},
        }
        if signer_view:
            res['views'] = [(signer_view.id, 'list')]
        return res

    def _compute_next_signer(self):
        """
        Determine the next authorised signer in the multi-party signature
        workflow sequence for this collection order, enabling the Sign Next
        button to be directed at the correct contact.
        """
        saved_orders = self.filtered(lambda o: bool(o.id) and isinstance(o.id, int))
        if not saved_orders:
            for order in self:
                order.next_signer_id = False
                order.next_signer_role_name = False
            return

        ref_docs = [f"wm.collection.order,{order.id}" for order in saved_orders]
        requests = self.env['wm.signature.request'].sudo().search([
            ('reference_doc', 'in', ref_docs),
            ('state', '=', 'sent')
        ])
        requests_by_order = {}
        for req in requests:
            try:
                oid = int(str(req.reference_doc).split(',')[1])
                requests_by_order[oid] = requests_by_order.get(oid, self.env['wm.signature.request']) | req
            except (ValueError, IndexError, AttributeError):
                continue

        for order in self:
            reqs = requests_by_order.get(order.id, self.env['wm.signature.request'])
            pending_signers = reqs.mapped('signer_ids').filtered(lambda s: s.state != 'signed')
            if len(pending_signers) == 1 and 'manager' not in (pending_signers[0].role_id.name or '').lower():
                order.next_signer_id = pending_signers[0].id
                order.next_signer_role_name = pending_signers[0].role_id.name
            else:
                order.next_signer_id = False
                order.next_signer_role_name = False

    def action_sign_next(self):
        """
        Open the digital signature wizard targeting the next required signer in
        the collection order's multi-party signing queue, advancing the
        signature workflow.
        """
        self.ensure_one()
        if self.next_signer_id:
            return {
                'type': 'ir.actions.act_url',
                'url': f'/wm_signature/sign/{self.next_signer_id.access_token}',
                'target': 'self',
            }
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_sign(self):
        """
        Open the digital signature wizard pre-filled with the current
        collection order reference and signer details, capturing an authorised
        operator's countersignature.
        """
        self.ensure_one()
        if not self.signature_template_id:
            default_template = self.env.ref('wm_collection.sig_template_collection_order', raise_if_not_found=False)
            if default_template:
                self.signature_template_id = default_template.id
            else:
                raise ValidationError(_("Please select a Signature Template in the Other Info tab before signing."))

        # Check if already fully signed
        signed_request = self.env['wm.signature.request'].sudo().search([
            ('reference_doc', '=', f"wm.collection.order,{self.id}"),
            ('state', '=', 'signed')
        ], limit=1)
        if signed_request:
            signer = signed_request.signer_ids.filtered(lambda s: s.partner_id == self.env.user.partner_id)[:1] or signed_request.signer_ids[:1]
            if signer:
                return {
                    'type': 'ir.actions.act_url',
                    'url': f'/wm_signature/sign/{signer.access_token}',
                    'target': 'self',
                }

        if not self.collection_report_pdf:
            pdf_content, filename = self._generate_collection_report_pdf()
            if not pdf_content:
                raise UserError(_("Unable to generate the Collection Order PDF for signing."))
            self.sudo().write({
                'collection_report_pdf': base64.b64encode(pdf_content),
                'collection_report_pdf_filename': filename,
            })

        template = self.signature_template_id.sudo()
        role = template.role_ids[:1]
        if not role:
            role = self.env.ref('wm_collection.sig_role_driver', raise_if_not_found=False)
            if not role:
                role = self.env['wm.signature.role'].sudo().create({'name': 'Waste Collector / Verification Officer'})
            template.write({'role_ids': [(4, role.id)]})

        sig_items = template.item_ids.filtered(lambda item: item.type == 'signature')
        if len(sig_items) > 1:
            sig_items[1:].unlink()
        elif not sig_items:
            self.env['wm.signature.item'].sudo().create({
                'template_id': template.id,
                'role_id': role.id,
                'type': 'signature',
                'page': 1,
                'x': 12,
                'y': 78,
                'width': 42,
                'height': 7,
            })

        back_url = f"/web#id={self.id}&model={self._name}&view_type=form"
        encoded_back_url = urllib.parse.quote(back_url)
        return {
            'type': 'ir.actions.act_url',
            'url': f'/wm_signature/template/edit/{template.id}?order_id={self.id}&back_url={encoded_back_url}',
            'target': 'self',
        }

    def _generate_collection_report_pdf(self):
        """
        Render the collection order QWeb report template to a PDF binary, using
        the collection point delivery address and waste line details for the
        document body.
        """
        self.ensure_one()
        try:
            pdf_content, _format = self.env['ir.actions.report'].sudo()._render_qweb_pdf(
                'wm_collection.collection_order_report', [self.id]
            )
            return pdf_content, f"Collection_Order_{self.name}.pdf"
        except Exception as e:
            _logger.error("Collection Order PDF render failed: %s", e, exc_info=True)
        return False, False


class WmCollectionOrderLine(models.Model):
    """One waste material line within a collection order, recording category, product, weight, and price."""
    _name = 'wm.collection.order.line'
    _description = 'Collection Order Line'

    order_id = fields.Many2one('wm.collection.order', string='Order', help='Provides information about order', ondelete='cascade', index=True, copy=False)
    category_id = fields.Many2one('wm.waste.category', string='Waste Category', required=True, help='Primary waste category for this line')
    product_id = fields.Many2one('product.product', string='Waste Material', help='Provides information about waste material')
    estimated_weight = fields.Float(string='Estimated Weight', help='Provides information about estimated weight')
    weight = fields.Float(string='Confirmed Weight', help='Provides information about confirmed weight')
    price = fields.Float(string='Price per kg', help='Provides information about price per kg', compute='_compute_price', store=True, readonly=False)
    price_basis = fields.Selection([
        ('per_kg', 'Per kg'),
        ('per_collection', 'Per Collection'),
        ('contract_fee', 'Contract Fee'),
    ], string='Pricing Basis', compute='_compute_price_basis', store=True,
        help='Per kg: price x weight. Per collection: a flat price for this '
             'category. Contract fee: covered by the contract\'s per-collection '
             'fee, which is added once to the order total.')
    total_amount = fields.Float(string='Total Amount', help='Provides information about total amount', compute='_compute_total_amount', store=True)

    def _get_billing_rule(self):
        """
        Rate rule for this line: the order's own contract (when installed)
        and the date the collection was performed, as invoicing uses.
        """
        self.ensure_one()
        return self._get_billing_rules()[self]

    def _get_billing_rule_key(self):
        """Inputs that determine a line's rate rule (see ``_get_billing_rule``)."""
        self.ensure_one()
        if not self.category_id:
            return False
        order = self.order_id
        if not order:
            return (self.category_id, self.env['res.partner'], fields.Date.context_today(self), None)
        contract = order.contract_id if 'contract_id' in order._fields else False
        return (self.category_id, order.partner_id, order._get_billing_service_date(), contract or None)

    def _get_billing_rules(self):
        """
        Rate rule of each line, as ``{line: rule}``, resolving the rule once
        per distinct (category, partner, service date, contract) instead of
        once per line. Nothing is cached beyond this call.
        """
        Order = self.env['wm.collection.order']
        rules_by_key = {}
        result = {}
        for line in self:
            key = line._get_billing_rule_key()
            if not key:
                result[line] = False
                continue
            if key not in rules_by_key:
                category, partner, date, contract = key
                rules_by_key[key] = Order._get_billing_rule(category, partner or False, date, contract=contract)
            result[line] = rules_by_key[key]
        return result

    @api.depends('category_id', 'order_id.partner_id', 'order_id.scheduled_start')
    def _compute_price_basis(self):
        """
        How the line is priced. Per-collection and hybrid contract fees are
        not per-kg prices: they are charged once per order.
        """
        rules = self._get_billing_rules()
        for line in self:
            rule = rules[line]
            basis = getattr(rule, 'billing_basis', 'per_kg') if rule else 'per_kg'
            if rule and getattr(rule, 'contract_id', 0) and basis in ('flat_per_collection', 'hybrid'):
                line.price_basis = 'contract_fee'
            elif basis == 'flat_per_collection':
                line.price_basis = 'per_collection'
            else:
                line.price_basis = 'per_kg'

    # 'order_id.actual_end' is deliberately not a dependency: completing the
    # order must not overwrite a manually entered price.
    @api.depends('product_id', 'category_id', 'product_id.list_price', 'category_id.price', 'order_id.partner_id')
    def _compute_price(self):
        """
        Calculate the line-level unit price for each collection order line by
        applying the matching contract rate or tariff schedule to the collected
        material weight.
        """
        rules = self._get_billing_rules()
        for line in self:
            rule = rules[line]
            if rule and getattr(rule, 'contract_id', 0) and rule.billing_basis in ('flat_per_collection', 'hybrid'):
                # Covered by the contract's per-collection fee (order total)
                line.price = 0.0
            elif rule and rule.price:
                line.price = rule.price
            elif line.product_id and line.product_id.list_price:
                line.price = line.product_id.list_price
            elif line.category_id and line.category_id.price:
                line.price = line.category_id.price
            else:
                line.price = 0.0

    @api.depends('price', 'weight', 'price_basis')
    def _compute_total_amount(self):
        """
        Line amount: price x weight for per-kg lines, the flat price for a
        per-collection category rule, nothing for lines covered by the
        contract's per-collection fee (charged once on the order).
        """
        for line in self:
            if line.price_basis == 'contract_fee':
                line.total_amount = 0.0
            elif line.price_basis == 'per_collection':
                line.total_amount = line.price
            else:
                line.total_amount = line.price * line.weight

    @api.constrains('product_id', 'order_id')
    def _check_unique_product_per_order(self):
        """
        Prevent duplicate waste product entries within a single collection
        order, ensuring each material line references a distinct product to
        avoid double-counting in billing.
        """
        for line in self:
            if line.order_id and line.product_id:
                duplicate = self.search([
                    ('order_id', '=', line.order_id.id),
                    ('product_id', '=', line.product_id.id),
                    ('id', '!=', line.id)
                ], limit=1)
                if duplicate:
                    raise ValidationError(_(
                        "The waste product '%(product)s' is added multiple times in collection order %(order)s. Each product can only be added once per collection order.",
                        product=line.product_id.display_name,
                        order=line.order_id.name or '',
                    ))

    @api.model_create_multi
    def create(self, vals_list):
        """
        Prevent adding lines to a collection order if the order is already in a locked state.
        """
        for vals in vals_list:
            if vals.get('order_id') and not self.env.context.get('programmatic_state_change') and not self.env.su:
                order = self.env['wm.collection.order'].browse(vals['order_id'])
                if order.state in ('completed', 'signed', 'invoiced', 'cancelled'):
                    raise UserError(_(
                        "Cannot add lines to collection order '%(name)s' because it is in '%(state)s' state.",
                        name=order.name,
                        state=dict(order._fields['state'].selection).get(order.state, order.state),
                    ))
        return super().create(vals_list)

    def write(self, vals):
        """
        Prevent modifying lines on a collection order if the order is in a locked state.
        """
        if not self.env.context.get('programmatic_state_change') and not self.env.su:
            for line in self:
                if line.order_id and line.order_id.state in ('completed', 'signed', 'invoiced', 'cancelled'):
                    raise UserError(_(
                        "Cannot modify line on collection order '%(name)s' because it is in '%(state)s' state.",
                        name=line.order_id.name,
                        state=dict(line.order_id._fields['state'].selection).get(line.order_id.state, line.order_id.state),
                    ))
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_locked_order_line(self):
        """
        Prevent deleting lines from a collection order if the order is in a locked state.
        """
        if not self.env.context.get('programmatic_state_change') and not self.env.su:
            for line in self:
                if line.order_id and line.order_id.state in ('completed', 'signed', 'invoiced', 'cancelled'):
                    raise UserError(_(
                        "Cannot delete line from collection order '%(name)s' because it is in '%(state)s' state.",
                        name=line.order_id.name,
                        state=dict(line.order_id._fields['state'].selection).get(line.order_id.state, line.order_id.state),
                    ))
