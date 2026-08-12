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
from odoo.exceptions import UserError
from odoo.tools.translate import _

class OilAroSettlementWizard(models.TransientModel):
    _name = 'oil.aro.settlement.wizard'
    _description = 'ARO Settlement Wizard'

    obligation_id = fields.Many2one('oil.aro.obligation', string='ARO Obligation', required=True,
                                    readonly=True, help="Link this transaction or record to the corresponding 'aro obligation' reference.")
    settlement_type = fields.Selection([
        ('full', 'Full Settlement'),
        ('partial', 'Partial Settlement')
    ], string='Settlement Type', default='full', required=True, help="Select the appropriate classification or category for 'settlement type'.")
    wip_line_ids = fields.Many2many('oil.aro.wip', string='WIP Lines to Settle', help="Link this transaction or record to the corresponding 'wip lines to settle' reference.")
    partial_liability_amount = fields.Monetary(string='Liability Amount to Release', currency_field='currency_id', help="The unit rate or total financial cost applied to this transaction.")
    settlement_date = fields.Date(string='Settlement Date', required=True, default=fields.Date.context_today, help="The date when this transaction, measurement, or event was officially recorded.")
    salvage_amount = fields.Monetary(string='Salvage Revenue / (Disposal Cost)', currency_field='currency_id', default=0.0, help="The unit rate or total financial cost applied to this transaction.")
    notes = fields.Text(string='Notes', help="Additional comments, details, or operational remarks about this record.")
    currency_id = fields.Many2one(related='obligation_id.currency_id', readonly=True, help="Link this transaction or record to the corresponding 'currency id' reference.")
    liability_balance = fields.Monetary(string='ARO Liability Balance', currency_field='currency_id',
                                        compute='_compute_preview', help="Specify the numerical measurement, volume, or financial amount for 'aro liability balance'.")
    total_wip = fields.Monetary(string='Total WIP', currency_field='currency_id', compute='_compute_preview', help="Specify the numerical measurement, volume, or financial amount for 'total wip'.")
    net_cost = fields.Monetary(string='Net Cost', currency_field='currency_id', compute='_compute_preview', help="The unit rate or total financial cost applied to this transaction.")
    variance = fields.Monetary(string='Variance', currency_field='currency_id', compute='_compute_preview', help="Specify the numerical measurement, volume, or financial amount for 'variance'.")
    result = fields.Char(string='Result', compute='_compute_preview', help="Specify the description or text value representing 'result'.", )

    @api.model
    def default_get(self, fields_list):
        """Executes the 'default get' process within the operational workflow."""
        res = super().default_get(fields_list)
        if 'obligation_id' in res or self._context.get('default_obligation_id'):
            ob_id = res.get('obligation_id') or self._context.get('default_obligation_id')
            ob = self.env['oil.aro.obligation'].browse(ob_id)
            res['wip_line_ids'] = [(6, 0, ob.wip_line_ids.filtered(lambda l: l.state == 'posted').ids)]
            res['partial_liability_amount'] = ob.current_liability_balance
        return res

    @api.onchange('settlement_type', 'obligation_id')
    def _onchange_settlement_type(self):
        """Refreshes UI fields and updates default values dynamically when the user modifies the 'type' field."""
        if self.settlement_type == 'partial' and self.obligation_id:
            self.partial_liability_amount = self.obligation_id.current_liability_balance

    @api.depends('obligation_id', 'salvage_amount', 'settlement_type', 'partial_liability_amount', 'wip_line_ids')
    def _compute_preview(self):
        """Calculates and updates the '' value automatically based on related operational inputs."""
        for rec in self:
            ob = rec.obligation_id

            if rec.settlement_type == 'full':
                liability = ob.current_liability_balance
            else:
                liability = rec.partial_liability_amount or 0.0

            # Sum selected WIP lines converting currency if necessary
            wip = 0.0
            for line in rec.wip_line_ids:
                if line.currency_id != ob.currency_id:
                    wip += line.currency_id._convert(
                        line.amount, ob.currency_id, ob.company_id or self.env.company, line.date or fields.Date.context_today(self)
                    )
                else:
                    wip += line.amount

            salvage = rec.salvage_amount or 0.0
            net = wip - salvage
            var = liability - net

            rec.liability_balance = liability
            rec.total_wip = wip
            rec.net_cost = net
            rec.variance = var

            if var > 0:
                rec.result = 'GAIN'
            elif var < 0:
                rec.result = 'LOSS'
            else:
                rec.result = 'BREAKEVEN'

    def action_settle(self):
        """Triggers the transition of the record to proceed with the 'settle' step in the workflow."""
        self.ensure_one()
        ob = self.obligation_id

        if ob.state != 'executing':
            raise UserError(_('Only executing ARO obligations can be settled.'))

        if self.settlement_type == 'partial':
            if self.partial_liability_amount <= 0:
                raise UserError(
                    _('Partial liability amount must be greater than zero.')
                )

            if self.partial_liability_amount > ob.current_liability_balance:
                raise UserError(
                    _('Partial liability cannot exceed current liability balance.')
                )

            if not self.wip_line_ids:
                raise UserError(
                    _('Select at least one WIP line.')
                )

        liability = self.liability_balance
        wip = self.total_wip
        salvage = self.salvage_amount or 0.0

        if salvage > 0 and salvage > wip:
            raise UserError(
                _('Salvage revenue cannot exceed WIP cost.')
            )

        # Actual net cost after salvage recovery
        net_cost = wip - salvage

        # Positive = gain
        # Negative = loss
        variance = liability - net_cost

        missing = []

        if not ob.liability_account_id:
            missing.append(_('ARO Liability Account'))

        if not ob.wip_account_id:
            missing.append(_('Decommissioning WIP Account'))

        if variance > 0 and not ob.settlement_gain_account_id:
            missing.append(_('Settlement Gain Account'))

        if variance < 0 and not ob.settlement_loss_account_id:
            missing.append(_('Settlement Loss Account'))

        if missing:
            raise UserError(
                _('Please configure:\n%s')
                % '\n'.join(missing)
            )

        lines = []

        # -------------------------------------------------
        # DR ARO LIABILITY
        # -------------------------------------------------
        lines.append((0, 0, {
            'name': _('ARO Liability Settlement'),
            'account_id': ob.liability_account_id.id,
            'debit': liability,
            'credit': 0.0,
        }))

        # -------------------------------------------------
        # CR WIP
        # -------------------------------------------------
        if wip:
            lines.append((0, 0, {
                'name': _('Clear Decommissioning WIP'),
                'account_id': ob.wip_account_id.id,
                'debit': 0.0,
                'credit': wip,
            }))

        # -------------------------------------------------
        # SALVAGE REVENUE
        # -------------------------------------------------
        if salvage > 0:
            lines.append((0, 0, {
                'name': _('Salvage Revenue'),
                'account_id': ob.settlement_gain_account_id.id,
                'debit': 0.0,
                'credit': salvage,
            }))

        # -------------------------------------------------
        # DISPOSAL COST
        # -------------------------------------------------
        elif salvage < 0:

            payable_account = self.env['account.account'].search([
                ('account_type', '=', 'liability_payable')
            ], limit=1)

            if not payable_account:
                raise UserError(
                    _('No payable account found.')
                )

            lines.append((0, 0, {
                'name': _('Disposal Cost'),
                'account_id': payable_account.id,
                'debit': 0.0,
                'credit': abs(salvage),
            }))

        # -------------------------------------------------
        # GAIN / LOSS
        # -------------------------------------------------

        total_debit = sum(l[2]['debit'] for l in lines)
        total_credit = sum(l[2]['credit'] for l in lines)

        difference = round(total_debit - total_credit, 2)

        if difference > 0:
            lines.append((0, 0, {
                'name': _('Gain on Settlement'),
                'account_id': ob.settlement_gain_account_id.id,
                'debit': 0.0,
                'credit': difference,
            }))

        elif difference < 0:
            lines.append((0, 0, {
                'name': _('Loss on Settlement'),
                'account_id': ob.settlement_loss_account_id.id,
                'debit': abs(difference),
                'credit': 0.0,
            }))

        move = self.env['account.move'].create({
            'move_type': 'entry',
            'journal_id': ob.journal_id.id,
            'date': self.settlement_date,
            'ref': _('ARO Settlement (%s) - %s') % (
                self.settlement_type,
                ob.name
            ),
            'line_ids': lines,
        })

        move.action_post()

        self.wip_line_ids.write({
            'state': 'settled',
            'settlement_move_id': move.id,
        })

        variance_pct = abs(variance) / (liability or 1.0)

        if variance_pct > 0.10:

            msg = _(
                'DECOMMISSIONING VARIANCE ALERT: '
                'Settlement variance %s exceeds 10%% threshold.'
            ) % ob.currency_id.format(variance)

            ob.message_post(body=msg)

            finance_group = self.env.ref(
                'account.group_account_manager',
                raise_if_not_found=False
            )

            finance_managers = (
                finance_group.users
                if finance_group and hasattr(finance_group, 'users')
                else self.env['res.users']
            )

            for manager in finance_managers:
                self.env['mail.activity'].create({
                    'res_model_id': self.env['ir.model']._get(
                        'oil.aro.obligation'
                    ).id,
                    'res_id': ob.id,
                    'activity_type_id': self.env.ref(
                        'mail.mail_activity_data_todo'
                    ).id,
                    'summary': _(
                        'Decommissioning Variance Alert > 10%'
                    ),
                    'note': msg,
                    'user_id': manager.id,
                    'date_deadline': fields.Date.context_today(self),
                })

        new_liability = (
                ob.current_liability_balance - liability
        )

        if self.settlement_type == 'full':

            ob.write({
                'settlement_date': self.settlement_date,
                'settlement_salvage': salvage,
                'settlement_move_id': move.id,
                'settlement_notes': self.notes,
                'current_liability_balance': 0.0,
                'state': 'settled',
            })

            ob.message_post(
                body=_(
                    'ARO full settlement completed. '
                    'Journal Entry: %s'
                ) % move.name
            )

        else:

            ob.write({
                'settlement_salvage':
                    ob.settlement_salvage + salvage,
                'current_liability_balance':
                    new_liability,
            })

            ob.message_post(
                body=_(
                    'ARO partial settlement completed. '
                    'Remaining liability: %s'
                ) % ob.currency_id.format(new_liability)
            )

        return {
            'type': 'ir.actions.act_window_close'
        }
