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
from odoo.exceptions import UserError, ValidationError
from odoo.tools.translate import _

class OilAroWip(models.Model):
    """
    Work-in-Progress cost line for a decommissioning project.

    During execution every cost (vendor bills, labour, materials) is
    recorded here.  The WIP total feeds directly into the settlement
    calculation.
    """
    _name = 'oil.aro.wip'
    _description = 'Decommissioning WIP Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    display_name = fields.Char(compute='_compute_display_name', help="A unique name or reference identifier used to track this record in the system.")

    def _compute_display_name(self):
        """Calculates and updates the 'name' value automatically based on related operational inputs."""
        for rec in self:
            rec.display_name = f"{rec.date or ''}: {rec.description or ''} ({rec.amount or 0.0})"

    obligation_id = fields.Many2one('oil.aro.obligation', string='ARO Obligation', required=True,
                                    ondelete='cascade', tracking=True, help="Link this transaction or record to the corresponding 'aro obligation' reference.")
    date = fields.Date(string='Date', required=True, default=fields.Date.context_today, tracking=True, help="The date when this transaction, measurement, or event was officially recorded.")
    cost_type = fields.Selection([('vendor_bill', 'Vendor Bill'), ('labour', 'Internal Labour'),
                                  ('material', 'Materials / Stock'), ('regulatory', 'Regulatory / Permits'),
                                  ('other', 'Other'), ], string='Cost Type', required=True, tracking=True, help="The unit rate or total financial cost applied to this transaction.")
    description = fields.Char(string='Description', required=True, tracking=True, help="Additional comments, details, or operational remarks about this record.")
    amount = fields.Monetary(string='Amount', currency_field='currency_id', required=True, tracking=True, help="The unit rate or total financial cost applied to this transaction.")
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.company.currency_id, help="Link this transaction or record to the corresponding 'currency' reference.")
    cost_center_id = fields.Many2one('account.analytic.account', string='Cost Center', help="The unit rate or total financial cost applied to this transaction.")
    decommissioning_plan_id = fields.Many2one('project.project', string='Decommissioning Project', help="Link this transaction or record to the corresponding 'decommissioning project' reference.")
    source_bill_id = fields.Many2one('account.move', string='Vendor Bill',
                                     domain=[('move_type', 'in', ('in_invoice', 'in_refund'))], help="Link this transaction or record to the corresponding 'vendor bill' reference.")
    source_partner_id = fields.Many2one('res.partner', string='Vendor / Party', help="Link this transaction or record to the corresponding 'vendor / party' reference.")
    move_id = fields.Many2one('account.move', string='WIP Journal Entry', readonly=True, help="Link this transaction or record to the corresponding 'wip journal entry' reference.")
    posted_date = fields.Date(string='Posted Date', readonly=True, help="The date when this transaction, measurement, or event was officially recorded.")
    state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted to WIP'), ('settled', 'Settled')], string='Status',
                             default='draft', tracking=True, help="The current step of this record in its operational or approval lifecycle.")
    settlement_move_id = fields.Many2one('account.move', string='Settlement Move', readonly=True, help="Link this transaction or record to the corresponding 'settlement move' reference.")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, help="The company managing this operational record or transaction.")


    # ── CONSTRAINTS ─────────────────────────────────────────────────
    @api.constrains('amount')
    def _check_amount(self):
        """Enforces validation rules to ensure '' meets required safety and regulatory standards."""
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError(_('Amount must be greater than zero.'))

    @api.onchange('obligation_id')
    def _onchange_obligation_id(self):
        """Refreshes UI fields and updates default values dynamically when the user modifies the 'id' field."""
        if self.obligation_id:
            self.cost_center_id = self.obligation_id.cost_center_id or self.obligation_id.analytic_account_id
            self.decommissioning_plan_id = self.obligation_id.decommissioning_plan_id

    def action_post_wip(self):
        """
        Post WIP Cost

        Accounting Entry:
            Dr Decommissioning WIP
            Cr Accounts Payable
        """
        for rec in self:
            if rec.state != 'draft':
                continue

            ob = rec.obligation_id

            # ---------------------------------------------------------
            # VALIDATIONS
            # ---------------------------------------------------------
            if not ob.wip_account_id:
                raise UserError(_('Configure WIP Account on the ARO obligation.'))
            if not ob.journal_id:
                raise UserError(_('Configure ARO Journal on the ARO obligation.'))
            if not rec.currency_id:
                raise UserError(_('Currency is required.'))

            # ---------------------------------------------------------
            # GET ACCOUNTS PAYABLE
            # ---------------------------------------------------------
            company = ob.company_id or rec.company_id or self.env.company
            # Use partner's default payable account (company aware)
            ap_account = self.env['res.partner'].with_company(company).property_account_payable_id
            if not ap_account:
                # Fallback: search any payable account without company filter
                ap_account = self.env['account.account'].search([
                    ('account_type', '=', 'liability_payable'),
                ], limit=1)
            if not ap_account:
                raise UserError(_(
                    'No Accounts Payable account found.\n'
                    'Please configure a default payable account on the company '
                    'or ensure your chart of accounts has a payable account.'
                ))

            # ---------------------------------------------------------
            # ANALYTIC DISTRIBUTION
            # ---------------------------------------------------------
            analytic_acc = rec.cost_center_id or ob.cost_center_id or ob.analytic_account_id
            analytic_distribution = {str(analytic_acc.id): 100.0} if analytic_acc else False

            # ---------------------------------------------------------
            # MULTI CURRENCY – convert to company currency
            # ---------------------------------------------------------
            company_currency = company.currency_id
            amount_company = rec.currency_id._convert(
                rec.amount,
                company_currency,
                company,
                rec.date or fields.Date.context_today(self)
            )
            use_foreign = rec.currency_id != company_currency

            # ---------------------------------------------------------
            # BUILD JOURNAL ITEMS (skip currency fields when not foreign)
            # ---------------------------------------------------------
            debit_line_vals = {
                'name': rec.description,
                'account_id': ob.wip_account_id.id,
                'debit': amount_company,
                'credit': 0.0,
                'analytic_distribution': analytic_distribution,
            }
            credit_line_vals = {
                'name': rec.description,
                'account_id': ap_account.id,
                'debit': 0.0,
                'credit': amount_company,
            }
            if use_foreign:
                debit_line_vals.update({
                    'currency_id': rec.currency_id.id,
                    'amount_currency': rec.amount,
                })
                credit_line_vals.update({
                    'currency_id': rec.currency_id.id,
                    'amount_currency': -rec.amount,
                })
            # If not foreign, no currency_id or amount_currency fields are added

            # ---------------------------------------------------------
            # CREATE OR UPDATE JOURNAL ENTRY
            # ---------------------------------------------------------
            if rec.move_id:
                move = rec.move_id
                move_vals = {
                    'journal_id': ob.journal_id.id,
                    'date': rec.date,
                    'ref': _('ARO WIP - %s') % ob.name,
                    'line_ids': [(5, 0, 0), (0, 0, debit_line_vals), (0, 0, credit_line_vals)],
                }
                move.write(move_vals)
            else:
                move_vals = {
                    'move_type': 'entry',
                    'journal_id': ob.journal_id.id,
                    'date': rec.date,
                    'ref': _('ARO WIP - %s') % ob.name,
                    'line_ids': [(0, 0, debit_line_vals), (0, 0, credit_line_vals)],
                }
                move = self.env['account.move'].create(move_vals)
            move.action_post()

            rec.write({
                'move_id': move.id,
                'state': 'posted',
                'posted_date': fields.Date.today(),
            })
            rec.message_post(body=_('Posted to WIP. Journal Entry %s updated/created.') % move.name)

    def action_reset_draft(self):
        """Triggers the transition of the record to proceed with the 'reset draft' step in the workflow."""
        for rec in self:
            if rec.move_id:
                rec.move_id.button_draft()
            rec.state = 'draft'
