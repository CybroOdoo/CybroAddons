# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    recurring_invoice_id = fields.Many2one(
        'account.recurring.invoice', string='Recurring Invoice',
        copy=False, index='btree_not_null',
        help="The recurring template that generated this invoice.")
    asset_depreciation_ids = fields.One2many('account.asset.depreciation.line',
                                             'move_id',
                                             string='Assets Depreciation Lines')
    to_check = fields.Boolean(string='To Check', tracking=True,
                              help="If this checkbox is ticked, it means that the user was not sure of all the related "
                                   "information at the time of the creation of the move and that the move needs to be "
                                   "checked again.",
                              )

    def _post(self, soft=True):
        """After posting: mark the depreciation lines as posted, close the
        fully depreciated assets and create the assets of the bill lines.

        ``_post`` is also what core's auto-post cron calls, so this runs for
        every posted move, not only from the Post button."""
        posted = super()._post(soft=soft)
        posted.asset_depreciation_ids.post_lines_and_close_asset()
        for move in posted.filtered(lambda m: m.is_invoice()):
            # The default type in the context is the invoice type, not the
            # asset type: remove it before creating the assets.
            context = dict(self.env.context)
            context.pop('default_type', None)
            move.invoice_line_ids.with_context(context).sudo().asset_create()
        return posted

    def button_draft(self):
        """Resetting a bill to draft removes the assets it created, so posting
        it again does not create them twice. Assets that already have
        depreciation entries must be cancelled first."""
        assets = self.env['account.asset.asset'].sudo().with_context(
            active_test=False).search([('invoice_id', 'in', self.ids),
                                       ('state', '!=', 'cancelled')])
        with_entries = assets.filtered(
            lambda a: a.depreciation_line_ids.filtered('move_check'))
        if with_entries:
            raise UserError(_(
                "This document has assets with depreciation entries: %s. "
                "Cancel these assets first.",
                ', '.join(with_entries.mapped('name'))))
        res = super().button_draft()
        assets.write({'state': 'draft'})
        assets.unlink()
        return res

    def _invoice_paid_hook(self):
        """When an invoice is paid, clear the customer's follow-up level if
        nothing is left open, so the next overdue invoice starts again at the
        first level."""
        res = super()._invoice_paid_hook()
        self.filtered(lambda m: m.move_type == 'out_invoice') \
            .commercial_partner_id._reset_followup_level()
        return res

    def button_cancel(self):
        """A cancelled depreciation entry frees its board line, so the entry
        is created again when it is due."""
        res = super().button_cancel()
        self.asset_depreciation_ids.write({'move_id': False})
        return res

    def action_post(self):
        """To check the selected customers due amount is exceed than blocking stage"""
        pay_type = ['out_invoice', 'out_refund', 'out_receipt']
        for rec in self:
            if rec.partner_id.active_limit and rec.move_type in pay_type \
                    and rec.partner_id.enable_credit_limit:
                if rec.due_amount >= rec.partner_id.blocking_stage and rec.partner_id.blocking_stage != 0:
                    raise UserError(_(
                        "%s is in  Blocking Stage and "
                        "has a due amount of %s %s to pay") % (
                                        rec.partner_id.name, rec.due_amount,
                                        rec.currency_id.symbol))

        # Assets and depreciation lines are handled in ``_post``.
        return super().action_post()

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
