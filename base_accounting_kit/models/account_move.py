# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    """Inherits from the account.move model for adding the depreciation
    field to the account"""
    _inherit = 'account.move'

    has_due = fields.Boolean(string='Has due')
    is_warning = fields.Boolean(string='Is warning')
    due_amount = fields.Float(string="Due Amount",
                              related='partner_id.due_amount')
    recurring_ref = fields.Char(string='Recurring Ref')
    asset_depreciation_ids = fields.One2many('account.asset.depreciation.line',
                                             'move_id',
                                             string='Assets Depreciation Lines')
    to_check = fields.Boolean(string='To Check', tracking=True,
                              help="If this checkbox is ticked, it means that "
                                   "the user was not sure of all the related "
                                   "information at the time of the creation of "
                                   "the move and that the move needs to be "
                                   "checked again.",
                              )

    def button_cancel(self):
        """Button action to cancel the transfer"""
        for move in self:
            for line in move.asset_depreciation_ids:
                line.move_posted_check = False
        return super(AccountMove, self).button_cancel()

    def post(self):
        """Supering the post method to mapped the asset depreciation records"""
        self.mapped('asset_depreciation_ids').post_lines_and_close_asset()
        return super(AccountMove, self).action_post()

    @api.model
    def _refund_cleanup_lines(self, lines):
        """Supering the refund cleanup lines to check the asset category """
        result = super(AccountMove, self)._refund_cleanup_lines(lines)
        for i, line in enumerate(lines):
            for name, field in line._fields.items():
                if name == 'asset_category_id':
                    result[i][2][name] = False
                    break
        return result

    def action_cancel(self):
        """Action perform to cancel the asset record"""
        res = super(AccountMove, self).action_cancel()
        self.env['account.asset.asset'].sudo().search(
            [('invoice_id', 'in', self.ids)]).write({'active': False})
        return res

    def action_post(self):
        """To check the selected customers due amount is exceed than blocking stage"""
        pay_type = ['out_invoice', 'out_refund', 'out_receipt']
        for rec in self:
            if rec.partner_id.active_limit and rec.move_type in pay_type \
                    and rec.partner_id.enable_credit_limit:
                if rec.due_amount >= rec.partner_id.blocking_stage \
                        and rec.partner_id.blocking_stage != 0:
                    raise UserError(_(
                        "%s is in  Blocking Stage and "
                        "has a due amount of %s %s to pay") % (
                                        rec.partner_id.name, rec.due_amount,
                                        rec.currency_id.symbol))

        result = super(AccountMove, self).action_post()
        for inv in self:
            context = dict(self.env.context)
            context.pop('default_type', None)
            inv.invoice_line_ids.with_context(context).asset_create()
        return result

    @api.depends('amount_residual', 'move_type', 'state', 'company_id',
                 'reconciled_payment_ids.state',
                 'reconciled_payment_ids.is_matched')
    def _compute_payment_state(self):
        """Override to ensure invoices remain 'in_payment' if linked bank
        payments are not matched with a statement."""
        super()._compute_payment_state()
        for move in self:
            if move.state == 'posted' and move.is_invoice(True) and \
                    move.payment_state == 'paid':
                payments = move._get_reconciled_payments()
                if any(p.journal_id.type in ('bank', 'cash') and
                       not p.is_matched for p in payments):
                    move.payment_state = 'in_payment'

    @api.onchange('partner_id')
    def check_due(self):
        """To show the due amount and warning stage"""
        if self.partner_id and self.partner_id.due_amount > 0 \
                and self.partner_id.active_limit \
                and self.partner_id.enable_credit_limit:
            self.has_due = True
        else:
            self.has_due = False
        if self.partner_id and self.partner_id.active_limit \
                and self.partner_id.enable_credit_limit:
            if self.due_amount >= self.partner_id.warning_stage:
                if self.partner_id.warning_stage != 0:
                    self.is_warning = True
        else:
            self.is_warning = False
