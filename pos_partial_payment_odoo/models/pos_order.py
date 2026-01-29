# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mruthul Raj(odoo@cybrosys.info)
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
from odoo.osv.expression import AND
from odoo.tools import float_round, float_is_zero


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
        # TODO: add support for mix of cash and non-cash payments when both cash_rounding and only_round_cash_method are True
        if not self.config_id.cash_rounding \
                or self.config_id.only_round_cash_method \
                and not any(
            p.payment_method_id.is_cash_count for p in self.payment_ids):
            total = self.amount_total
        else:
            total = float_round(self.amount_total,
                                precision_rounding=self.config_id.rounding_method.rounding,
                                rounding_method=self.config_id.rounding_method.rounding_method)
        isPaid = float_is_zero(total - self.amount_paid,
                               precision_rounding=self.currency_id.rounding)
        if not isPaid:
            pos_config = self.env['pos.config'].search([])
            for shop in pos_config:
                if shop.partial_payment:
                    isPaid = True
        if not isPaid and not self.config_id.cash_rounding:
            raise UserError(_("Order %s is not fully paid.", self.name))
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
                raise UserError(_("Order %s is not fully paid.", self.name))
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

    @api.model_create_multi
    def create(self, vals_list):
        """Super create function"""
        if vals_list[0]['amount_paid'] < vals_list[0]['amount_total']:
            vals_list[0]['is_partial_payment'] = True
        return super(PosOrder, self).create(vals_list)
