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
#############################################################################
import logging

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)


class OilAroObligation(models.Model):
    """
    Asset Retirement Obligation — simplified 5-state lifecycle.

    Workflow:
        draft       → Initial estimate, not yet posted to GL
        recognized  → Posted to GL, accretion running automatically
        executing   → Decommissioning work underway, WIP accumulating
        settled     → Final settlement posted, GL cleared, gain/loss booked
        closed      → No further activity
        cancelled   → GL reversed
    """
    _name = 'oil.aro.obligation'
    _description = 'Asset Retirement Obligation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'
    _rec_name = 'name'

    # ── IDENTIFICATION ──────────────────────────────────────────────
    name = fields.Char(
        string='Reference', required=True, copy=False,
        readonly=True, default=lambda self: _('New'), tracking=True, help="A unique name or reference identifier used to track this record in the system.")
    description = fields.Text(string='Description', tracking=True, help="Additional comments, details, or operational remarks about this record.")

    asset_kind = fields.Selection([('reservoir', 'Reservoir / Well'), ('lease', 'Lease'),
                                   ('equipment', 'Equipment / Facility'), ('pipeline', 'Pipeline')], string='Asset Kind', required=True,
                                  tracking=True, help="Select the appropriate classification or category for 'asset kind'.")
    reservoir_id = fields.Many2one('oil.reservoir', string='Reservoir / Well', tracking=True, help="The geological reservoir or oil/gas well source associated with this production.")
    lease_id = fields.Many2one('oil.lease.agreement', string='Lease', tracking=True, help="The contract agreement details governing mineral rights and operations on this tract of land.")
    equipment_id = fields.Many2one('maintenance.equipment', string='Equipment', tracking=True, help="The equipment asset or machinery associated with this operational task.")
    pipeline_id = fields.Many2one('delivery.carrier', string='Pipeline', tracking=True, help="Link this transaction or record to the corresponding 'pipeline' reference.")

    # ── RESPONSIBLE & PROJECT LINKS ─────────────────────────────────
    responsible_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user, tracking=True, help="The employee, operator, or coordinator responsible for managing this record.")
    decommissioning_plan_id = fields.Many2one('project.project', string='Decommissioning Project', tracking=True, help="Link this transaction or record to the corresponding 'decommissioning project' reference.")
    environmental_obligation_type = fields.Selection([('regulatory', 'Regulatory'),('voluntary', 'Voluntary')],
                                                     string='Environmental Obligation Type', default='regulatory',
                                                     tracking=True, help="Select the appropriate classification or category for 'environmental obligation type'.")

    # ── FINANCIAL PARAMETERS ────────────────────────────────────────
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.company.currency_id, tracking=True, help="Link this transaction or record to the corresponding 'currency' reference.")
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company, help="The company managing this operational record or transaction.")

    current_cost = fields.Monetary(string='Current Cost (Real)', currency_field='currency_id', tracking=True, help="The unit rate or total financial cost applied to this transaction.")
    inflation_rate = fields.Float(string='Inflation Rate (%)', default=2.0, tracking=True, help="Specify the numerical measurement, volume, or financial amount for 'inflation rate (%)'.")

    future_cost = fields.Monetary(string='Future Cost (Nominal)', currency_field='currency_id',
                                  tracking=True, help='Engineering estimate of the future decommissioning cost.',
                                  compute='_compute_future_cost', store=True)
    discount_rate = fields.Float(string='Discount Rate (%)', digits=(6, 4), default=6.0,
                                 tracking=True, help='Credit-adjusted risk-free rate per IAS 37.')
    recognition_date = fields.Date(string='Recognition Date', tracking=True, default=fields.Date.context_today, help="The date when this transaction, measurement, or event was officially recorded.")
    abandonment_date = fields.Date(string='Estimated Abandonment Date', tracking=True, help="The date when this transaction, measurement, or event was officially recorded.")

    years_to_abandonment = fields.Float(string='Years to Abandonment', compute='_compute_years_to_abandonment',
                                        store=True, help="Specify the numerical measurement, volume, or financial amount for 'years to abandonment'.")
    priority_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], string='Priority Level', compute='_compute_priority_level', store=True, help="Select the appropriate classification or category for 'priority level'.")

    # ── RUNNING BALANCES (set by accounting logic) ──────────────────
    initial_pv = fields.Monetary(string='Initial PV', currency_field='currency_id', readonly=True, tracking=True, help="Specify the numerical measurement, volume, or financial amount for 'initial pv'.")
    current_liability_balance = fields.Monetary(string='Current Liability Balance', currency_field='currency_id',
                                                readonly=True, tracking=True, help="Specify the numerical measurement, volume, or financial amount for 'current liability balance'.")
    accreted_to_date = fields.Monetary(string='Cumulative Accretion', currency_field='currency_id', readonly=True, help="The date when this transaction, measurement, or event was officially recorded.")
    last_accretion_date = fields.Date(string='Last Accretion Posted', readonly=True, help="The date when this transaction, measurement, or event was officially recorded.")
    accretion_frequency = fields.Selection([('monthly', 'Monthly'), ('quarterly', 'Quarterly'),
                                            ('annual', 'Annual'), ], string='Accretion Frequency', default='quarterly',
                                           tracking=True, help="Select the appropriate classification or category for 'accretion frequency'.")

    # ── ACCOUNTING ──────────────────────────────────────────────────
    aro_asset_account_id = fields.Many2one('account.account', string='ARO Asset Account', required=True,
                                           domain="[('account_type', '=', 'asset_non_current')]",
                                           help='Account debited at recognition (capitalized ARO asset).')
    liability_account_id = fields.Many2one('account.account', string='ARO Liability Account',
                                           required=True, domain="[('account_type', '=', 'liability_non_current')]",
                                           help="Link this transaction or record to the corresponding 'aro liability account' reference.")
    accretion_expense_account_id = fields.Many2one('account.account', string='Accretion Expense Account',
                                                   required=True, domain="[('account_type', '=', 'expense')]",
                                                   help="Link this transaction or record to the corresponding 'accretion expense account' reference.")
    wip_account_id = fields.Many2one('account.account', string='Decom WIP Account', required=True,
                                     domain="[('account_type', '=', 'asset_current')]",
                                     help="Link this transaction or record to the corresponding 'decom wip account' reference.")
    settlement_gain_account_id = fields.Many2one('account.account', string='Settlement Gain Account',
                                                 domain="[('account_type', '=', 'income_other')]",
                                                 help="Link this transaction or record to the corresponding 'settlement gain account' reference.")
    settlement_loss_account_id = fields.Many2one('account.account', string='Settlement Loss Account',
                                                 domain="[('account_type', '=', 'expense')]",
                                                 help="Link this transaction or record to the corresponding 'settlement loss account' reference.")
    deferred_tax_asset_account_id = fields.Many2one('account.account', string='Deferred Tax Asset ARO Account',
                                                    domain="[('account_type', '=', 'asset_non_current')]",
                                                    help="Deferred tax asset account for ARO.")
    deferred_tax_benefit_account_id = fields.Many2one('account.account', string='Deferred Tax Benefit Account',
                                                      domain="[('account_type', '=', 'expense')]",
                                                      help="Deferred tax benefit account for ARO.")
    journal_id = fields.Many2one('account.journal', string='ARO Journal', required=True,
                                 domain=[('type', '=', 'general')], help="Link this transaction or record to the corresponding 'aro journal' reference.")
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', help="Link this transaction or record to the corresponding 'analytic account' reference.")
    cost_center_id = fields.Many2one('account.analytic.account', string='Cost Center', tracking=True, help="The unit rate or total financial cost applied to this transaction.")
    # GL links (for reversal on cancel)
    initial_move_id = fields.Many2one('account.move', string='Initial Recognition Journal', readonly=True,
                                      copy=False, help="Link this transaction or record to the corresponding 'initial recognition journal' reference.")

    # Joint Venture (JOA) Link
    jv_agreement_id = fields.Many2one('oil.jv.agreement', string='JOA / JV Agreement', tracking=True, help="Link this transaction or record to the corresponding 'joa / jv agreement' reference.")
    partner_share_ids = fields.One2many('oil.aro.partner.share', 'obligation_id', string='JV Partner Shares', help="Link this transaction or record to the corresponding 'jv partner shares' reference.")

    # Settlement summary (stored on obligation at settlement time)
    settlement_date = fields.Date(string='Settlement Date', readonly=True, copy=False, help="The date when this transaction, measurement, or event was officially recorded.")
    settlement_salvage = fields.Monetary(string='Salvage Revenue', currency_field='currency_id', readonly=True,
                                         copy=False, help="Specify the numerical measurement, volume, or financial amount for 'salvage revenue'.")
    settlement_move_id = fields.Many2one('account.move', string='Settlement Journal', readonly=True,
                                         copy=False, help="Link this transaction or record to the corresponding 'settlement journal' reference.")
    settlement_notes = fields.Text(string='Settlement Notes', readonly=True, copy=False, help="Additional comments, details, or operational remarks about this record.")

    # ── RELATED LINES ───────────────────────────────────────────────
    accretion_line_ids = fields.One2many('oil.aro.accretion.line', 'obligation_id', string='Accretion Schedule', help="Link this transaction or record to the corresponding 'accretion schedule' reference.")
    revision_ids = fields.One2many('oil.aro.revision', 'obligation_id', string='Revisions', help="Link this transaction or record to the corresponding 'revisions' reference.")
    wip_line_ids = fields.One2many('oil.aro.wip', 'obligation_id', string='Decom WIP', help="Link this transaction or record to the corresponding 'decom wip' reference.")

    # ── COMPUTED ROLL-UPS ───────────────────────────────────────────
    wip_total = fields.Monetary(string='Total WIP', currency_field='currency_id', compute='_compute_wip_total',
                                store=True, help="Specify the numerical measurement, volume, or financial amount for 'total wip'.")
    net_decom_cost = fields.Monetary(string='Net Decom Cost', currency_field='currency_id',
                                     compute='_compute_net_decom_cost', store=True,
                                     help='WIP total minus salvage revenue.')
    settlement_variance = fields.Monetary(string='Settlement Variance (Gain +ve)', currency_field='currency_id',
                                          compute='_compute_settlement_variance', store=True,
                                          help='Positive = gain (over-provisioned), Negative = loss.')

    # ── STATE ───────────────────────────────────────────────────────
    state = fields.Selection([('draft', 'Draft'), ('recognized', 'Recognized'), ('hold', 'Hold'), ('executing', 'Executing'),
                              ('settled', 'Settled'), ('closed', 'Closed'), ('cancelled', 'Cancelled'), ],
                             string='Status', default='draft', tracking=True, help="The current step of this record in its operational or approval lifecycle.")
    previous_state = fields.Selection([
        ('recognized', 'Recognized'),
        ('executing', 'Executing')
    ], string='Previous State', help="The current step of this record in its operational or approval lifecycle.")

    # ---------------------------------------------------------
    # SMART BUTTON COUNTS
    # ---------------------------------------------------------

    wip_count = fields.Integer(string='WIP Count', compute='_compute_counts', help="Specify the numerical measurement, volume, or financial amount for 'wip count'.", )
    accretion_count = fields.Integer(string='Accretion Count', compute='_compute_counts', help="Specify the numerical measurement, volume, or financial amount for 'accretion count'.", )
    revision_count = fields.Integer(string='Revision Count', compute='_compute_counts', help="Specify the numerical measurement, volume, or financial amount for 'revision count'.", )
    journal_count = fields.Integer(string='Journal Count', compute='_compute_counts', help="Specify the numerical measurement, volume, or financial amount for 'journal count'.", )
    template_id = fields.Many2one('oil.aro.template', string='ARO Template', help="Link this transaction or record to the corresponding 'aro template' reference.", )

    incident_count = fields.Integer(string='Incident Count', compute='_compute_incident_count', help="Specify the numerical measurement, volume, or financial amount for 'incident count'.")
    hse_incident_ids = fields.One2many('oil.hse.incident', 'aro_obligation_id', string='HSE Incidents', help="Health, Safety, and Environment incident record linked to this activity.")

    @api.depends('hse_incident_ids')
    def _compute_incident_count(self):
        """Calculates and updates the 'count' value automatically based on related operational inputs."""
        for rec in self:
            rec.incident_count = len(rec.hse_incident_ids)

    # ── COMPUTES ────────────────────────────────────────────────────
    @api.depends('current_cost', 'inflation_rate', 'years_to_abandonment')
    def _compute_future_cost(self):

        """Calculates and updates the 'cost' value automatically based on related operational inputs."""
        for rec in self:
            if rec.current_cost:
                rec.future_cost = rec.current_cost * ((1.0 + rec.inflation_rate / 100.0) ** rec.years_to_abandonment)

    @api.depends('abandonment_date', 'state')
    def _compute_priority_level(self):
        """Calculates and updates the 'level' value automatically based on related operational inputs."""
        today = fields.Date.context_today(self)
        for rec in self:
            if rec.state in ('settled', 'closed', 'cancelled') or not rec.abandonment_date:
                rec.priority_level = 'low'
                continue
            delta = rec.abandonment_date - today
            days = delta.days
            if days <= 90:
                rec.priority_level = 'critical'
            elif days <= 365:
                rec.priority_level = 'high'
            elif days <= 1095:
                rec.priority_level = 'medium'
            else:
                rec.priority_level = 'low'

    @api.depends('recognition_date', 'abandonment_date')
    def _compute_years_to_abandonment(self):
        """Calculates and updates the 'to abandonment' value automatically based on related operational inputs."""
        for rec in self:
            if rec.recognition_date and rec.abandonment_date:
                delta = rec.abandonment_date - rec.recognition_date
                rec.years_to_abandonment = round(delta.days / 365.25, 4)
            else:
                rec.years_to_abandonment = 0.0

    @api.depends('wip_line_ids.amount', 'wip_line_ids.currency_id', 'wip_line_ids.state', 'currency_id')
    def _compute_wip_total(self):
        """Calculates and updates the 'total' value automatically based on related operational inputs."""
        for rec in self:
            total = 0.0
            for line in rec.wip_line_ids:
                if line.state != 'posted':
                    continue
                if line.currency_id and line.currency_id != rec.currency_id:
                    total += line.currency_id._convert(
                        line.amount, rec.currency_id, rec.company_id or self.env.company, line.date or fields.Date.context_today(self)
                    )
                else:
                    total += line.amount
            rec.wip_total = total

    @api.depends('wip_total', 'settlement_salvage')
    def _compute_net_decom_cost(self):
        """Calculates and updates the 'decom cost' value automatically based on related operational inputs."""
        for rec in self:
            rec.net_decom_cost = rec.wip_total - (rec.settlement_salvage or 0.0)

    @api.depends('current_liability_balance', 'net_decom_cost', 'state')
    def _compute_settlement_variance(self):
        """Calculates and updates the 'variance' value automatically based on related operational inputs."""
        for rec in self:
            if rec.state in ('settled', 'closed'):
                rec.settlement_variance = (
                        rec.current_liability_balance - rec.net_decom_cost)
            else:
                rec.settlement_variance = 0.0

    @api.constrains('discount_rate', 'future_cost', 'recognition_date', 'abandonment_date')
    def _check_financial_parameters(self):
        """Enforces validation rules to ensure 'parameters' meets required safety and regulatory standards."""
        for rec in self:
            if rec.discount_rate <= 0.0 or rec.discount_rate >= 100.0:
                raise ValidationError(_("Discount rate must be between 0 and 100."))
            if rec.future_cost and rec.future_cost <= 0.0:
                raise ValidationError(_("Future cost must be greater than 0."))
            if (rec.recognition_date and rec.abandonment_date
                    and rec.recognition_date >= rec.abandonment_date):
                raise ValidationError(
                    _("Recognition date must be earlier than abandonment date."))

    # ---------------------------------------------------------
    # COMPUTE COUNTS
    # ---------------------------------------------------------

    def _compute_counts(self):
        """Calculates and updates the '' value automatically based on related operational inputs."""
        for rec in self:
            rec.wip_count = len(rec.wip_line_ids)

            rec.accretion_count = len(rec.accretion_line_ids)

            rec.revision_count = len(rec.revision_ids)

            moves = (
                    rec.initial_move_id
                    | rec.settlement_move_id
                    | rec.accretion_line_ids.mapped('move_id')
                    | rec.revision_ids.mapped('move_id')
                    | rec.wip_line_ids.mapped('move_id')
            )

            rec.journal_count = len(moves)

    @api.onchange('template_id')
    def _onchange_template_id(self):

        """Refreshes UI fields and updates default values dynamically when the user modifies the 'id' field."""
        for rec in self:
            template = rec.template_id
            if not template:
                continue

            rec.aro_asset_account_id = (template.aro_asset_account_id)
            rec.liability_account_id = (template.liability_account_id)
            rec.accretion_expense_account_id = (template.accretion_expense_account_id)
            rec.wip_account_id = (template.wip_account_id)
            rec.settlement_gain_account_id = (template.settlement_gain_account_id)
            rec.settlement_loss_account_id = (template.settlement_loss_account_id)
            rec.deferred_tax_asset_account_id = (template.deferred_tax_asset_account_id)
            rec.deferred_tax_benefit_account_id = (template.deferred_tax_benefit_account_id)
            rec.journal_id = (template.journal_id)
            rec.discount_rate = (template.discount_rate)
            rec.accretion_frequency = (template.accretion_frequency)

    # ── SEQUENCE & JV INTEGRATION ────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        """Registers a new record in the system, validating and pre-populating standard operational defaults."""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'oil.aro.obligation') or _('New')
        records = super().create(vals_list)
        for rec in records:
            if rec.jv_agreement_id:
                for partner in rec.jv_agreement_id.partner_ids:
                    self.env['oil.aro.partner.share'].create({
                        'obligation_id': rec.id,
                        'partner_id': partner.partner_id.id,
                        'working_interest': partner.working_interest,
                    })
        return records

    def write(self, vals):
        """Updates the current record's details, performing sanity checks on the modified fields."""
        res = super().write(vals)
        if 'jv_agreement_id' in vals:
            for rec in self:
                rec.partner_share_ids.unlink()
                if rec.jv_agreement_id:
                    for partner in rec.jv_agreement_id.partner_ids:
                        self.env['oil.aro.partner.share'].create({
                            'obligation_id': rec.id,
                            'partner_id': partner.partner_id.id,
                            'working_interest': partner.working_interest,
                        })
        return res

    # ── PV CALCULATION ──────────────────────────────────────────────
    def _calculate_pv(self, future_cost=None, discount_rate=None, years=None):
        """PV = FV / (1 + r)^n  (IAS 37 present value)"""
        self.ensure_one()
        fv = future_cost if future_cost is not None else self.future_cost
        r = (discount_rate if discount_rate is not None
             else self.discount_rate) / 100.0
        n = years if years is not None else self.years_to_abandonment
        if n <= 0:
            return fv
        return fv / ((1 + r) ** n)

    # ── WORKFLOW ACTIONS ─────────────────────────────────────────────
    def action_recognize(self):
        """Post the initial ARO journal: Dr ARO Asset Account / Cr ARO Liability."""
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Only draft ARO records can be recognized.'))
            if not rec.future_cost or rec.future_cost <= 0:
                raise UserError(_('Future cost must be positive.'))
            if not rec.abandonment_date or not rec.recognition_date:
                raise UserError(_('Recognition and abandonment dates are required.'))
            if rec.abandonment_date <= rec.recognition_date:
                raise UserError(_('Abandonment date must be after recognition date.'))

            pv = rec._calculate_pv()
            rec.initial_pv = pv
            rec.current_liability_balance = pv

            analytic = ({str(rec.analytic_account_id.id): 100.0} if rec.analytic_account_id else False)

            move = self.env['account.move'].create({
                'journal_id': rec.journal_id.id,
                'date': rec.recognition_date,
                'ref': _('ARO Recognition: %s') % rec.name,
                'move_type': 'entry',
                'line_ids': [
                    (0, 0, {
                        'name': _('ARO Asset capitalization'),
                        'account_id': rec.aro_asset_account_id.id,
                        'debit': pv,
                        'credit': 0.0,
                        'analytic_distribution': analytic,
                    }),
                    (0, 0, {
                        'name': _('ARO Liability recognition'),
                        'account_id': rec.liability_account_id.id,
                        'debit': 0.0,
                        'credit': pv,
                    }),
                ],
            })
            move.action_post()
            rec.initial_move_id = move.id
            rec.last_accretion_date = rec.recognition_date
            rec.state = 'recognized'
            rec.message_post(body=_(
                'ARO recognized. Present Value %(pv)s posted to GL.',
                pv=rec.currency_id.format(pv)))
        return True

    def action_start_executing(self):
        """Move from recognized → executing. Decommissioning work begins."""
        for rec in self:
            if rec.state != 'recognized':
                raise UserError(_('Only recognized ARO can start executing.'))
            rec.state = 'executing'
            rec.message_post(body=_(
                'Decommissioning execution started. Record WIP costs in the WIP tab.'))
            
            # Create a task for the decommissioning team if decommissioning_plan_id is set
            if rec.decommissioning_plan_id:
                self.env['project.task'].create({
                    'name': _('Decommissioning Execution: %s') % rec.name,
                    'project_id': rec.decommissioning_plan_id.id,
                    'description': _('Decommissioning execution started for ARO: %s. Please manage tasks and track WIP costs.') % rec.name,
                    'user_ids': [rec.responsible_id.id] if rec.responsible_id else False,
                })
            
            # Create an activity for the responsible user
            responsible = rec.responsible_id or rec.create_uid or self.env.user
            self.env['mail.activity'].create({
                'res_model_id': self.env['ir.model']._get('oil.aro.obligation').id,
                'res_id': rec.id,
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'summary': _('Decommissioning Execution Started'),
                'note': _('The ARO has entered the Executing state. Please begin work and record WIP costs.'),
                'user_id': responsible.id,
                'date_deadline': fields.Date.context_today(rec),
            })

    def action_hold(self):
        """Triggers the transition of the record to proceed with the 'hold' step in the workflow."""
        for rec in self:
            if rec.state not in ('recognized', 'executing'):
                raise UserError(_("Only recognized or executing AROs can be placed on hold."))
            rec.write({
                'previous_state': rec.state,
                'state': 'hold'
            })
            rec.message_post(body=_("ARO put on hold. Accretion paused."))

    def action_resume(self):
        """Triggers the transition of the record to proceed with the 'resume' step in the workflow."""
        for rec in self:
            if rec.state != 'hold':
                raise UserError(_("Only AROs on hold can be resumed."))
            rec.write({
                'state': rec.previous_state or 'recognized',
                'previous_state': False
            })
            rec.message_post(body=_("ARO resumed. Accretion restarted."))

    def action_open_revision_wizard(self):
        """Open the estimate revision wizard (available when recognized or executing)."""
        self.ensure_one()
        if self.state not in ('recognized', 'executing'):
            raise UserError(
                _('Revisions can only be made on recognized or executing AROs.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Revise ARO Estimate'),
            'res_model': 'oil.aro.revision.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_obligation_id': self.id},
        }

    def action_view_incidents(self):
        """Triggers the transition of the record to proceed with the 'view incidents' step in the workflow."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('HSE Incidents'),
            'res_model': 'oil.hse.incident',
            'view_mode': 'list,form',
            'domain': [('aro_obligation_id', '=', self.id)],
            'context': {'default_aro_obligation_id': self.id},
        }

    def action_open_settlement_wizard(self):
        """Open the settlement wizard from executing state."""
        self.ensure_one()
        if self.state != 'executing':
            raise UserError(_('Only executing ARO can be settled.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Settle ARO'),
            'res_model': 'oil.aro.settlement.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_obligation_id': self.id},
        }

    def action_close(self):
        """Close the ARO — no further activity."""
        for rec in self:
            if rec.state != 'settled':
                raise UserError(_('Only settled ARO can be closed.'))
            rec.state = 'closed'
            rec.message_post(body=_('ARO closed. No further activity.'))

    def action_cancel(self):
        """Cancel with full GL reversal (accretion + initial recognition)."""
        for rec in self:
            if rec.state in ('settled', 'closed'):
                raise UserError(_('Cannot cancel a settled or closed ARO.'))
            today = fields.Date.context_today(rec)

            # 1. Reverse accretion journals newest-first
            for acc_line in rec.accretion_line_ids.sorted(
                    key=lambda l: l.date, reverse=True):
                if acc_line.move_id and acc_line.move_id.state == 'posted':
                    rev = acc_line.move_id._reverse_moves(
                        default_values_list=[{
                            'date': today,
                            'ref': _('Reversal: %s') % acc_line.move_id.ref,
                        }],
                        cancel=True,
                    )
                    if rev and rev[0].state != 'posted':
                        rev[0].action_post()

            # 2. Reverse initial recognition journal
            if rec.initial_move_id and rec.initial_move_id.state == 'posted':
                rev = rec.initial_move_id._reverse_moves(
                    default_values_list=[{
                        'date': today,
                        'ref': _('Cancel ARO: %s') % rec.name,
                    }],
                    cancel=True,
                )
                if rev and rev[0].state != 'posted':
                    rev[0].action_post()

            rec.current_liability_balance = 0.0
            rec.accreted_to_date = 0.0
            rec.state = 'cancelled'
            rec.message_post(body=_(
                'ARO cancelled. All GL journals reversed.'))

    # ── ACCRETION (Effective Interest Method) ────────────────────────
    def post_accretion(self, posting_date=None):
        """Post one period of accretion using Effective Interest Method (IAS 37)."""
        self.ensure_one()
        if self.state not in ('recognized', 'executing'):
            return False

        posting_date = posting_date or fields.Date.context_today(self)

        # Same-period guard
        periods_per_year = {'monthly': 12, 'quarterly': 4, 'annual': 1}[
            self.accretion_frequency]
        min_months = {'monthly': 1, 'quarterly': 3, 'annual': 12}[
            self.accretion_frequency]

        if self.last_accretion_date:
            _d = relativedelta(posting_date, self.last_accretion_date)
            months_since = _d.years * 12 + _d.months
            if months_since < min_months:
                _logger.info(
                    'ARO %s: skipped — %s months since last posting, need %s.',
                    self.name, months_since, min_months)
                return False

        # EIM: accretion = L × ((1+r)^(1/n) − 1)
        r = self.discount_rate / 100.0
        accretion = self.current_liability_balance * (
                (1.0 + r) ** (1.0 / periods_per_year) - 1.0)

        if accretion <= 0:
            return False

        analytic = (
            {str(self.analytic_account_id.id): 100.0}
            if self.analytic_account_id else False)

        move = self.env['account.move'].create({
            'journal_id': self.journal_id.id,
            'date': posting_date,
            'ref': _('ARO Accretion %s') % self.name,
            'move_type': 'entry',
            'line_ids': [
                (0, 0, {
                    'name': _('Accretion expense'),
                    'account_id': self.accretion_expense_account_id.id,
                    'debit': accretion,
                    'credit': 0.0,
                    'analytic_distribution': analytic,
                }),
                (0, 0, {
                    'name': _('ARO liability accretion'),
                    'account_id': self.liability_account_id.id,
                    'debit': 0.0,
                    'credit': accretion,
                }),
            ],
        })
        move.action_post()

        self.env['oil.aro.accretion.line'].create({
            'obligation_id': self.id,
            'date': posting_date,
            'opening_balance': self.current_liability_balance,
            'accretion_amount': accretion,
            'closing_balance': self.current_liability_balance + accretion,
            'move_id': move.id,
        })
        self.current_liability_balance += accretion
        self.accreted_to_date += accretion
        self.last_accretion_date = posting_date
        return True

    def _get_next_accretion_date(self, base_date):
        """Executes the 'get next accretion date' process within the operational workflow."""
        self.ensure_one()
        months = {'monthly': 1, 'quarterly': 3, 'annual': 12}[self.accretion_frequency]
        return base_date + relativedelta(months=months)

    # ── CRON ─────────────────────────────────────────────────────────
    @api.model
    def cron_post_accretion(self):
        """Posts accretion for every active obligation due in the current period, catching up missed ones."""
        today = fields.Date.context_today(self)
        obligations = self.search([
            ('state', 'in', ('recognized', 'executing')),
        ])
        for ob in obligations:
            try:
                with self.env.cr.savepoint():
                    base_date = ob.last_accretion_date or ob.recognition_date
                    if not base_date:
                        continue
                    next_due = ob._get_next_accretion_date(base_date)
                    while next_due <= today:
                        ob.post_accretion(posting_date=next_due)
                        next_due = ob._get_next_accretion_date(next_due)
            except Exception as e:
                _logger.error(
                    'Failed to post accretion for ARO %s: %s', ob.name, str(e))

    @api.model
    def cron_warn_approaching_abandonment(self):
        """Executes the 'cron warn approaching abandonment' process within the operational workflow."""
        today = fields.Date.context_today(self)
        aros = self.search([('state', 'in', ('recognized', 'executing')), ('abandonment_date', '!=', False)])
        for aro in aros:
            delta = aro.abandonment_date - today
            days = delta.days
            warning_message = False
            if 360 <= days <= 365:
                warning_message = _("WARNING: ARO %s is approaching abandonment date in 12 months (on %s).") % (aro.name, aro.abandonment_date)
            elif 175 <= days <= 180:
                warning_message = _("WARNING: ARO %s is approaching abandonment date in 6 months (on %s).") % (aro.name, aro.abandonment_date)
            elif 85 <= days <= 90:
                warning_message = _("WARNING: ARO %s is approaching abandonment date in 3 months (on %s).") % (aro.name, aro.abandonment_date)
            
            if warning_message:
                activity_summary = _("Abandonment Warning - %s") % aro.name
                existing = self.env['mail.activity'].search([
                    ('res_model', '=', 'oil.aro.obligation'),
                    ('res_id', '=', aro.id),
                    ('summary', '=', activity_summary),
                ])
                if not existing:
                    aro.message_post(body=warning_message)
                    responsible = aro.responsible_id or aro.create_uid or self.env.user
                    self.env['mail.activity'].create({
                        'res_model_id': self.env['ir.model']._get('oil.aro.obligation').id,
                        'res_id': aro.id,
                        'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                        'summary': activity_summary,
                        'note': warning_message,
                        'user_id': responsible.id,
                        'date_deadline': today,
                    })

    @api.model
    def cron_equipment_cert_expiry_aro(self):
        """Executes the 'cron equipment cert expiry aro' process within the operational workflow."""
        today = fields.Date.context_today(self)
        equipments = self.env['maintenance.equipment'].search([
            ('is_oil_equipment', '=', True),
            ('certification_expiry', '<', today),
            ('is_decommissioned', '=', False)
        ])
        for equip in equipments:
            existing = self.env['oil.aro.obligation'].search([
                ('equipment_id', '=', equip.id),
                ('state', '!=', 'cancelled')
            ])
            if not existing:
                self.env['oil.aro.obligation'].create({
                    'name': _("ARO Suggestion (Cert Expired): %s") % equip.name,
                    'asset_kind': 'equipment',
                    'equipment_id': equip.id,
                    'state': 'draft',
                    'future_cost': 10000.0,
                    'description': _("Automated ARO suggestion triggered by expired certification (%s) on equipment: %s") % (equip.certification_expiry, equip.name),
                })
                equip.message_post(body=_("Certification expired on %s. Suggestion for ARO Obligation created.") % equip.certification_expiry)

    # ---------------------------------------------------------
    # SMART BUTTON ACTIONS
    # ---------------------------------------------------------

    def action_view_wip(self):
        """Triggers the transition of the record to proceed with the 'view wip' step in the workflow."""
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Decommissioning WIP'),
            'res_model': 'oil.aro.wip',
            'view_mode': 'list,form',
            'domain': [('obligation_id', '=', self.id)],
            'context': {
                'default_obligation_id': self.id,
            },
        }

    def action_view_accretion(self):
        """Triggers the transition of the record to proceed with the 'view accretion' step in the workflow."""
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Accretion Schedule'),
            'res_model': 'oil.aro.accretion.line',
            'view_mode': 'list,form',
            'domain': [('obligation_id', '=', self.id)],
        }

    def action_view_revisions(self):
        """Triggers the transition of the record to proceed with the 'view revisions' step in the workflow."""
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': _('ARO Revisions'),
            'res_model': 'oil.aro.revision',
            'view_mode': 'list,form',
            'domain': [('obligation_id', '=', self.id)],
        }

    def action_view_journals(self):
        """Triggers the transition of the record to proceed with the 'view journals' step in the workflow."""
        self.ensure_one()

        moves = (
                self.initial_move_id
                | self.settlement_move_id
                | self.accretion_line_ids.mapped('move_id')
                | self.revision_ids.mapped('move_id')
                | self.wip_line_ids.mapped('move_id')
        )

        return {
            'type': 'ir.actions.act_window',
            'name': _('ARO Journal Entries'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', moves.ids)],
        }

    def bulk_schedule_execute(self, template, line=None):
        """Target 2 (update) — post one accretion period on this obligation.

        The hook reimplements no accounting: it calls the existing
        ``post_accretion()`` (IAS 37 Effective Interest Method) exactly as the
        standalone cron does. ``post_accretion()`` returns False when the
        obligation is not yet due (same-period guard) or in a non-accreting
        state — that maps to a skipped line. A missing-account/state UserError
        is caught by the engine and also marks the line skipped.
        """
        if template.target_model_name == 'oil.aro.accretion.line':
            posting_date = template.aro_posting_date
            if not posting_date and line and line.job_id and \
                    line.job_id.scheduled_date:
                posting_date = fields.Date.to_date(line.job_id.scheduled_date)
            posting_date = posting_date or fields.Date.context_today(self)
            # Snapshot the balance fields so the framework can restore them on
            # rollback (the GL move itself is not reversed — see the existing
            # action_cancel for a full reversal path).
            if line:
                line._set_original_value({
                    'current_liability_balance': self.current_liability_balance,
                    'accreted_to_date': self.accreted_to_date,
                    'last_accretion_date': (
                        fields.Date.to_string(self.last_accretion_date)
                        if self.last_accretion_date else False
                    ),
                })
            posted = self.post_accretion(posting_date)
            if not posted and line:
                line.write({
                    'state': 'skipped',
                    'skip_reason': 'already_processed',
                })
            return False
        return super().bulk_schedule_execute(template, line)

