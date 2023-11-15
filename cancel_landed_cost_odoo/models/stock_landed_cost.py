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
from odoo import fields, models


class StockLandedCost(models.Model):
    """Inherits 'stock.landed.cost' model to add additional functionality
    related to cancelling and resetting landed cost records.

    Methods:
        action_landed_cost_cancel: Cancels the landed cost record by deleting
        its associated accounting entries, stock valuation, and changes state
        to 'cancelled.

        action_landed_cost_reset_and_cancel: Resets the landed cost record by
        deleting its associated accounting entries and stock valuation.
        It changes the state back to 'draft'.

        action_landed_cost_cancel_and_delete: Deletes the landed cost record by
        deleting its associated accounting entries and stock valuation. It also
        deletes the Landed cost record.

        action_landed_cost_cancel_form: Cancels the landed cost record and
        deletes its associated accounting entries and stock valuation.
        It also creates two entries to revert back to the original cost price,
        which are also deleted in the process.

    """
    _inherit = 'stock.landed.cost'

    is_cancel = fields.Boolean(string='Cancel', default=False,
                               help='If the user clicks the "Cancel" button'
                                    'once, it will hide the button and make'
                                    'it invisible.')

    def action_landed_cost_cancel(self):
        """Cancels the landed cost record by deleting its associated
        accounting entries, stock valuation, and changes state to 'cancelled'.

         Additionally, it reverts the original cost price by creating two
         entries, which are also deleted in the process.
        """
        for rec in self:
            for line in rec.valuation_adjustment_lines.filtered(
                    lambda line: line.move_id):
                product = line.move_id.product_id
                if product.cost_method == 'average':
                    original_price = product.standard_price
                    new_price = product.standard_price - line.additional_landed_cost
                    product.write({'standard_price': new_price})
                    stock_valuation_layer = self.env['stock.valuation.layer'] \
                        .search([('product_id', '=', product.id),
                                 ('description', '=', f'Product value manually '
                                                      f'modified (from {original_price} to {new_price})')],
                                limit=1)
                    if stock_valuation_layer:
                        stock_valuation_layer.account_move_id.button_draft()
                        stock_valuation_layer.account_move_id.sudo().unlink()
                        stock_valuation_layer.sudo().unlink()
            if rec.account_move_id:
                account_id = rec.account_move_id
                account_move_ids = account_id.line_ids
                if account_move_ids:
                    account_id.sudo().write(
                        {'state': 'draft', 'name': 'Delete Sequence Number'})
                    account_move_ids.sudo().unlink()
                    account_id.sudo().unlink()
            if rec.valuation_adjustment_lines:
                rec.valuation_adjustment_lines.unlink()
            if rec.stock_valuation_layer_ids:
                rec.stock_valuation_layer_ids.sudo().unlink()
            rec.write({'state': 'cancel'})

    def action_landed_cost_reset_and_cancel(self):
        """Resets the landed cost record by deleting its associated accounting
        entries and stock valuation. It changes the state back to 'draft'.

        Additionally, it reverts the original cost price by creating two entries,
        which are also deleted in the process.
        """
        for rec in self:
            for line in rec.valuation_adjustment_lines.filtered(
                    lambda line: line.move_id):
                product = line.move_id.product_id
                if product.cost_method == 'average':
                    original_price = product.standard_price
                    new_price = product.standard_price - line.additional_landed_cost
                    product.write({'standard_price': new_price})
                    stock_valuation_layer = self.env['stock.valuation.layer'] \
                        .search([('product_id', '=', product.id),
                                 ('description', '=', f'Product value manually '
                                                      f'modified (from {original_price} to {new_price})')],
                                limit=1)
                    if stock_valuation_layer:
                        stock_valuation_layer.account_move_id.button_draft()
                        stock_valuation_layer.account_move_id.sudo().unlink()
                        stock_valuation_layer.sudo().unlink()
            if rec.account_move_id:
                account_id = rec.account_move_id
                account_move_ids = account_id.line_ids
                if account_move_ids:
                    account_id.sudo().write(
                        {'state': 'draft', 'name': 'Delete Sequence Number'})
                    account_move_ids.sudo().unlink()
                    account_id.sudo().unlink()
            if rec.valuation_adjustment_lines:
                rec.valuation_adjustment_lines.unlink()
            if rec.stock_valuation_layer_ids:
                rec.sudo().stock_valuation_layer_ids.unlink()
            rec.write({'state': 'draft'})

    def action_landed_cost_cancel_and_delete(self):
        """Deletes the landed cost record by deleting its associated accounting
         entries and stock valuation. It also deletes the Landed cost record.

        Additionally, it reverts the original cost price by creating two
        entries, which are also deleted in the process.
        """
        for rec in self:
            for line in rec.valuation_adjustment_lines.filtered(
                    lambda line: line.move_id):
                product = line.move_id.product_id
                if product.cost_method == 'average':
                    original_price = product.standard_price
                    new_price = product.standard_price - line.additional_landed_cost
                    product.write({'standard_price': new_price})
                    stock_valuation_layer = self.env['stock.valuation.layer'] \
                        .search([('product_id', '=', product.id),
                                 ('description', '=', f'Product value manually '
                                                      f'modified (from {original_price} to {new_price})')],
                                limit=1)
                    if stock_valuation_layer:
                        stock_valuation_layer.account_move_id.button_draft()
                        stock_valuation_layer.account_move_id.sudo().unlink()
                        stock_valuation_layer.sudo().unlink()
            if rec.account_move_id:
                account_id = rec.account_move_id
                account_move_ids = account_id.line_ids
                if account_move_ids:
                    account_id.sudo().write(
                        {'state': 'draft', 'name': 'Delete Sequence Number'})
                    account_move_ids.sudo().unlink()
                    account_id.sudo().unlink()
            if rec.valuation_adjustment_lines:
                rec.valuation_adjustment_lines.unlink()
            if rec.stock_valuation_layer_ids:
                rec.sudo().stock_valuation_layer_ids.unlink()
            rec.write({'state': 'cancel'})
            rec.unlink()

    def action_landed_cost_cancel_form(self):
        """Cancels the landed cost record and deletes its associated
        accounting entries and stock valuation. It also creates two entries
        to revert back to the original cost price, which are also deleted in
        the process.

        The specific action performed depends on the value of the
        'cancel_landed_cost_odoo.land_cost_cancel_modes'
        configuration parameter:
        - 'cancel': Changes the landed cost state to 'cancel' and sets
        the 'is_cancel' flag to True.
        - 'cancel_draft': Changes the landed cost state to 'draft'
        and sets the 'is_cancel' flag to False.
        - 'cancel_delete': Deletes the landed cost record and returns an
        action to open the Landed Cost tree view.
        """
        for rec in self:
            for line in rec.valuation_adjustment_lines.filtered(
                    lambda line: line.move_id):
                product = line.move_id.product_id
                if product.cost_method == 'average':
                    original_price = product.standard_price
                    new_price = product.standard_price - line.additional_landed_cost
                    product.write({'standard_price': new_price})
                    stock_valuation_layer = self.env['stock.valuation.layer'] \
                        .search([('product_id', '=', product.id),
                                 ('description', '=', f'Product value manually '
                                                      f'modified (from {original_price} to {new_price})')],
                                limit=1)
                    if stock_valuation_layer:
                        stock_valuation_layer.account_move_id.button_draft()
                        stock_valuation_layer.account_move_id.sudo().unlink()
                        stock_valuation_layer.sudo().unlink()
        if self.account_move_id:
            account_id = self.account_move_id
            account_move_ids = account_id.line_ids
            if account_move_ids:
                account_id.sudo().write(
                    {'state': 'draft', 'name': 'Delete Sequence Number'})
                account_move_ids.sudo().unlink()
                account_id.sudo().unlink()
        if self.valuation_adjustment_lines:
            self.valuation_adjustment_lines.unlink()
        if self.stock_valuation_layer_ids:
            self.sudo().stock_valuation_layer_ids.unlink()
        landed_mode = self.env['ir.config_parameter'].sudo().get_param(
            'cancel_landed_cost_odoo.land_cost_cancel_modes')
        if landed_mode == 'cancel':
            self.write({'state': 'cancel'})
            self.is_cancel = True
        if landed_mode == 'cancel_draft':
            self.write({'state': 'draft'})
            self.is_cancel = False
        if landed_mode == 'cancel_delete':
            self.write({'state': 'cancel'})
            self.unlink()
            return {
                'name': 'Landed Cost',
                'type': 'ir.actions.act_window',
                'res_model': 'stock.landed.cost',
                'view_mode': 'tree,form',
                'target': 'current'
            }
