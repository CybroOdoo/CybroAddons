# -- coding: utf-8 --
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import fields, models, _
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    """Inherit manufacturing order to add some function """
    _inherit = 'mrp.production'

    def checking_access(self, rec):
        """Warning for cancel button in action"""
        if self.state == 'done':
            rec.action_cancel_manufacturing_order()
        else:
            raise UserError(_(
                "You cannot cancel an order that is not in Done state!"))

    def action_cancel_manufacturing_order(self):
        """To cancel manufacturing order while clicking the button cancel"""

        finished_moves = self.move_finished_ids.filtered(
            lambda l: l.state == 'done')
        raw_moves = self.move_raw_ids.filtered(lambda l: l.state == 'done')

        # --- Step 1: Reverse finished product (remove from destination, return to WIP) ---
        for move in finished_moves:
            self._reverse_stock_quant(
                product=move.product_id,
                qty=move.product_qty,
                from_location=move.location_dest_id,  # deduct from where it was put
                to_location=move.location_id,  # return to where it came from
                lot=(move.move_line_ids.mapped('lot_id')[:1]
                     if move.has_tracking != 'none' else False)
            )

        # --- Step 2: Reverse raw material moves (return components to source) ---
        for move in raw_moves:
            self._reverse_stock_quant(
                product=move.product_id,
                qty=move.product_qty,
                from_location=move.location_dest_id,  # deduct from consumption location
                to_location=move.location_id,  # return to component source
                lot=(move.move_line_ids.mapped('lot_id')[:1]
                     if move.has_tracking != 'none' else False)
            )

        # --- Step 3: Cancel workorders ---
        workorders = self.sudo().mapped('workorder_ids')
        if workorders:
            workorders.write({'state': 'cancel'})

        # --- Step 4: Cancel all moves and the production order ---
        (finished_moves | raw_moves).sudo().write({'state': 'cancel'})
        (finished_moves | raw_moves).mapped('move_line_ids').sudo().write({'state': 'cancel'})
        self.write({'state': 'cancel'})

    def _reverse_stock_quant(self, product, qty, from_location, *,
                             to_location, lot=False):
        """
        Directly and safely adjust stock.quant:
        - Deduct qty from from_location
        - Add qty to to_location
        """
        stock_quant = self.env['stock.quant'].sudo()

        domain_from = [
            ('product_id', '=', product.id),
            ('location_id', '=', from_location.id),
        ]
        domain_to = [
            ('product_id', '=', product.id),
            ('location_id', '=', to_location.id),
        ]
        if lot:
            domain_from += [('lot_id', '=', lot.id)]
            domain_to += [('lot_id', '=', lot.id)]

        # Deduct from source
        quant_from = stock_quant.search(domain_from, limit=1)
        if quant_from:
            quant_from.quantity -= qty
        else:
            stock_quant.create([{
                'product_id': product.id,
                'location_id': from_location.id,
                'lot_id': lot.id if lot else False,
                'quantity': -qty,
            }])

        # Add to destination
        quant_to = stock_quant.search(domain_to, limit=1)
        if quant_to:
            quant_to.quantity += qty
        else:
            stock_quant.create([{
                'product_id': product.id,
                'location_id': to_location.id,
                'lot_id': lot.id if lot else False,
                'quantity': qty,
            }])
