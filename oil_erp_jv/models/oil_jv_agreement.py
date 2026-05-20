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

from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class OilJVAgreement(models.Model):
    """
    Master Joint Operating Agreement (JOA). Contains the list of JV partners
    with their Working Interest percentages which must sum to exactly 100%.
    """
    _name = 'oil.jv.agreement'
    _description = 'Joint Operating Agreement'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc, id desc'

    name = fields.Char(
        string='JOA Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        help="Auto-generated JOA reference number.")
    title = fields.Char(
        string='Agreement Title',
        required=True,
        tracking=True,
        help="Descriptive title for this Joint Operating Agreement.")
    project_id = fields.Many2one(
        'project.project',
        string='Project / Block',
        required=True,
        tracking=True,
        domain="[('is_template', '=', False), ('is_oil_gas_project', '=', True)]",
        help="Oil & Gas project or block covered by this JOA.")
    operator_id = fields.Many2one(
        'res.partner',
        string='Operator',
        required=True,
        tracking=True,
        help="The operating partner who manages day-to-day operations.")
    effective_date = fields.Date(
        string='Effective Date',
        required=True,
        tracking=True,
        help="Date when this agreement becomes effective.")
    expiry_date = fields.Date(
        string='Expiry Date',
        tracking=True,
        help="Date when this agreement expires.")
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id,
        help="Currency used for all financial transactions under this JOA.")
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        help="Company that owns this JOA record.")
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('active', 'Active'),
            ('expired', 'Expired'),
            ('terminated', 'Terminated'),
        ],
        string='Status',
        default='draft',
        tracking=True,
        help="Current status of the agreement.")
    partner_ids = fields.One2many(
        'oil.jv.partner',
        'agreement_id',
        string='JV Partners',
        help="List of joint venture partners and their working interests.")
    total_wi = fields.Float(
        string='Total WI %',
        compute='_compute_total_wi',
        store=True,
        digits=(6, 4),
        help="Sum of all partner Working Interests. Must equal 100%.")
    afe_ids = fields.One2many(
        'oil.afe',
        'agreement_id',
        string='AFEs',
        help="Authority for Expenditure records under this JOA.")
    afe_count = fields.Integer(
        string='AFE Count',
        compute='_compute_afe_count',
        help="Number of AFEs under this agreement.")
    cash_call_ids = fields.One2many(
        'oil.jv.cash.call',
        'agreement_id',
        string='Cash Calls',
        help="Cash calls issued under this JOA.")
    jib_ids = fields.One2many(
        'oil.jv.jib',
        'agreement_id',
        string='JIBs',
        help="Joint Interest Billing statements under this JOA.")
    cash_call_count = fields.Integer(
        string='Cash Call Count',
        compute='_compute_cash_call_count',
        help="Number of cash calls under this agreement.")
    jib_count = fields.Integer(
        string='JIB Count',
        compute='_compute_jib_count',
        help="Number of JIBs under this agreement.")
    revenue_ids = fields.One2many(
        'oil.jv.revenue',
        'agreement_id',
        string='Revenue Distributions',
        help="Revenue distribution records under this JOA.")
    revenue_count = fields.Integer(
        string='Revenue Count',
        compute='_compute_revenue_count',
        help="Number of revenue distributions under this agreement.")
    royalty_ids = fields.One2many(
        'oil.royalty',
        'jv_agreement_id',
        string='Royalties',
        help="Royalty records linked to this JOA.")
    royalty_count = fields.Integer(
        string='Royalty Count',
        compute='_compute_royalty_count',
        help="Number of royalties linked to this agreement.")
    total_nri = fields.Float(
        string='Total NRI %',
        compute='_compute_total_nri',
        store=True,
        digits=(6, 4),
        help="Sum of all partner Net Revenue Interests.")
    validation_warnings = fields.Text(
        string='Validation Warnings',
        compute='_compute_validation_warnings',
        help="Computed warnings about partner interest configuration.")
    accounting_method = fields.Selection(
        [
            ('proportionate', 'Proportionate Consolidation'),
            ('equity', 'Equity Method'),
        ],
        string='Accounting Method',
        default='proportionate',
        tracking=True,
        help="Method used for JV accounting.")
    notes = fields.Text(
        string='Notes',
        help="Additional terms, clauses or notes about this JOA.")

    @api.depends('partner_ids.working_interest')
    def _compute_total_wi(self):
        """Computes total working interest across all JV partners."""
        for record in self:
            record.total_wi = sum(record.partner_ids.mapped('working_interest'))

    @api.depends('partner_ids.net_revenue_interest')
    def _compute_total_nri(self):
        """Computes total NRI across all JV partners."""
        for record in self:
            record.total_nri = sum(
                record.partner_ids.mapped('net_revenue_interest'))

    @api.depends('partner_ids.working_interest',
                 'partner_ids.net_revenue_interest',
                 'partner_ids.is_operator',
                 'partner_ids.partner_id')
    def _compute_validation_warnings(self):
        """Computes soft validation warnings displayed in the form."""
        for record in self:
            warnings = []
            for p in record.partner_ids:
                if (p.net_revenue_interest
                        and p.net_revenue_interest > p.working_interest):
                    warnings.append(
                        _("Partner '%s': NRI (%.4f%%) exceeds WI (%.4f%%). "
                          "NRI should typically be less than or equal to WI.",
                          p.partner_id.name,
                          p.net_revenue_interest,
                          p.working_interest))
            record.validation_warnings = (
                '\n'.join(warnings) if warnings else False)

    def _compute_afe_count(self):
        """Computes count of AFEs linked to this agreement."""
        for record in self:
            record.afe_count = len(record.afe_ids)

    def _compute_cash_call_count(self):
        """Computes count of Cash Calls linked to this agreement."""
        for record in self:
            record.cash_call_count = len(record.cash_call_ids)

    def _compute_jib_count(self):
        """Computes count of JIBs linked to this agreement."""
        for record in self:
            record.jib_count = len(record.jib_ids)

    def _compute_revenue_count(self):
        """Computes count of Revenue Distributions linked to this agreement."""
        for record in self:
            record.revenue_count = len(record.revenue_ids)

    def _compute_royalty_count(self):
        """Computes count of Royalties linked to this agreement."""
        for record in self:
            record.royalty_count = len(record.royalty_ids)

    @api.constrains('partner_ids')
    def _check_wi_sum(self):
        """Validates that working interests sum to exactly 100%."""
        for record in self:
            if record.partner_ids:
                total = sum(record.partner_ids.mapped('working_interest'))
                if abs(total - 100.0) > 0.01:
                    raise ValidationError(
                        _("Working interests must sum to 100%%. "
                          "Current total: %.4f%% for '%s'.",
                          total, record.name))

    @api.constrains('partner_ids')
    def _check_nri_total(self):
        """Validates that total NRI does not exceed 100%."""
        for record in self:
            nri_partners = record.partner_ids.filtered(
                lambda p: p.net_revenue_interest > 0)
            if nri_partners:
                total_nri = sum(nri_partners.mapped('net_revenue_interest'))
                if total_nri > 100.0 + 0.01:
                    raise ValidationError(
                        _("Total Net Revenue Interest cannot exceed 100%%. "
                          "Current total: %.4f%% for '%s'.",
                          total_nri, record.name))

    @api.constrains('partner_ids')
    def _check_single_operator(self):
        """Validates that only one partner is marked as operator."""
        for record in self:
            operators = record.partner_ids.filtered('is_operator')
            if len(operators) > 1:
                names = ', '.join(operators.mapped('partner_id.name'))
                raise ValidationError(
                    _("Only one operator is allowed per agreement. "
                      "Found multiple operators: %s in '%s'.",
                      names, record.name))

    @api.constrains('effective_date', 'expiry_date')
    def _check_dates(self):
        """Validates expiry date is after effective date."""
        for record in self:
            if record.expiry_date and record.effective_date:
                if record.expiry_date <= record.effective_date:
                    raise ValidationError(
                        _("Expiry date must be after effective date for '%s'.",
                          record.name))

    @api.model_create_multi
    def create(self, vals_list):
        """Assigns auto-sequence on creation."""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'oil.jv.agreement') or _('New')
        return super().create(vals_list)

    def action_activate(self):
        """Activates the JOA after validation."""
        for record in self:
            if record.state != 'draft':
                raise UserError(_("Only draft agreements can be activated."))
            if not record.partner_ids:
                raise UserError(
                    _("Add at least one JV partner before activating."))
            total = sum(record.partner_ids.mapped('working_interest'))
            if abs(total - 100.0) > 0.01:
                raise UserError(
                    _("Working interests must sum to 100%% before activation. "
                      "Current total: %.4f%%.", total))
            record.write({'state': 'active'})

    def action_expire(self):
        """Marks the agreement as expired."""
        for record in self:
            if record.state != 'active':
                raise UserError(
                    _("Only active agreements can be marked as expired."))
            record.write({'state': 'expired'})

    def action_terminate(self):
        """Terminates the agreement."""
        for record in self:
            if record.state not in ('draft', 'active'):
                raise UserError(
                    _("Only draft or active agreements can be terminated."))
            record.write({'state': 'terminated'})

    def action_set_to_draft(self):
        """Resets agreement back to draft."""
        for record in self:
            if record.state == 'active':
                raise UserError(
                    _("Active agreements cannot be reset to draft. "
                      "Terminate first if needed."))
            record.write({'state': 'draft'})

    def action_view_afes(self):
        """Opens the list of AFEs linked to this JOA."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('AFEs'),
            'res_model': 'oil.afe',
            'view_mode': 'list,form',
            'domain': [('agreement_id', '=', self.id)],
            'context': {'default_agreement_id': self.id},
            'target': 'current',
        }

    def action_view_cash_calls(self):
        """Opens the list of Cash Calls linked to this JOA."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cash Calls'),
            'res_model': 'oil.jv.cash.call',
            'view_mode': 'list,form',
            'domain': [('agreement_id', '=', self.id)],
            'context': {'default_agreement_id': self.id},
            'target': 'current',
        }

    def action_view_jibs(self):
        """Opens the list of JIBs linked to this JOA."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Joint Interest Billing'),
            'res_model': 'oil.jv.jib',
            'view_mode': 'list,form',
            'domain': [('agreement_id', '=', self.id)],
            'context': {'default_agreement_id': self.id},
            'target': 'current',
        }

    def action_view_revenues(self):
        """Opens the list of Revenue Distributions linked to this JOA."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Revenue Distributions'),
            'res_model': 'oil.jv.revenue',
            'view_mode': 'list,form',
            'domain': [('agreement_id', '=', self.id)],
            'context': {'default_agreement_id': self.id},
            'target': 'current',
        }

    def action_view_royalties(self):
        """Opens the list of Royalties linked to this JOA."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Royalties'),
            'res_model': 'oil.royalty',
            'view_mode': 'list,form',
            'domain': [('jv_agreement_id', '=', self.id)],
            'context': {'default_jv_agreement_id': self.id},
            'target': 'current',
        }

    def action_create_royalty(self):
        """Creates a new Royalty record pre-linked to this JOA."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create Royalty'),
            'res_model': 'oil.royalty',
            'view_mode': 'form',
            'context': {'default_jv_agreement_id': self.id},
            'target': 'current',
        }

    @api.model
    def _cron_check_joa_expiry(self):
        """Scheduled action: expire active JOAs past expiry_date and
        warn/cancel related records (contracts, royalties, revenue
        distributions)."""
        today = fields.Date.today()
        expired = self.search([
            ('state', '=', 'active'),
            ('expiry_date', '!=', False),
            ('expiry_date', '<', today),
        ])
        for joa in expired:
            joa.write({'state': 'expired'})
            joa.message_post(
                body=_("JOA automatically expired on %s.", today),
                message_type='notification')

            # Expire related contracts linked to this JOA
            contracts = self.env['oil.contract'].search([
                ('jv_agreement_id', '=', joa.id),
                ('state', 'in', ('draft', 'confirmed')),
            ])
            for contract in contracts:
                contract.write({'state': 'expired'})
                contract.message_post(
                    body=_("Contract expired because JOA '%s' expired.",
                           joa.name),
                    message_type='notification')

            # Warn on confirmed royalties
            royalties = self.env['oil.royalty'].search([
                ('jv_agreement_id', '=', joa.id),
                ('state', '=', 'confirmed'),
            ])
            for royalty in royalties:
                royalty.message_post(
                    body=_("Warning: JV Agreement '%s' has expired. "
                           "Please review this royalty.", joa.name),
                    message_type='notification')

            # Warn on draft revenue distributions
            revenues = self.env['oil.jv.revenue'].search([
                ('agreement_id', '=', joa.id),
                ('state', '=', 'draft'),
            ])
            for rev in revenues:
                rev.message_post(
                    body=_("Warning: JV Agreement '%s' has expired. "
                           "This revenue distribution cannot proceed.",
                           joa.name),
                    message_type='notification')
