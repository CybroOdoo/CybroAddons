# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import api, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class StockMove(models.Model):
    _inherit = "stock.move"


    def product_price_update_before_done(self, forced_qty=None):
        tmpl_dict = defaultdict(lambda: 0.0)
        # adapt standard price on incomming moves if the product cost_method is 'average'
        std_price_update = {}
        for move in self.filtered(lambda move: move.location_id.usage in ('supplier', 'production') and move.product_id.cost_method in ('average', 'last')):
            product_tot_qty_available = move.product_id.qty_available + tmpl_dict[move.product_id.id]
            rounding = move.product_id.uom_id.rounding

            qty_done = 0.0
            if float_is_zero(product_tot_qty_available, precision_rounding=rounding):
                new_std_price = move._get_price_unit()
            elif float_is_zero(product_tot_qty_available + move.product_qty, precision_rounding=rounding) or \
                    float_is_zero(product_tot_qty_available + qty_done, precision_rounding=rounding):
                new_std_price = move._get_price_unit()
            else:
                # Get the standard price
                if move.product_id.cost_method == 'average':
                    amount_unit = std_price_update.get(
                        (move.company_id.id, move.product_id.id)) or move.product_id.standard_price
                    qty_done = move.product_uom._compute_quantity(move.quantity_done, move.product_id.uom_id)
                    qty = forced_qty or qty_done
                    new_std_price = ((amount_unit * product_tot_qty_available) + (move._get_price_unit() * qty)) / (product_tot_qty_available + qty_done)
            if move.product_id.cost_method == 'last' and move.product_id.valuation == 'real_time':
                new_std_price = move._get_price_unit()
                products = self.env['product.product'].browse(move.product_id.id)
                account_id = products.property_account_creditor_price_difference.id or products.categ_id.property_account_creditor_price_difference_categ.id
                if not account_id:
                    raise UserError(_('Configuration error. Please configure the price difference account on the product or its category to process this operation.'))
                products.create_price_change_account_move(new_std_price, account_id, move.company_id.id, move.origin)
            tmpl_dict[move.product_id.id] += qty_done
            # Write the standard price, as SUPERUSER_ID because a warehouse manager may not have the right to write on products
            move.product_id.with_context(force_company=move.company_id.id).sudo().write({'standard_price': new_std_price})
            std_price_update[move.company_id.id, move.product_id.id] = new_std_price


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'


    def write(self, vals):
        """ When editing a done stock.move.line, we impact the valuation. Users may increase or
        decrease the `qty_done` field. There are three cost method available: standard, average
        and fifo. We implement the logic in a similar way for standard and average: increase
        or decrease the original value with the standard or average price of today. In fifo, we
        have a different logic wheter the move is incoming or outgoing. If the move is incoming, we
        update the value and remaining_value/qty with the unit price of the move. If the move is
        outgoing and the user increases qty_done, we call _run_fifo and it'll consume layer(s) in
        the stack the same way a new outgoing move would have done. If the move is outoing and the
        user decreases qty_done, we either increase the last receipt candidate if one is found or
        we decrease the value with the last fifo price.
        """
        if 'qty_done' in vals:
            moves_to_update = {}
            for move_line in self.filtered(
                    lambda ml: ml.state == 'done' and (ml.move_id._is_in() or ml.move_id._is_out())):
                moves_to_update[move_line.move_id] = vals['qty_done'] - move_line.qty_done

            for move_id, qty_difference in moves_to_update.items():
                move_vals = {}
                if move_id.product_id.cost_method in ['standard', 'average', 'last']:
                    correction_value = qty_difference * move_id.product_id.standard_price
                    if move_id._is_in():
                        move_vals['value'] = move_id.value + correction_value
                    elif move_id._is_out():
                        move_vals['value'] = move_id.value - correction_value
                else:
                    if move_id._is_in():
                        correction_value = qty_difference * move_id.price_unit
                        new_remaining_value = move_id.remaining_value + correction_value
                        move_vals['value'] = move_id.value + correction_value
                        move_vals['remaining_qty'] = move_id.remaining_qty + qty_difference
                        move_vals['remaining_value'] = move_id.remaining_value + correction_value
                    elif move_id._is_out() and qty_difference > 0:
                        correction_value = self.env['stock.move']._run_fifo(move_id, quantity=qty_difference)
                        # no need to adapt `remaining_qty` and `remaining_value` as `_run_fifo` took care of it
                        move_vals['value'] = move_id.value - correction_value
                    elif move_id._is_out() and qty_difference < 0:
                        candidates_receipt = self.env['stock.move'].search(move_id._get_in_domain(), order='date, id desc', limit=1)
                        if candidates_receipt:
                            candidates_receipt.write({
                                'remaining_qty': candidates_receipt.remaining_qty + -qty_difference,
                                'remaining_value': candidates_receipt.remaining_value + (
                                -qty_difference * candidates_receipt.price_unit),
                            })
                            correction_value = qty_difference * candidates_receipt.price_unit
                        else:
                            correction_value = qty_difference * move_id.product_id.standard_price
                        move_vals['value'] = move_id.value - correction_value
                move_id.write(move_vals)

                if move_id.product_id.valuation == 'real_time':
                    move_id.with_context(force_valuation_amount=correction_value, forced_quantity=qty_difference)._account_entry_move()
                if qty_difference > 0:
                    move_id.product_price_update_before_done(forced_qty=qty_difference)
        return super(StockMoveLine, self).write(vals)
