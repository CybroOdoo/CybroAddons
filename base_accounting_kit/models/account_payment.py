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
from odoo import fields, models, _
from odoo.exceptions import UserError


class AccountRegisterPayments(models.TransientModel):
    """Inherits the account.payment.register model to add the new
     fields and functions"""
    _inherit = "account.payment.register"

    bank_reference = fields.Char(string="Bank Reference", copy=False)
    cheque_reference = fields.Char(string="Cheque Reference", copy=False)
    effective_date = fields.Date('Effective Date',
                                 help='Effective date of PDC', copy=False,
                                 default=False)

    def _create_payment_vals_from_wizard(self, batch_result):
        """Carry the PDC/cheque references onto the created payment vals."""
        res = super()._create_payment_vals_from_wizard(batch_result)
        res.update({
            'bank_reference': self.bank_reference,
            'cheque_reference': self.cheque_reference,
            'effective_date': self.effective_date,
        })
        return res

    def _create_payment_vals_from_batch(self, batch_result):
        """Carry the PDC/cheque references onto the created payment vals."""
        res = super()._create_payment_vals_from_batch(batch_result)
        res.update({
            'bank_reference': self.bank_reference,
            'cheque_reference': self.cheque_reference,
            'effective_date': self.effective_date,
        })
        return res


class AccountPayment(models.Model):
    """It inherits the account.payment model for adding new fields
     and functions"""
    _inherit = "account.payment"

    bank_reference = fields.Char(string="Bank Reference", copy=False)
    cheque_reference = fields.Char(string="Cheque Reference",copy=False)
    effective_date = fields.Date('Effective Date',
                                 help='Effective date of PDC', copy=False,
                                 default=False)
    bulk_payment_id = fields.Many2one(
        'account.bulk.payment', string='Bulk Payment', copy=False,
        help="Batch this payment is grouped into for bank processing.")

    def action_add_to_bulk_payment(self):
        """Group the selected payments into a new bulk payment (they must
        share the same journal and payment type)."""
        payments = self or self.browse(self.env.context.get('active_ids', []))
        if not payments:
            raise UserError(_("Select at least one payment."))
        if len(payments.journal_id) != 1 or len(set(payments.mapped(
                'payment_type'))) != 1:
            raise UserError(_(
                "Select payments that share the same journal and type."))
        batch = self.env['account.bulk.payment'].create({
            'journal_id': payments.journal_id.id,
            'batch_type': payments[0].payment_type,
            'payment_method_line_id': payments[0].payment_method_line_id.id,
        })
        payments.write({'bulk_payment_id': batch.id})
        return {
            'name': _('Bulk Payment'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.bulk.payment',
            'view_mode': 'form',
            'res_id': batch.id,
        }

    def open_payment_matching_screen(self):
        """Open the partner's open reconcilable journal items for manual
        matching. (The enterprise 'manual_reconciliation_view' client action is
        not available in Community, so we open the reconcilable move lines.)"""
        self.ensure_one()
        if not self.partner_id:
            raise UserError(_("Payments without a customer can't be matched"))
        partner = self.partner_id.commercial_partner_id
        return {
            'name': _("Matching"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.line',
            'view_mode': 'list,form',
            'domain': [
                ('partner_id', '=', partner.id),
                ('account_id.reconcile', '=', True),
                ('parent_state', '=', 'posted'),
                ('reconciled', '=', False),
                ('company_id', '=', self.company_id.id),
            ],
            'context': {'search_default_partner_id': partner.id},
        }

    def print_checks(self):
        """ Check that the recordset is valid, post any draft payments and
        call do_print_checks() """
        # Since this method can be called via a client_action_multi, we
        # need to make sure the received records are what we expect
        selfs = self.filtered(lambda r:
                              r.payment_method_line_id.code
                              in ['check_printing', 'pdc']
                              and not r.is_sent)
        if len(selfs) == 0:
            raise UserError(_(
                "Payments to print as a checks must have 'Check' "
                "or 'PDC' selected as payment method and "
                "not have already been sent"))
        if any(payment.journal_id != selfs[0].journal_id for payment in selfs):
            raise UserError(_(
                "In order to print multiple checks at once, they "
                "must belong to the same bank journal."))

        if not selfs[0].journal_id.check_manual_sequencing:
            # The wizard asks for the number printed on the first pre-printed
            # check. Order numerically (::BIGINT) and preserve zero-padding —
            # a plain string sort would rank "9" above "10".
            self.env.cr.execute("""
                  SELECT payment.check_number
                    FROM account_payment payment
                   WHERE payment.journal_id = %(journal_id)s
                     AND payment.check_number IS NOT NULL
                ORDER BY payment.check_number::BIGINT DESC
                   LIMIT 1
            """, {'journal_id': selfs[0].journal_id.id})
            last_check_number = (self.env.cr.fetchone() or (False,))[0]
            number_len = len(last_check_number or "")
            next_check_number = f'{int(last_check_number or 0) + 1:0{number_len}}'
            return {
                'name': _('Print Pre-numbered Checks'),
                'type': 'ir.actions.act_window',
                'res_model': 'print.prenumbered.checks',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'payment_ids': selfs.ids,
                    'default_next_check_number': next_check_number,
                }
            }
        else:
            selfs.filtered(lambda r: r.state == 'draft').action_post()
            # ``do_print_checks`` (account_check_printing) marks them as sent
            # and raises a RedirectWarning if no check layout is configured.
            return selfs.do_print_checks()

    # --- PDC post-dating -----------------------------------------------------
    # A post-dated cheque should hit the ledger on its effective (clearing)
    # date, not the payment date. The old ``_prepare_payment_moves`` hook was
    # removed in v16+, so we post-date the generated journal entry through the
    # current move-build/synchronization hooks. Everything else (currency,
    # outstanding accounts) still derives from ``payment.date``.
    def _pdc_accounting_date(self):
        """Effective date for a PDC payment's journal entry, else payment date."""
        self.ensure_one()
        if self.payment_method_line_id.code == 'pdc' and self.effective_date:
            return self.effective_date
        return self.date

    def _get_trigger_fields_to_synchronize(self):
        """Re-sync the move when the PDC effective date changes."""
        return super()._get_trigger_fields_to_synchronize() + ('effective_date',)

    def _prepare_move_line_default_vals(self, write_off_line_vals=None,
                                        force_balance=None):
        line_vals_list = super()._prepare_move_line_default_vals(
            write_off_line_vals=write_off_line_vals, force_balance=force_balance)
        if self.payment_method_line_id.code == 'pdc' and self.effective_date:
            for vals in line_vals_list:
                vals['date_maturity'] = self.effective_date
        return line_vals_list

    def _generate_move_vals(self, write_off_line_vals=None, force_balance=None,
                            line_ids=None):
        move_vals = super()._generate_move_vals(
            write_off_line_vals=write_off_line_vals, force_balance=force_balance,
            line_ids=line_ids)
        move_vals['date'] = self._pdc_accounting_date()
        return move_vals

    def _synchronize_to_moves(self, changed_fields):
        super()._synchronize_to_moves(changed_fields)
        if not any(f in changed_fields
                   for f in self._get_trigger_fields_to_synchronize()):
            return
        for pay in self:
            if pay.move_id and pay.move_id.state != 'posted' \
                    and pay.payment_method_line_id.code == 'pdc' \
                    and pay.effective_date:
                pay.move_id.with_context(skip_invoice_sync=True).write(
                    {'date': pay.effective_date})

    def mark_as_sent(self):
        """Updates the is_move_sent value of the payment model"""
        self.write({'is_sent': True})

    def unmark_as_sent(self):
        """Updates the is_move_sent value of the payment model"""
        self.write({'is_sent': False})
