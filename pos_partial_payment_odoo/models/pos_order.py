# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anfas Faisal K (odoo@cybrosys.info)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.osv.expression import AND, _logger
from odoo.tools.float_utils import float_round, float_is_zero, float_compare

try:
    # Optional: use psycopg2 constants if available for more robust checks
    from psycopg2 import errors as pg_errors
except Exception:
    pg_errors = None


class PosOrder(models.Model):
    """
    This class extends the 'pos.order' model to introduce additional
    functionality related to partial payments and order management in the
    Point of Sale (POS) system.

    It adds fields and methods for tracking partial payments, computing due
    amounts, and marking orders as paid. The class also includes a method to
    search for partial orders based on specified criteria.

    """
    _inherit = 'pos.order'

    is_partial_payment = fields.Boolean(string="Is Partial Payment",
                                        default=False,
                                        help="Flag indicating whether this POS "
                                             "order is a partial payment.")
    due_amount = fields.Float(string="Amount Due",
                              compute='_compute_due_amount',
                              store=True,
                              help="The amount remaining to be paid for this"
                                   "POS order.")

    @api.depends('amount_total', 'amount_paid')
    def _compute_due_amount(self):
        """
        Compute the due amount for the POS order.

        This method computes the difference between the total amount and the amount paid
        for the POS order and updates the 'due_amount' field accordingly.
        """
        for record in self:
            record.due_amount = record.amount_total - record.amount_paid

    def _order_fields(self, ui_order):
        """
        Prepare dictionary for create method

        This method prepares a dictionary of order fields for creating a POS order based
        on the data from the user interface (UI) order.
        """
        result = super()._order_fields(ui_order)
        result['is_partial_payment'] = ui_order.get('is_partial_payment')
        return result

    def action_pos_order_paid(self):
        """
        Mark the POS order as paid. This method marks the POS order as
        paid and ensures that it is fully paid based on the partial
        payment.
        """
        self.ensure_one()
        # compute the total to compare taking into account cash rounding config on the order's config
        if (not self.config_id.cash_rounding) or (
                self.config_id.only_round_cash_method and not any(
                p.payment_method_id.is_cash_count for p in self.payment_ids)):
            total = self.amount_total
        else:
            # use the configured rounding method value and rounding algorithm if present
            precision_rounding = getattr(self.config_id.rounding_method,
                                         'rounding',
                                         self.currency_id.rounding) or self.currency_id.rounding
            total = float_round(self.amount_total,
                                precision_rounding=precision_rounding,
                                rounding_method=getattr(
                                    self.config_id.rounding_method,
                                    'rounding_method', None))

        isPaid = float_is_zero(total - self.amount_paid,
                               precision_rounding=self.currency_id.rounding)

        # Only allow marking as paid for partial payments when this order specifically is flagged as partial payment
        if not isPaid:
            # previously code flipped isPaid True if any pos_config.partial_payment existed,
            # which caused incorrect marking. Instead: only allow if the *current order* is a partial payment order.
            if self.is_partial_payment:
                isPaid = True

        # Keep the cash rounding tolerance check if still not isPaid (original behavior)
        if not isPaid and not self.config_id.cash_rounding:
            raise UserError(_("Order %s is not fully paid.") % (self.name,))
        elif not isPaid and self.config_id.cash_rounding:
            currency = self.currency_id
            if self.config_id.rounding_method.rounding_method == "HALF-UP":
                maxDiff = currency.round(
                    self.config_id.rounding_method.rounding / 2)
            else:
                maxDiff = currency.round(
                    self.config_id.rounding_method.rounding)
            diff = currency.round(self.amount_total - self.amount_paid)
            if not abs(diff) <= maxDiff:
                raise UserError(_("Order %s is not fully paid.") % (self.name,))

        self.write({'state': 'paid'})
        return True

    @api.model
    def search_partial_order_ids(self, config_id, domain, limit, offset):
        """Search for 'partial' orders that satisfy the given domain,
        limit and offset."""
        default_domain = ['&', ('config_id', '=', config_id),
                          ('is_partial_payment', '=', True), '!', '|',
                          ('state', '=', 'draft'), ('state', '=', 'cancelled')]
        real_domain = AND([domain, default_domain])
        ids = self.search(AND([domain, default_domain]), limit=limit,
                          offset=offset).ids
        totalCount = self.search_count(real_domain)
        return {'ids': ids, 'totalCount': totalCount}

    def _create_invoice(self, move_vals):
        """
        Create the account.move (invoice) and apply cash rounding adjustments
        ONLY if the order is effectively paid within rounding tolerance.

        NOTE: do NOT call super()._create_invoice(move_vals) because the original
        implementation already contains rounding logic that would run unconditionally.
        """
        self.ensure_one()

        # Create the invoice move directly (same as original POS code)
        new_move = self.env['account.move'].sudo().with_company(
            self.company_id).with_context(
            default_move_type=move_vals['move_type']
        ).create(move_vals)

        # Post a message on the invoice linking to the POS order
        message = _(
            "This invoice has been created from the point of sale session: %s",
            self._get_html_link(),
        )
        new_move.message_post(body=message)

        # If no cash rounding configured for the POS, nothing to do
        if not self.config_id.cash_rounding:
            return new_move

        # determine rounding precision
        rounding_precision = new_move.currency_id.rounding or self.currency_id.rounding or 0.0

        # Determine whether the order is paid within rounding tolerance
        is_paid_within_rounding = float_compare(self.amount_paid,
                                                self.amount_total,
                                                precision_rounding=rounding_precision) >= 0

        # If only_round_cash_method is set, require at least one cash payment
        if self.config_id.only_round_cash_method and not any(
                p.payment_method_id.is_cash_count for p in self.payment_ids):
            apply_rounding = False
        else:
            apply_rounding = is_paid_within_rounding

        # If not applying rounding, return the invoice as-is
        if not apply_rounding:
            return new_move

        # Compute rounding applied and adjust rounding + receivable lines
        rounding_applied = float_round(self.amount_paid - self.amount_total,
                                       precision_rounding=rounding_precision)

        rounding_line_difference = 0.0
        rounding_line = new_move.line_ids.filtered(
            lambda line: line.display_type == 'rounding')

        if rounding_line and rounding_line.filtered(lambda l: l.debit > 0):
            rl = rounding_line.filtered(lambda l: l.debit > 0)[0]
            rounding_line_difference = rl.debit + rounding_applied
        elif rounding_line and rounding_line.filtered(lambda l: l.credit > 0):
            rl = rounding_line.filtered(lambda l: l.credit > 0)[0]
            rounding_line_difference = -rl.credit + rounding_applied
        else:
            rounding_line_difference = rounding_applied

        if rounding_applied:
            if rounding_applied > 0.0:
                account_id = new_move.invoice_cash_rounding_id.loss_account_id.id
            else:
                account_id = new_move.invoice_cash_rounding_id.profit_account_id.id

            if rounding_line:
                if rounding_line_difference:
                    rounding_line.with_context(skip_invoice_sync=True,
                                               check_move_validity=False).write(
                        {
                            'debit': rounding_applied < 0.0 and -rounding_applied or 0.0,
                            'credit': rounding_applied > 0.0 and rounding_applied or 0.0,
                            'account_id': account_id,
                            'price_unit': rounding_applied,
                        })
            else:
                # create the rounding line
                self.env['account.move.line'].with_context(
                    skip_invoice_sync=True, check_move_validity=False).create({
                    'balance': -rounding_applied,
                    'quantity': 1.0,
                    'partner_id': new_move.partner_id.id,
                    'move_id': new_move.id,
                    'currency_id': new_move.currency_id.id,
                    'company_id': new_move.company_id.id,
                    'company_currency_id': new_move.company_id.currency_id.id,
                    'display_type': 'rounding',
                    'sequence': 9999,
                    'name': self.config_id.rounding_method.name,
                    'account_id': account_id,
                })
        else:
            if rounding_line:
                rounding_line.with_context(skip_invoice_sync=True,
                                           check_move_validity=False).unlink()

        if rounding_line_difference:
            existing_terms_line = new_move.line_ids.filtered(
                lambda line: line.account_id.account_type in (
                    'asset_receivable', 'liability_payable'))
            if existing_terms_line:
                if existing_terms_line.debit > 0:
                    existing_terms_line_new_val = float_round(
                        existing_terms_line.debit + rounding_line_difference,
                        precision_rounding=rounding_precision)
                else:
                    existing_terms_line_new_val = float_round(
                        -existing_terms_line.credit + rounding_line_difference,
                        precision_rounding=rounding_precision)
                existing_terms_line.with_context(skip_invoice_sync=True).write({
                    'debit': existing_terms_line_new_val > 0.0 and existing_terms_line_new_val or 0.0,
                    'credit': existing_terms_line_new_val < 0.0 and -existing_terms_line_new_val or 0.0,
                })

        return new_move

