# -*- coding: utf-8 -*-
#############################################################################
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
# ############################################################################

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.translate import _

class CustodyTransfer(models.Model):
    """
    Main custody transfer document.

    Acts as the legal and operational workflow layer above inventory movement.
    Uses stock.picking.type (Operation Type) to define the nature of the
    transfer instead of a separate configuration model. Fields are auto-
    populated from the linked stock picking when the operator clicks
    'Update from Transfer'.
    """
    _name = "custody.transfer"
    _description = "Custody Transfer"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "transfer_date desc, name desc"
    _rec_name = "name"

    # -------------------------------------------------------------------------
    # Identity
    # -------------------------------------------------------------------------
    name = fields.Char(
        string="Transfer Number",
        required=True,
        copy=False,
        default=lambda self: _("New"),
        tracking=True, help="A unique name or reference identifier used to track this record in the system.",
    )
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id, help="Link this transaction or record to the corresponding 'currency' reference.")
    picking_type_id = fields.Many2one(
        "stock.picking.type",
        string="Operation Type",
        required=True,
        tracking=True,
        help="Odoo operation type that defines the nature of this custody transfer "
             "(e.g. Receipts, Delivery Orders, Internal Transfers). "
             "Auto-filled from the linked stock transfer.",
    )
    picking_code = fields.Selection(
        related="picking_type_id.code",
        string="Operation Type Code", help="Select the appropriate classification or category for 'operation type code'.",
    )

    transfer_date = fields.Datetime(
        string="Transfer Date",
        required=True,
        default=fields.Datetime.now,
        tracking=True,
        help="Date and time when the physical custody handover occurs.",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company, help="The company managing this operational record or transaction.",
    )
    reference = fields.Char(
        string="External Reference",
        help="External document number (e.g. picking name, PO number).",
    )
    seal_number = fields.Char(string="Seal Number", help="Specify the description or text value representing 'seal number'.")

    # Transfer purpose / reason
    transfer_purpose = fields.Selection(
        [
            ('commercial_sale', 'Commercial Sale'),
            ('inter_facility', 'Inter-Facility Transfer'),
            ('emergency', 'Emergency Transfer'),
            ('intercompany', 'Intercompany'),
            ('pipeline_injection', 'Pipeline Injection'),
            ('other', 'Other'),
        ],
        string='Transfer Purpose',
        tracking=True,
        help='Commercial or operational reason for this custody transfer.',
    )

    # Bill of lading
    bill_of_lading_ref = fields.Char(
        string='Bill of Lading No.',
        tracking=True,
        help='Official Bill of Lading reference number issued by the carrier.',
    )
    bill_of_lading_attachment = fields.Many2many(
        'ir.attachment',
        'custody_transfer_bol_attachment_rel',
        'transfer_id',
        'attachment_id',
        string='Bill of Lading Document',
        help='Attach the signed Bill of Lading document(s) here.',
    )

    # Demurrage
    demurrage_hours = fields.Float(
        string='Demurrage Hours',
        digits=(10, 2),
        tracking=True,
        help='Total hours of delay beyond the allowed laytime for loading/unloading.',
    )
    demurrage_rate = fields.Monetary(
        string='Demurrage Rate (per hour)',
        currency_field='currency_id',
        help='Contractual demurrage rate per hour. Used to compute total demurrage cost.',
    )
    demurrage_cost = fields.Monetary(
        string='Demurrage Cost',
        currency_field='currency_id',
        compute='_compute_demurrage_cost',
        store=True,
        tracking=True,
        help='Total demurrage cost: demurrage_hours × demurrage_rate.',
    )

    # Crude quality at loading and arrival
    api_gravity_loading = fields.Float(
        string='API Gravity (Loading)',
        digits=(6, 2),
        tracking=True,
        help='API gravity of the crude measured at the loading point.',
    )
    api_gravity_arrival = fields.Float(
        string='API Gravity (Arrival)',
        digits=(6, 2),
        tracking=True,
        help='API gravity of the crude measured at the arrival/destination point.',
    )

    notes = fields.Html(string="Internal Notes", help="Additional comments, details, or operational remarks about this record.")

    # -------------------------------------------------------------------------
    # Workflow configuration (direct on document, not via a type model)
    # -------------------------------------------------------------------------
    approval_policy = fields.Selection(
        [("single", "Single Approval"), ("dual", "Dual Approval")],
        string="Approval Policy",
        default="single",
        required=True,
        tracking=True,
        help="Single: one approver is sufficient. "
             "Dual: a second approver (different user) is required before "
             "the custody transfer can proceed.",
    )

    # -------------------------------------------------------------------------
    # Standard measurement conditions (Phase 2)
    # -------------------------------------------------------------------------
    measurement_method = fields.Selection(
        [
            ("manual", "Manual"),
            ("auto", "Auto (SCADA)"),
        ],
        string="Measurement Method",
        default="manual",
        help="Method used to measure product quantities on this transfer. "
             "If Auto (SCADA), temperatures and pressures are fetched from the source location.",
    )
    is_scada_installed = fields.Boolean(
        compute="_compute_is_scada_installed",
        string="Is SCADA Installed", help="Enable or activate this option to apply 'is scada installed' status to the record.",
    )

    def _compute_is_scada_installed(self):
        """Calculates and updates the 'scada installed' value automatically based on related operational inputs."""
        installed = self._is_scada_installed()
        for record in self:
            record.is_scada_installed = installed

    def _is_scada_installed(self):
        """Executes the 'is scada installed' process within the operational workflow."""
        scada_module = self.env['ir.module.module'].sudo().search([('name', '=', 'oil_erp_scada')], limit=1)
        return bool(scada_module and scada_module.state == 'installed')

    # -------------------------------------------------------------------------
    # Workflow state
    # -------------------------------------------------------------------------
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("approved", "Approved"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
            ("disputed", "Disputed"),
        ],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        copy=False, help="The current step of this record in its operational or approval lifecycle.",
    )
    is_locked = fields.Boolean(string="Locked", default=False, tracking=True, help="Enable or activate this option to apply 'locked' status to the record.")
    dispute_reason = fields.Text(string="Dispute Reason", help="Specify the description or text value representing 'dispute reason'.")
    dispute_resolved_by = fields.Many2one("res.users", string="Dispute Resolved By", readonly=True, help="Link this transaction or record to the corresponding 'dispute resolved by' reference.")
    dispute_resolved_date = fields.Datetime(string="Dispute Resolved Date", readonly=True, help="The date when this transaction, measurement, or event was officially recorded.")

    # -------------------------------------------------------------------------
    # Locations (auto-filled from operation type or picking)
    # -------------------------------------------------------------------------
    source_location_id = fields.Many2one(
        "stock.location",
        string="Source Location",
        required=True,
        tracking=True,
        help="Location from which the product is physically being transferred. "
             "Auto-filled from the operation type or linked stock transfer.",
    )
    destination_location_id = fields.Many2one(
        "stock.location",
        string="Destination Location",
        required=True,
        tracking=True,
        help="Location to which the product is being physically transferred. "
             "Auto-filled from the operation type or linked stock transfer.",
    )

    # -------------------------------------------------------------------------
    # Ownership fields
    # -------------------------------------------------------------------------
    owner_partner_id = fields.Many2one(
        "res.partner", string="Legal Owner", tracking=True,
        help="The party that legally owns the product during this transfer. "
             "Not set for internal or manufacturing operations.",
    )
    custodian_partner_id = fields.Many2one(
        "res.partner", string="Custodian", tracking=True,
        help="The party physically holding the product. "
             "May differ from the legal owner during transit.",
    )
    operator_partner_id = fields.Many2one(
        "res.partner", string="Operator", tracking=True,
        help="The party operating the facility, pipeline, or vessel.",
    )
    carrier_partner_id = fields.Many2one(
        "res.partner", string="Carrier", tracking=True,
        help="The transport company or driver responsible for the physical movement. "
             "Auto-filled from the Driver field on the linked stock transfer.",
    )

    # -------------------------------------------------------------------------
    # Approval tracking
    # -------------------------------------------------------------------------
    first_approver_id = fields.Many2one("res.users", string="First Approver", readonly=True, copy=False, help="Link this transaction or record to the corresponding 'first approver' reference.")
    first_approval_date = fields.Datetime(string="First Approval Date", readonly=True, copy=False, help="The date when this transaction, measurement, or event was officially recorded.")
    second_approver_id = fields.Many2one("res.users", string="Second Approver", readonly=True, copy=False, help="Link this transaction or record to the corresponding 'second approver' reference.")
    second_approval_date = fields.Datetime(string="Second Approval Date", readonly=True, copy=False, help="The date when this transaction, measurement, or event was officially recorded.")
    completed_by = fields.Many2one("res.users", string="Completed By", readonly=True, copy=False, help="Link this transaction or record to the corresponding 'completed by' reference.")
    completed_date = fields.Datetime(string="Completion Date", readonly=True, copy=False, help="The date when this transaction, measurement, or event was officially recorded.")

    # -------------------------------------------------------------------------
    # Linked documents
    # -------------------------------------------------------------------------
    picking_id = fields.Many2one(
        "stock.picking",
        string="Stock Transfer",
        copy=False,
        tracking=True,
        help="Linked stock picking. Use 'Update from Transfer' to populate "
             "fields automatically from this picking.",
    )
    gate_pass_id = fields.Many2one("oil.gate.pass", string="Gate Pass", copy=False, help="Link this transaction or record to the corresponding 'gate pass' reference.")
    contract_id = fields.Many2one("oil.contract", string="Contract", help="Link this transaction or record to the corresponding 'contract' reference.")
    nomination_id = fields.Many2one(
        "oil.pipeline.nomination",
        string="Pipeline Nomination",
        readonly=True,
        help="Linked Pipeline Nomination if this transfer was created from a pipeline stock picking.",
    )
    account_move_ids = fields.Many2many(
        "account.move",
        "custody_transfer_account_move_rel",
        "transfer_id", "move_id",
        string="Journal Entries",
        copy=False, help="Link this transaction or record to the corresponding 'journal entries' reference.",
    )
    account_move_count = fields.Integer(compute="_compute_account_move_count", help="Specify the numerical measurement, volume, or financial amount for 'account move count'.")

    # -------------------------------------------------------------------------
    # Lines, parties, events
    # -------------------------------------------------------------------------
    line_ids = fields.One2many("custody.transfer.line", "transfer_id", string="Transfer Lines", copy=True, help="Link this transaction or record to the corresponding 'transfer lines' reference.")
    party_ids = fields.One2many("custody.transfer.party", "transfer_id", string="Parties", copy=False, help="Link this transaction or record to the corresponding 'parties' reference.")
    event_ids = fields.One2many("custody.transfer.event", "transfer_id", string="Audit Events", copy=False, help="Link this transaction or record to the corresponding 'audit events' reference.")

    # -------------------------------------------------------------------------
    # Quantity totals
    # -------------------------------------------------------------------------
    total_planned_qty = fields.Monetary(compute="_compute_qty_totals", store=True, string="Total Planned", help="The quantity of product scheduled or expected to be handled in this operation.")
    total_actual_qty = fields.Monetary(compute="_compute_qty_totals", store=True, string="Total Actual", help="The actual measured volume or quantity of product recorded during operations.")
    total_variance_qty = fields.Monetary(compute="_compute_qty_totals", store=True, string="Total Variance", help="The calculated difference between the actual measured quantity and the planned quantity.")

    # -------------------------------------------------------------------------
    # Compute methods
    # -------------------------------------------------------------------------
    @api.depends("line_ids.planned_qty", "line_ids.actual_qty",
                 "line_ids.variance_qty")
    def _compute_qty_totals(self):
        """Calculates and updates the 'totals' value automatically based on related operational inputs."""
        for t in self:
            t.total_planned_qty = sum(t.line_ids.mapped("planned_qty"))
            t.total_actual_qty = sum(t.line_ids.mapped("actual_qty"))
            t.total_variance_qty = sum(t.line_ids.mapped("variance_qty"))

    @api.depends('demurrage_hours', 'demurrage_rate')
    def _compute_demurrage_cost(self):
        """Calculates and updates the 'cost' value automatically based on related operational inputs."""
        for rec in self:
            rec.demurrage_cost = rec.demurrage_hours * rec.demurrage_rate

    def _compute_account_move_count(self):
        """Calculates and updates the 'move count' value automatically based on related operational inputs."""
        for t in self:
            t.account_move_count = len(t.account_move_ids)

    # -------------------------------------------------------------------------
    # Onchange
    # -------------------------------------------------------------------------
    @api.onchange("picking_type_id")
    def _onchange_picking_type_id(self):
        """Auto-fill source/destination from the operation type defaults."""
        if self.picking_type_id:
            if not self.source_location_id:
                self.source_location_id = self.picking_type_id.default_location_src_id
            if not self.destination_location_id:
                self.destination_location_id = self.picking_type_id.default_location_dest_id

    @api.onchange("measurement_method", "source_location_id", "picking_type_id")
    def _onchange_scada_auto_populate(self):
        """Auto-populate temperature and pressure from SCADA on all lines.

        After the HPM merge, everything is stored in °F / psi natively, so
        SCADA values pass through without unit conversion.
        """
        if not self._is_scada_installed():
            return
        for rec in self:
            if rec.measurement_method == 'auto':
                if rec.picking_type_id and rec.picking_type_id.code == 'incoming':
                    continue
                location = rec.source_location_id
                if location:
                    location_db = rec.env["stock.location"].browse(location._origin.id or location.id)
                    if location_db.is_storage_tank:
                        temp_f = location_db.current_temperature_f or 0.0
                        pressure = location_db.current_pressure or 0.0
                        for line in rec.line_ids:
                            line.hpm_observed_temperature = temp_f
                            line.hpm_observed_pressure = pressure

    # -------------------------------------------------------------------------
    # ORM overrides
    # -------------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Registers a new record in the system, validating and pre-populating standard operational defaults."""
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code("custody.transfer") or _("New")
        records = super().create(vals_list)
        for rec in records:
            rec._log_event("create", _("Custody transfer created."))
        return records

    def write(self, vals):
        """Updates the current record's details, performing sanity checks on the modified fields."""
        old_states = {r.id: r.state for r in self}
        result = super().write(vals)
        if "state" in vals:
            state_labels = dict(self._fields["state"].selection)
            for rec in self:
                old = old_states.get(rec.id, "")
                if old != rec.state:
                    rec._log_event(
                        "state_change",
                        _("Status changed from %(old)s to %(new)s.",
                          old=state_labels.get(old, old),
                          new=state_labels.get(rec.state, rec.state)),
                        old_value=old, new_value=rec.state,
                    )
        return result

    # -------------------------------------------------------------------------
    # Wizard measurement defaults
    # -------------------------------------------------------------------------
    def _get_wizard_measurement_defaults(self):
        """Return averaged measurement values from CT lines for pre-populating
        the delivery validation wizard.

        Note on field-name mapping:
        CT lines store HPM fields (`hpm_observed_temperature`, etc.) in °F/psi.
        The base wizard in oil_erp_transfers expects its own field names
        (`temperature`, `pressure`, `api_gravity`, `density_at_15c`,
        `bsw_percent`, `sulfur_content`) — we map ours onto its names here.
        """
        self.ensure_one()
        lines = self.line_ids

        def avg(field_name):
            """Executes the 'avg' process within the operational workflow."""
            vals = [getattr(l, field_name) for l in lines if getattr(l, field_name)]
            return round(sum(vals) / len(vals), 6) if vals else 0.0

        return {
            "temperature": avg("hpm_observed_temperature"),
            "pressure": avg("hpm_observed_pressure"),
            "api_gravity": avg("hpm_observed_api_gravity"),
            "density_at_15c": avg("hpm_density_at_15c"),
            "bsw_percent": avg("hpm_water_content"),
            "sulfur_content": avg("hpm_sulfur_content"),
        }

    # -------------------------------------------------------------------------
    # Workflow actions
    # -------------------------------------------------------------------------
    def action_approve(self):
        """Triggers the transition of the record to proceed with the 'approve' step in the workflow."""
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft transfers can be approved."))
        if not self.line_ids:
            raise UserError(_("Cannot approve a transfer with no product lines."))
        now = fields.Datetime.now()
        vals = {"first_approver_id": self.env.user.id, "first_approval_date": now}
        if self.approval_policy == "dual" and not self.second_approver_id:
            self.write(vals)
            self._log_event("approval", _("First approval granted by %s.", self.env.user.name))
            self.message_post(body=_("First approval granted. Awaiting second approver."), message_type="notification")
        else:
            vals["state"] = "approved"
            self.write(vals)
            self._log_event("approval", _("Transfer approved by %s.", self.env.user.name))
            self._update_stock_picking_quantities()

    def action_second_approve(self):
        """Triggers the transition of the record to proceed with the 'second approve' step in the workflow."""
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft transfers can receive a second approval."))
        if not self.first_approver_id:
            raise UserError(_("First approval must be granted before the second."))
        if self.approval_policy != "dual":
            raise UserError(_("This transfer does not require a second approval."))
        if self.second_approver_id:
            raise UserError(_("Second approval has already been granted."))
        if self.env.user == self.first_approver_id:
            raise UserError(_("The second approver must be a different user from the first."))
        self.write({
            "second_approver_id": self.env.user.id,
            "second_approval_date": fields.Datetime.now(),
            "state": "approved",
        })
        self._log_event("approval", _("Second approval granted by %s.", self.env.user.name))
        self._update_stock_picking_quantities()

    # def _update_stock_picking_quantities(self):
    #     """Update the quantity field on the linked stock.picking (the stock.move records)
    #     with the actual quantity needed to match the demand (planned_qty) from the CT form,
    #     and also update the line's actual_qty to match it so they are aligned."""
    #     self.ensure_one()
    #     if not self.picking_id:
    #         return
    #     for line in self.line_ids:
    #         moves = self.picking_id.move_ids.filtered(
    #             lambda m: m.product_id == line.product_id and m.state not in ('cancel', 'done')
    #         )
    #         qty_needed = line.hpm_required_actual_qty or line.planned_qty
    #         if moves:
    #             moves.write({'quantity': qty_needed})
    #         # Also update the actual_qty on the custody transfer line to be the qty_needed
    #         line.write({'actual_qty': qty_needed})

    def _update_stock_picking_quantities(self):
        """
        Push the gross (raw observed) quantity required to deliver the
        contracted Net Standard Volume back to the linked picking.

        Both demand (product_uom_qty) and done qty (quantity) are set to the
        same UoM-rounded gross value so the picking is in perfect balance —
        no Check Availability mismatch, no back-order on validation. The
        commercial (net) demand is preserved on the CT line as planned_qty.
        """
        self.ensure_one()
        if not self.picking_id:
            return

        picking = self.picking_id.with_context(bypass_reservation_update=True)

        for line in self.line_ids:
            moves = picking.move_ids.filtered(
                lambda m: m.product_id == line.product_id
                          and m.state not in ("cancel", "done")
            )
            if not moves:
                continue
            raw_qty = line.hpm_required_actual_qty or line.planned_qty
            qty_needed = line.product_uom_id.round(raw_qty)
            moves.write({
                "product_uom_qty": qty_needed,
                "quantity": qty_needed,
            })

            line.write({"actual_qty": qty_needed})
        picking.move_ids.filtered(lambda m: m.state == "assigned")._action_assign()

    def action_start(self):
        """Triggers the transition of the record to proceed with the 'start' step in the workflow."""
        self.ensure_one()
        if self.state != "approved":
            raise UserError(_("Only approved transfers can be started."))
        self.write({"state": "in_progress"})

    def action_complete(self):
        """Triggers the transition of the record to proceed with the 'complete' step in the workflow."""
        self.ensure_one()
        if self.state not in ("approved", "in_progress"):
            raise UserError(_("Only approved or in-progress transfers can be completed."))
        now = fields.Datetime.now()
        self.write({
            "state": "completed",
            "is_locked": True,
            "completed_by": self.env.user.id,
            "completed_date": now,
        })
        self._log_event("state_change", _("Transfer completed by %s.", self.env.user.name))

    def action_cancel(self):
        """Triggers the transition of the record to proceed with the 'cancel' step in the workflow."""
        self.ensure_one()
        if self.state == "completed":
            raise UserError(_("Completed transfers cannot be cancelled."))
        if self.state == "cancelled":
            raise UserError(_("Already cancelled."))
        self.write({"state": "cancelled"})
        self._log_event("state_change", _("Transfer cancelled by %s.", self.env.user.name))

    def action_reset_draft(self):
        """Triggers the transition of the record to proceed with the 'reset draft' step in the workflow."""
        self.ensure_one()
        if self.state not in ("cancelled", "disputed"):
            raise UserError(_("Only cancelled or disputed transfers can be reset to draft."))
        self.write({
            "state": "draft",
            "first_approver_id": False,
            "first_approval_date": False,
            "second_approver_id": False,
            "second_approval_date": False,
            "is_locked": False,
        })
        self._log_event("state_change", _("Transfer reset to draft by %s.", self.env.user.name))

    def action_dispute(self):
        """Triggers the transition of the record to proceed with the 'dispute' step in the workflow."""
        self.ensure_one()
        if self.state not in ("approved", "in_progress", "completed"):
            raise UserError(_("Only active or completed transfers can be disputed."))
        self.write({"state": "disputed"})
        self._log_event("dispute", _("Transfer disputed by %s.", self.env.user.name))

    def action_resolve_dispute(self):
        """Triggers the transition of the record to proceed with the 'resolve dispute' step in the workflow."""
        self.ensure_one()
        if self.state != "disputed":
            raise UserError(_("This transfer is not currently disputed."))
        self.write({
            "state": "completed",
            "is_locked": True,
            "dispute_resolved_by": self.env.user.id,
            "dispute_resolved_date": fields.Datetime.now(),
        })
        self._log_event("dispute_resolved", _("Dispute resolved by %s.", self.env.user.name))

    # -------------------------------------------------------------------------
    # Smart button actions
    # -------------------------------------------------------------------------
    def action_view_picking(self):
        """Triggers the transition of the record to proceed with the 'view picking' step in the workflow."""
        self.ensure_one()
        if not self.picking_id:
            return False
        return {
            "type": "ir.actions.act_window",
            "name": _("Stock Transfer"),
            "res_model": "stock.picking",
            "res_id": self.picking_id.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_view_gate_pass(self):
        """Triggers the transition of the record to proceed with the 'view gate pass' step in the workflow."""
        self.ensure_one()
        if not self.gate_pass_id:
            return False
        return {
            "type": "ir.actions.act_window",
            "name": _("Gate Pass"),
            "res_model": "oil.gate.pass",
            "res_id": self.gate_pass_id.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_view_account_moves(self):
        """Triggers the transition of the record to proceed with the 'view account moves' step in the workflow."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Journal Entries"),
            "res_model": "account.move",
            "domain": [("id", "in", self.account_move_ids.ids)],
            "view_mode": "list,form",
            "target": "current",
        }

    # -------------------------------------------------------------------------
    # Accounting
    # -------------------------------------------------------------------------
    def _create_accounting_entries(self):
        """Executes the 'create accounting entries' process within the operational workflow."""
        self.ensure_one()
        journal = self.env["account.journal"].search(
            [("type", "=", "general"), ("company_id", "=", self.company_id.id)], limit=1
        )
        if not journal:
            self.message_post(body=_("No General journal found. Accounting entry skipped."), message_type="notification")
            return
        move = self.env["account.move"].create({
            "move_type": "entry",
            "date": self.completed_date or fields.Date.today(),
            "ref": _("Custody Transfer: %s", self.name),
            "company_id": self.company_id.id,
            "journal_id": journal.id,
            "line_ids": [],
        })
        self.account_move_ids = [(4, move.id)]
        self._log_event("note", _("Journal entry %s created.", move.name))

    # -------------------------------------------------------------------------
    # Audit log
    # -------------------------------------------------------------------------
    def _log_event(self, event_type, description, old_value=None, new_value=None):
        """Executes the 'log event' process within the operational workflow."""
        self.ensure_one()
        self.env["custody.transfer.event"].create({
            "transfer_id": self.id,
            "event_type": event_type,
            "event_date": fields.Datetime.now(),
            "user_id": self.env.user.id,
            "description": description,
            "old_value": old_value,
            "new_value": new_value,
        })

    # -------------------------------------------------------------------------
    # Constraints
    # -------------------------------------------------------------------------
    @api.constrains("source_location_id", "destination_location_id")
    def _check_locations(self):
        """Enforces validation rules to ensure '' meets required safety and regulatory standards."""
        for t in self:
            if t.source_location_id == t.destination_location_id:
                raise ValidationError(_("Source and destination locations must be different."))

    @api.constrains("api_gravity_loading", "api_gravity_arrival")
    def _check_api_gravity(self):
        """Enforces validation rules to ensure 'gravity' meets required safety and regulatory standards."""
        for t in self:
            if t.api_gravity_loading and t.api_gravity_loading < 0:
                raise ValidationError(_("API gravity loading cannot be negative."))
            if t.api_gravity_arrival and t.api_gravity_arrival < 0:
                raise ValidationError(_("API gravity arrival cannot be negative."))
