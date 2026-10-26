#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import _, fields, models


class AccountMove(models.Model):
    """Extends Customer Invoice with waste management monthly billing run linkage."""
    _inherit = 'account.move'

    billing_run_id = fields.Many2one(
        'wm.monthly.billing.run',
        string='Monthly Billing Run',
        readonly=True,
        ondelete='set null',
        copy=False,
        help="The monthly billing run that generated this consolidated invoice.",
    )

    def button_cancel(self):
        """Cancelling an invoice releases what it had billed, so the orders and
        events are not left marked as billed with no invoice behind them."""
        res = super().button_cancel()
        self._release_billing_links()
        return res

    def unlink(self):
        """Deleting a draft invoice also releases what it had billed."""
        self._release_billing_links(self)
        return super().unlink()

    def _release_billing_links(self, moves=None):
        """Free the collection orders (monthly billing run or direct invoice)
        and the ad-hoc billable events whose invoice has been cancelled or
        deleted.

        :param moves: invoices to release regardless of their state (used on
            deletion); by default only the cancelled invoices of ``self``.
        """
        cancelled = moves if moves is not None else self.filtered(lambda move: move.state == 'cancel')
        if not cancelled:
            return
        run_lines = self.env['wm.monthly.billing.run.line'].sudo().search([
            ('invoice_id', 'in', cancelled.ids), ('state', '=', 'billed')])
        if run_lines:
            run_lines.collection_order_ids.write({'billing_run_line_id': False})
            run_lines.write({
                'state': 'draft',
                'note': _("Invoice cancelled: the orders were released and can be billed again."),
            })
        direct_orders = self.env['wm.collection.order'].sudo().search([
            ('direct_invoice_id', 'in', cancelled.ids)])
        if direct_orders:
            direct_orders.write({'direct_invoice_id': False})
        if 'wm.billable.event' in self.env:
            events = self.env['wm.billable.event'].sudo().search([
                ('invoice_id', 'in', cancelled.ids), ('state', '=', 'invoiced')])
            if events:
                events.write({'state': 'confirmed', 'invoice_id': False, 'invoice_line_id': False})
