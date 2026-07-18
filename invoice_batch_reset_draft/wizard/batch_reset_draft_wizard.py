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

# Only customer invoices, vendor bills and their credit notes / refunds.
INVOICE_TYPES = ('out_invoice', 'in_invoice', 'out_refund', 'in_refund')


class InvoiceBatchResetDraftWizard(models.TransientModel):
    _name = 'invoice.batch.reset.draft.wizard'
    _description = 'Reset / Cancel Invoices in Bulk'

    operation = fields.Selection(
        selection=[('draft', 'Reset to Draft'), ('cancel', 'Cancel')],
        string='Operation', required=True, default='draft')
    move_ids = fields.Many2many(
        comodel_name='account.move', string='Invoices')
    reason = fields.Char(
        string='Reason',
        help="Optional. Logged in the chatter of each affected invoice.")
    eligible_count = fields.Integer(
        string='Eligible', compute='_compute_preview')
    skipped_count = fields.Integer(
        string='Skipped', compute='_compute_preview')
    preview = fields.Html(
        string='Summary', compute='_compute_preview', sanitize=False)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        moves = self.env['account.move'].browse(
            self.env.context.get('active_ids', []))
        # Keep only invoices / bills / refunds; other move types are ignored.
        moves = moves.filtered(lambda m: m.move_type in INVOICE_TYPES)
        res['move_ids'] = [(6, 0, moves.ids)]
        return res

    def _skip_reason(self, move):
        """Return None if `move` can undergo the chosen operation, else a
        human-readable reason (used both for the preview and to skip safely)."""
        self.ensure_one()
        if self.operation == 'draft':
            if move.state not in ('posted', 'cancel'):
                return _('Not posted or cancelled (%s)', move.state)
            if move.state == 'posted' and move.need_cancel_request:
                return _('Needs a cancellation request')
            if move.inalterable_hash:
                return _('Locked / hashed entry')
            if move.tax_cash_basis_rec_id or move.tax_cash_basis_origin_move_id:
                return _('Tax cash-basis entry')
        else:  # cancel
            if move.state == 'cancel':
                return _('Already cancelled')
            if move.state not in ('posted', 'draft'):
                return _('Cannot cancel (%s)', move.state)
        return None

    @api.depends('move_ids', 'operation')
    def _compute_preview(self):
        for wiz in self:
            eligible = wiz.move_ids.filtered(lambda m: not wiz._skip_reason(m))
            skipped = wiz.move_ids - eligible
            wiz.eligible_count = len(eligible)
            wiz.skipped_count = len(skipped)
            verb = _('reset to draft') if wiz.operation == 'draft' \
                else _('cancelled')
            html = _('<p><b>%(n)s</b> record(s) will be %(verb)s.</p>',
                     n=len(eligible), verb=verb)
            if skipped:
                rows = ''.join(
                    '<li>%s &mdash; %s</li>' % (m.display_name,
                                                wiz._skip_reason(m))
                    for m in skipped[:30])
                if len(skipped) > 30:
                    rows += _('<li>… and %s more</li>', len(skipped) - 30)
                html += _('<p><b>%(n)s</b> will be skipped:</p><ul>%(rows)s</ul>',
                          n=len(skipped), rows=rows)
            wiz.preview = html

    def action_confirm(self):
        self.ensure_one()
        verb = _('reset to draft') if self.operation == 'draft' \
            else _('cancelled')
        # Ineligible records are filtered out up front; the rest are processed
        # with Odoo's standard methods (the transaction rolls back on error).
        eligible = self.move_ids.filtered(lambda m: not self._skip_reason(m))
        skipped = len(self.move_ids) - len(eligible)
        if self.operation == 'draft':
            eligible.button_draft()
        else:
            # Reset to draft first, then cancel — mirrors the standard manual
            # flow rather than cancelling a posted entry directly.
            eligible.filtered(lambda m: m.state == 'posted').button_draft()
            eligible.button_cancel()
        if eligible:
            body = _('Bulk operation: %s.', verb)
            if self.reason:
                body += _(' Reason: %s', self.reason)
            for move in eligible:
                move.message_post(body=body)
        message = _('%(n)s record(s) %(verb)s.', n=len(eligible), verb=verb)
        if skipped:
            message += _(' %s skipped.', skipped)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Reset to Draft') if self.operation == 'draft'
                else _('Cancel Invoices'),
                'message': message,
                'type': 'success' if not skipped else 'warning',
                'sticky': bool(skipped),
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }
