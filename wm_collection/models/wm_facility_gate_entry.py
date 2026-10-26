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
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class WmFacilityGateEntry(models.Model):
    """Model tracking truck scale intake, four-way weight reconciliation, and facility acceptance/rejection."""
    _name = 'wm.facility.gate.entry'
    _description = 'Facility Gate Entry & Weight Reconciliation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'entry_datetime desc, id desc'

    name = fields.Char(
        string='Gate Ticket #',
        default=lambda self: _('New'),
        copy=False,
        readonly=True,
        required=True
    )
    facility_id = fields.Many2one(
        'wm.disposal.facility',
        string='Disposal / Processing Facility',
        required=True,
        tracking=True
    )
    vehicle_id = fields.Many2one(
        'fleet.vehicle',
        string='Vehicle / Truck',
        required=True,
        tracking=True
    )
    driver_id = fields.Many2one(
        'res.partner',
        string='Driver',
        tracking=True
    )
    collection_order_id = fields.Many2one(
        'wm.collection.order',
        string='Collection Order',
        domain="[('state', 'in', ('completed', 'signed')), '|', ('gate_entry_ids', '=', False), ('gate_entry_ids.state', '=', 'cancelled')]",
        tracking=True
    )

    entry_datetime = fields.Datetime(
        string='Gate In Time',
        default=fields.Datetime.now,
        required=True,
        tracking=True
    )
    exit_datetime = fields.Datetime(
        string='Gate Out Time',
        tracking=True
    )
    confirmed_weight = fields.Float(
        string='Confirmed Weight (kg)',
        compute='_compute_confirmed_weight',
        store=True,
        readonly=False,
        tracking=True,
        help='Payload weight in kg received at the gate. Taken from the linked collection order, '
             'and can be corrected at the gate.'
    )
    estimated_weight = fields.Float(
        string='Estimated Weight (kg)',
        compute='_compute_estimated_weight',
        store=True,
        readonly=False,
        tracking=True,
        help='Expected waste payload weight from the order schedule.'
    )
    accepted_weight = fields.Float(
        string='Accepted Weight (kg)',
        compute='_compute_line_totals',
        store=True,
        readonly=False,
        tracking=True,
        help='Weight of waste accepted into facility.'
    )
    rejected_weight = fields.Float(
        string='Rejected Weight (kg)',
        compute='_compute_line_totals',
        store=True,
        readonly=False,
        tracking=True,
        help='Weight of waste rejected (e.g. contamination, unpermitted items).'
    )
    weight_variance = fields.Float(
        string='Weight Variance (kg)',
        compute='_compute_weight_variance',
        store=True,
        help='Total Gate Entry Intake Weight (Accepted + Rejected) minus Collection Order Confirmed Weight.'
    )
    reconciliation_status = fields.Selection([
        ('balanced', 'Balanced (Within Tolerance)'),
        ('overweight', 'Overweight Load'),
        ('underweight', 'Underweight Load'),
        ('rejected_items', 'Rejected Payload Detected'),
    ], string='Reconciliation Status', compute='_compute_reconciliation_status', store=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'Weighing / In Progress'),
        ('accepted', 'Accepted & Received'),
        ('partially_rejected', 'Partially Rejected'),
        ('rejected', 'Fully Rejected'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True, copy=False)
    rejection_reason = fields.Text(string='Rejection Reason / Notes')
    line_ids = fields.One2many(
        'wm.facility.gate.entry.line',
        'gate_entry_id',
        string='Payload Category Lines'
    )
    allowed_collection_point_ids = fields.Many2many(
        'wm.collection.point',
        compute='_compute_allowed_collection_points',
        string='Allowed Collection Points'
    )
    rejection_line_ids = fields.One2many(
        'wm.facility.gate.entry.rejection.line',
        'gate_entry_id',
        string='Itemized Rejections & Contamination'
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )
    billable_event_count = fields.Integer(
        string='Billable Event Count',
        compute='_compute_billable_event_count'
    )

    @api.depends('collection_order_id', 'collection_order_id.collection_point_id')
    def _compute_allowed_collection_points(self):
        """Collection points a rejection may be itemized on: the linked order's point."""
        for rec in self:
            rec.allowed_collection_point_ids = rec.collection_order_id.collection_point_id

    @api.model_create_multi
    def create(self, vals_list):
        enabled = self.env['ir.config_parameter'].sudo().get_param('wm_collection.use_facility_gate_entry', 'True') in ('True', '1')
        if not enabled:
            raise UserError(_("Facility Gate Entries feature is disabled in Waste Management settings."))
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('wm.facility.gate.entry') or _('New')
        return super().create(vals_list)

    @api.onchange('collection_order_id')
    def _onchange_collection_order_id(self):
        """Auto-populate payload breakdown lines and header defaults from the selected collection order."""
        if not self.collection_order_id:
            return

        order = self.collection_order_id
        if hasattr(order, 'vehicle_id') and order.vehicle_id and not self.vehicle_id:
            self.vehicle_id = order.vehicle_id
        if hasattr(order, 'driver_id') and order.driver_id and not self.driver_id:
            self.driver_id = order.driver_id

        new_lines = []
        if hasattr(order, 'order_line_ids') and order.order_line_ids:
            for line in order.order_line_ids:
                category = getattr(line, 'category_id', False) or (
                    getattr(line.product_id, 'wm_waste_category_id', False) if getattr(line, 'product_id', False) else False
                )
                if category:
                    est_wt = getattr(line, 'estimated_weight', 0.0) or getattr(line, 'weight', 0.0) or 0.0
                    new_lines.append((0, 0, {
                        'waste_category_id': category.id,
                        'estimated_weight': est_wt,
                        'accepted_weight': est_wt,
                    }))
        elif hasattr(order, 'waste_category_id') and order.waste_category_id:
            est_wt = getattr(order, 'estimated_weight', 0.0) or 0.0
            new_lines.append((0, 0, {
                'waste_category_id': order.waste_category_id.id,
                'estimated_weight': est_wt,
                'accepted_weight': est_wt,
            }))

        if new_lines:
            self.line_ids = [(5, 0, 0)] + new_lines

    @api.depends('collection_order_id', 'collection_order_id.confirmed_weight', 'collection_order_id.estimated_weight', 'collection_order_id.order_line_ids.weight')
    def _compute_confirmed_weight(self):
        """Compute confirmed weight from linked collection order."""
        for rec in self:
            if rec.collection_order_id:
                rec.confirmed_weight = (
                    getattr(rec.collection_order_id, 'confirmed_weight', 0.0)
                    or sum(rec.collection_order_id.order_line_ids.mapped('weight'))
                    or getattr(rec.collection_order_id, 'estimated_weight', 0.0)
                    or 0.0
                )
            else:
                rec.confirmed_weight = rec.confirmed_weight or 0.0

    @api.constrains('confirmed_weight')
    def _check_confirmed_weight(self):
        """Ensure the confirmed weight entered at the gate is not negative."""
        for rec in self:
            if rec.confirmed_weight < 0.0:
                raise ValidationError(_("Confirmed Weight cannot be negative."))

    @api.constrains('collection_order_id', 'state')
    def _check_unique_collection_order(self):
        """Ensure a collection order is completed/signed and not assigned to multiple active gate entries."""
        for rec in self:
            if rec.collection_order_id and rec.state != 'cancelled':
                if rec.collection_order_id.state not in ('completed', 'signed'):
                    raise ValidationError(_(
                        "Collection Order '%(order)s' is currently in state '%(order_state)s'. "
                        "Only 'Completed' or 'Signed' collection orders can be assigned to a Gate Entry.",
                        order=rec.collection_order_id.name,
                        order_state=dict(rec.collection_order_id._fields['state'].selection).get(
                            rec.collection_order_id.state, rec.collection_order_id.state
                        ),
                    ))
                duplicate = self.search([
                    ('collection_order_id', '=', rec.collection_order_id.id),
                    ('state', '!=', 'cancelled'),
                    ('id', '!=', rec.id)
                ], limit=1)
                if duplicate:
                    raise ValidationError(_(
                        "Collection Order '%(order)s' is already assigned to active Gate Entry '%(entry)s'. "
                        "A Collection Order can only be linked to one active Gate Entry.",
                        order=rec.collection_order_id.name,
                        entry=duplicate.name,
                    ))

    @api.depends('collection_order_id', 'line_ids.estimated_weight')
    def _compute_estimated_weight(self):
        for rec in self:
            if rec.line_ids and any(ln.estimated_weight for ln in rec.line_ids):
                rec.estimated_weight = sum(rec.line_ids.mapped('estimated_weight'))
            elif rec.collection_order_id:
                rec.estimated_weight = getattr(rec.collection_order_id, 'estimated_weight', 0.0) or 0.0
            else:
                rec.estimated_weight = rec.estimated_weight or 0.0

    @api.depends('line_ids.accepted_weight', 'line_ids.rejected_weight', 'rejection_line_ids.rejected_weight')
    def _compute_line_totals(self):
        for rec in self:
            if rec.line_ids:
                rec.accepted_weight = sum(rec.line_ids.mapped('accepted_weight'))
            if rec.rejection_line_ids:
                rec.rejected_weight = sum(rec.rejection_line_ids.mapped('rejected_weight'))
            elif rec.line_ids:
                rec.rejected_weight = sum(rec.line_ids.mapped('rejected_weight'))

    @api.depends('accepted_weight', 'rejected_weight', 'confirmed_weight', 'estimated_weight', 'collection_order_id', 'collection_order_id.confirmed_weight', 'collection_order_id.estimated_weight')
    def _compute_weight_variance(self):
        """
        Compute Weight Variance by comparing total Gate Entry Intake Weight
        (accepted_weight + rejected_weight, or the gate's confirmed weight) against the
        total confirmed weight from the linked Collection Order (or estimated weight).
        """
        for rec in self:
            gate_intake_weight = (rec.accepted_weight or 0.0) + (rec.rejected_weight or 0.0)
            if gate_intake_weight <= 0.0 and rec.confirmed_weight > 0.0:
                gate_intake_weight = rec.confirmed_weight

            # The gate's own confirmed weight is what was received, so it is never the
            # baseline: that is the order's weight, else the expected weight.
            order_confirmed_weight = 0.0
            if rec.collection_order_id:
                order_confirmed_weight = (
                    getattr(rec.collection_order_id, 'confirmed_weight', 0.0)
                    or getattr(rec.collection_order_id, 'estimated_weight', 0.0)
                    or rec.estimated_weight
                    or 0.0
                )
            else:
                order_confirmed_weight = rec.estimated_weight or 0.0

            # Nothing to compare against: no variance rather than the whole load
            rec.weight_variance = gate_intake_weight - order_confirmed_weight if order_confirmed_weight else 0.0

    @api.depends('rejected_weight', 'weight_variance', 'accepted_weight', 'confirmed_weight')
    def _compute_reconciliation_status(self):
        """
        Compute Reconciliation Status based on gate entry rejected weight and
        weight variance relative to collection order confirmed weight.
        """
        for rec in self:
            if rec.rejected_weight > 0.0:
                rec.reconciliation_status = 'rejected_items'
            elif abs(rec.weight_variance) <= 50.0:
                rec.reconciliation_status = 'balanced'
            elif rec.weight_variance > 50.0:
                rec.reconciliation_status = 'overweight'
            else:
                rec.reconciliation_status = 'underweight'

    def _compute_billable_event_count(self):
        for rec in self:
            if 'wm.billable.event' in self.env and rec.id:
                rec.billable_event_count = self.env['wm.billable.event'].search_count([('gate_entry_id', '=', rec.id)])
            else:
                rec.billable_event_count = 0

    def action_start_weighing(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_("Only draft gate entries can be moved to weighing."))
            rec.write({'state': 'in_progress'})

    def action_process_reconciliation(self):
        for rec in self:
            if rec.state not in ('draft', 'in_progress'):
                raise UserError(_("Only draft or in-progress gate entries can be reconciled."))
            if rec.confirmed_weight <= 0.0 and rec.accepted_weight + rec.rejected_weight <= 0.0:
                raise ValidationError(_(
                    "Enter the Confirmed Weight, or the accepted or rejected weight, before processing reconciliation."))

            # Auto sync accepted/rejected weight if lines are empty
            if not rec.line_ids and rec.accepted_weight == 0.0:
                # Route entries carry only itemised rejections: whatever was
                # weighed in and not rejected is accepted.
                rec.accepted_weight = max(rec.confirmed_weight - rec.rejected_weight, 0.0)

            # Determine final state
            if rec.rejected_weight > 0 and rec.accepted_weight > 0:
                final_state = 'partially_rejected'
            elif rec.rejected_weight > 0 and rec.accepted_weight == 0:
                final_state = 'rejected'
            else:
                final_state = 'accepted'

            values = {'state': final_state}
            if not rec.exit_datetime:
                values['exit_datetime'] = fields.Datetime.now()
            rec.write(values)

            # Trigger Downstream Integrations
            rec._trigger_billing_events()
            rec._trigger_compliance_custody()
            rec._trigger_inventory_intake()

    def action_cancel(self):
        for rec in self:
            if rec.state in ('accepted', 'cancelled'):
                raise UserError(_("Accepted or already cancelled gate entries cannot be cancelled."))
            rec.write({'state': 'cancelled'})

    def action_reset_draft(self):
        for rec in self:
            if rec.state in ('draft', 'accepted'):
                raise UserError(_("Draft or accepted gate entries cannot be reset to draft."))
            rec.write({'state': 'draft'})

    def action_view_billable_events(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("wm_contracts_billing.action_wm_billable_event")
        action['domain'] = [('gate_entry_id', '=', self.id)]
        action['context'] = {'default_gate_entry_id': self.id}
        return action

    # -------------------------------------------------------------------------
    # Downstream Integrations
    # -------------------------------------------------------------------------

    def _trigger_billing_events(self):
        """Auto-creates wm.billable.event records for contamination or overweight loads."""
        if 'wm.billable.event' not in self.env:
            return
        # Gate operators cannot create billable events themselves (finance data)
        BillableEvent = self.env['wm.billable.event'].sudo()
        for rec in self:
            # Load-level charges go to the order's customer only. A load without an
            # order is billed through itemized rejection lines instead (never to
            # the driver).
            partner = rec.collection_order_id.partner_id if rec.collection_order_id else False
            # Re-processing an entry (after Reset to Draft) must not bill again
            existing_types = set(BillableEvent.search([('gate_entry_id', '=', rec.id)]).mapped('event_type'))

            # 1. Contamination / Rejection event
            if rec.rejection_line_ids:
                for rline in rec.rejection_line_ids:
                    if rline.rejected_weight > 0 and rline.partner_id and not getattr(rline, 'billable_event_id', False):
                        event = BillableEvent.create({
                            'partner_id': rline.partner_id.id,
                            'collection_point_id': rline.collection_point_id.id,
                            'event_type': 'contamination',
                            'event_date': fields.Date.today(),
                            'collection_order_id': rec.collection_order_id.id if rec.collection_order_id else False,
                            'gate_entry_id': rec.id,
                            'quantity': rline.rejected_weight,
                            'state': 'confirmed',
                            'notes': _("Gate Entry %s Itemized Rejection at %s: %s kg (Reason: %s)") % (
                                rec.name,
                                rline.collection_point_id.display_name,
                                rline.rejected_weight,
                                rline.rejection_reason or _("Unspecified")
                            )
                        })
                        if hasattr(rline, 'billable_event_id'):
                            rline.billable_event_id = event.id
            elif rec.rejected_weight > 0 or rec.state in ['rejected', 'partially_rejected']:
                if partner and 'contamination' not in existing_types:
                    BillableEvent.create({
                        'partner_id': partner.id,
                        'event_type': 'contamination',
                        'event_date': fields.Date.today(),
                        'collection_order_id': rec.collection_order_id.id if rec.collection_order_id else False,
                        'gate_entry_id': rec.id,
                        'quantity': rec.rejected_weight or 1.0,
                        'state': 'confirmed',
                        'notes': _("Gate Entry %s Rejected Payload: %s (Reason: %s)") % (
                            rec.name,
                            f"{rec.rejected_weight} kg",
                            rec.rejection_reason or _("Unspecified")
                        )
                    })

            # 2. Overweight event (if variance > 100 kg threshold)
            if rec.weight_variance > 100.0:
                if partner and 'overweight' not in existing_types:
                    BillableEvent.create({
                        'partner_id': partner.id,
                        'event_type': 'overweight',
                        'event_date': fields.Date.today(),
                        'collection_order_id': rec.collection_order_id.id if rec.collection_order_id else False,
                        'gate_entry_id': rec.id,
                        'quantity': rec.weight_variance,
                        'state': 'confirmed',
                        'notes': _("Gate Entry %s Overweight Payload Variance: %s kg (Est: %s kg, Confirmed: %s kg)") % (
                            rec.name,
                            rec.weight_variance,
                            rec.estimated_weight,
                            rec.confirmed_weight
                        )
                    })

    def _trigger_compliance_custody(self):
        """Auto-logs compliance custody transfer/disposition milestone if wm.compliance.custody exists."""
        if 'wm.compliance.custody' not in self.env or 'wm.compliance.manifest' not in self.env:
            return
        Custody = self.env['wm.compliance.custody']
        Manifest = self.env['wm.compliance.manifest']
        for rec in self:
            # Only the manifests of the customers whose waste is on this load
            generators = rec.collection_order_id.partner_id | rec.rejection_line_ids.mapped('partner_id')
            if not generators:
                continue
            manifests = Manifest.search([
                ('disposal_facility_id', '=', rec.facility_id.id),
                ('generator_id', 'in', generators.ids),
                ('state', 'in', ['submitted', 'collected']),
            ])
            action_type = 'disposed' if rec.state == 'accepted' else 'received'
            notes = _("Facility Gate Entry %s intake complete at %s. Confirmed Weight: %s kg, Accepted: %s kg, Rejected: %s kg.") % (
                rec.name,
                rec.facility_id.name,
                rec.confirmed_weight,
                rec.accepted_weight,
                rec.rejected_weight
            )
            for manifest in manifests:
                Custody.create({
                    'manifest_id': manifest.id,
                    'action': action_type,
                    'location': rec.facility_id.name or '',
                    'notes': notes,
                })
                # A fully accepted load completes the manifest (-> Certificate
                # of Destruction). Rejected or partially rejected loads stay
                # open for the compliance officer. The manifest's own
                # validations are never bypassed.
                if rec.state != 'accepted':
                    continue
                try:
                    with self.env.cr.savepoint():
                        if manifest.state == 'submitted':
                            manifest.action_collect()
                        if manifest.state == 'collected':
                            manifest.action_dispose()
                except Exception as e:
                    _logger.warning("Gate entry %s could not dispose manifest %s: %s", rec.name, manifest.name, e)
                    rec.message_post(body=_("Manifest %(manifest)s could not be disposed automatically: %(error)s") % {
                        'manifest': manifest.name, 'error': e,
                    })

    def _trigger_inventory_intake(self):
        """Auto-creates or updates waste batches in inventory for accepted intake."""
        if 'waste.batch' not in self.env:
            return
        WasteBatch = self.env['waste.batch']
        for rec in self:
            if rec.accepted_weight <= 0.0:
                continue
            # Already batched by this entry (re-processing), or by the order on
            # completion: creating more would count the waste twice.
            if WasteBatch.search_count([('name', '=like', 'INTAKE/%s%%' % rec.name)]):
                continue
            batch_domain = []
            if rec.collection_order_id:
                batch_domain = ['|', ('collection_order_id', '=', rec.collection_order_id.id),
                                ('collection_order_ids', 'in', rec.collection_order_id.ids)]
            if batch_domain and WasteBatch.search_count(batch_domain):
                continue

            lines_to_process = rec.line_ids.filtered(lambda ln: ln.accepted_weight > 0)
            if lines_to_process:
                for line in lines_to_process:
                    WasteBatch.create({
                        'name': _("INTAKE/%s/%s") % (rec.name, line.waste_category_id.name or 'GEN'),
                        'category_id': line.waste_category_id.id,
                        'gross_weight': line.accepted_weight,
                        'draft_quantity': line.accepted_weight,
                        'intake_weight': line.accepted_weight,
                        'collection_order_id': rec.collection_order_id.id if rec.collection_order_id else False,
                        'intake_notes': _("Received via Gate Entry %s at Facility %s.") % (rec.name, rec.facility_id.name)
                    })
            else:
                cat = rec.collection_order_id.waste_category_id if rec.collection_order_id and getattr(rec.collection_order_id, 'waste_category_id', False) else False
                if not cat:
                    cat = self.env['wm.waste.category'].search([], limit=1)
                if cat:
                    WasteBatch.create({
                        'name': _("INTAKE/%s") % (rec.name,),
                        'category_id': cat.id,
                        'gross_weight': rec.accepted_weight,
                        'draft_quantity': rec.accepted_weight,
                        'intake_weight': rec.accepted_weight,
                        'collection_order_id': rec.collection_order_id.id if rec.collection_order_id else False,
                        'intake_notes': _("Bulk load received via Gate Entry %s at Facility %s.") % (rec.name, rec.facility_id.name)
                    })


class WmFacilityGateEntryLine(models.Model):
    """Payload line for waste breakdown at facility gate entry."""
    _name = 'wm.facility.gate.entry.line'
    _description = 'Facility Gate Entry Payload Line'

    gate_entry_id = fields.Many2one(
        'wm.facility.gate.entry',
        string='Gate Entry Ticket',
        required=True,
        ondelete='cascade'
    )
    waste_category_id = fields.Many2one(
        'wm.waste.category',
        string='Waste Category',
        required=True
    )
    container_id = fields.Many2one(
        'wm.container',
        string='Container'
    )
    estimated_weight = fields.Float(string='Estimated Weight (kg)', default=0.0)
    accepted_weight = fields.Float(string='Accepted Weight (kg)', default=0.0)
    rejected_weight = fields.Float(string='Rejected Weight (kg)', default=0.0)
    rejection_reason = fields.Char(string='Rejection Reason')
    notes = fields.Text(string='Notes')


class WmFacilityGateEntryRejectionLine(models.Model):
    """Line model tracking itemized contamination and waste rejection per customer collection point."""
    _name = 'wm.facility.gate.entry.rejection.line'
    _description = 'Facility Gate Entry Rejection & Contamination Line'

    gate_entry_id = fields.Many2one(
        'wm.facility.gate.entry',
        string='Gate Entry Ticket',
        required=True,
        ondelete='cascade'
    )
    collection_point_id = fields.Many2one(
        'wm.collection.point',
        string='Collection Site / Customer Location',
        required=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        related='collection_point_id.partner_id',
        store=True,
        readonly=True
    )
    rejected_weight = fields.Float(
        string='Rejected Weight (kg)',
        default=0.0,
        required=True,
        help='Weight of contaminated or turned-away waste for this customer.'
    )
    rejection_reason = fields.Char(
        string='Rejection Reason / Contamination Details',
        help='Reason for rejection or specific contamination observed.'
    )

    @api.constrains('collection_point_id', 'gate_entry_id')
    def _check_collection_point_order(self):
        """Ensure selected collection point belongs to the collection order of the gate entry."""
        for line in self:
            if not line.gate_entry_id or not line.collection_point_id:
                continue
            allowed_points = line.gate_entry_id.allowed_collection_point_ids
            if allowed_points and line.collection_point_id not in allowed_points:
                raise ValidationError(_(
                    "Collection Point '%(point)s' (Customer: %(partner)s) is not the collection point of order '%(order)s'.",
                    point=line.collection_point_id.display_name,
                    partner=line.partner_id.name if line.partner_id else _('Unknown'),
                    order=line.gate_entry_id.collection_order_id.display_name,
                ))


class WmDisposalFacilityGateExt(models.Model):
    """Extends Disposal Facility with gate entry relational fields and smart button."""
    _inherit = 'wm.disposal.facility'

    gate_entry_ids = fields.One2many(
        'wm.facility.gate.entry',
        'facility_id',
        string='Facility Gate Entries'
    )
    gate_entry_count = fields.Integer(
        string='Gate Entry Count',
        compute='_compute_gate_entry_count'
    )

    def _compute_gate_entry_count(self):
        for facility in self:
            facility.gate_entry_count = len(facility.gate_entry_ids)

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
            'domain': [('facility_id', '=', self.id)],
            'context': {'default_facility_id': self.id},
        }
