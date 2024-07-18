# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from collections import defaultdict
from odoo import models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class StockMove(models.Model):
    """ Class to inherit stock_move to update the product price """
    _inherit = "stock.move"

    def product_price_update_before_done(self, forced_qty=None):

        tmpl_dict = defaultdict(lambda: 0.0)
        # adapt standard price on incomming moves if the product cost_method is 'average'
        std_price_update = {}
        for move in self.filtered(
                lambda move: move._is_in() and move.with_company(
                    move.company_id).product_id.cost_method == 'average'):
            product_tot_qty_available = move.product_id.sudo().with_company(
                move.company_id).quantity_svl + tmpl_dict[
                                            move.product_id.id]
            rounding = move.product_id.uom_id.rounding

            valued_move_lines = move._get_in_move_lines()
            qty_done = 0
            for valued_move_line in valued_move_lines:
                qty_done += valued_move_line.product_uom_id._compute_quantity(
                    valued_move_line.quantity, move.product_id.uom_id)

            qty = forced_qty or qty_done
            if float_is_zero(product_tot_qty_available,
                             precision_rounding=rounding):
                new_std_price = move._get_price_unit()
            elif float_is_zero(product_tot_qty_available + move.product_qty,
                               precision_rounding=rounding) or \
                    float_is_zero(product_tot_qty_available + qty,
                                  precision_rounding=rounding):
                new_std_price = move._get_price_unit()
            else:
                # Get the standard price
                amount_unit = std_price_update.get((move.company_id.id,
                                                    move.product_id.id)) or move.product_id.with_company(
                    move.company_id).standard_price
                new_std_price = ((
                                         amount_unit * product_tot_qty_available) + (
                                         move._get_price_unit() * qty)) / (
                                        product_tot_qty_available + qty)

            tmpl_dict[move.product_id.id] += qty_done
            # Write the standard price, as SUPERUSER_ID because a warehouse manager may not have the right to write on products
            move.product_id.with_company(move.company_id.id).with_context(
                disable_auto_svl=True).sudo().write(
                {'standard_price': new_std_price})
            std_price_update[
                move.company_id.id, move.product_id.id] = new_std_price

        # adapt standard price on incomming moves if the product cost_method
        # is 'fifo'
        for move in self.filtered(lambda move:
                                  move.with_company(
                                      move.company_id).product_id.cost_method == 'fifo'
                                  and float_is_zero(
                                      move.product_id.sudo().quantity_svl,
                                      precision_rounding=move.product_id.uom_id.rounding)):
            move.product_id.with_company(move.company_id.id).sudo().write(
                {'standard_price': move._get_price_unit()})
            # Add new costing method for 'last' with real-time or
            # manual_periodic valuation
        # Filter moves based on conditions
        for move in self.filtered(lambda move: move.with_company(
                move.company_id).product_id.cost_method == 'last' and
                                               (
                                                       move.product_id.valuation == 'real_time' or move.product_id.valuation == 'manual_periodic')):
            # Get the new standard price for the move
            new_std_price = move._get_price_unit()  # Presumably retrieves incoming move price

            # Retrieve product details for the move
            products = self.env['product.product'].browse(
                move.product_id.id)

            # Determine the account ID for price differences
            account_id = (
                    products.property_account_creditor_price_difference.id
                    or products.categ_id.property_account_creditor_price_difference_categ.id)

            # Check if account ID is not set, raise an error
            if not account_id:
                raise UserError(
                    _('Configuration error. Please configure the price '
                      'difference account on the product or its category '
                      'to process this operation.'))
            # products.create_price_change_account_move(new_std_price,
            #                                                       account_id,
            #                                                       move.company_id.id,
            #                                                       move.origin)
            # Update the standard price for the product
            move.product_id.with_company(move.company_id.id).with_context(
                disable_auto_svl=True).sudo().write(
                {'standard_price': new_std_price})
