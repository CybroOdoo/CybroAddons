# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies (<https://www.cybrosys.com>)
#    Author: Jumana Haseen (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class StockBackorderConfirmation(models.TransientModel):
    """This class inherits 'stock.backorder.confirmation' and adds
    required fields """
    _inherit = 'stock.backorder.confirmation'

    stock_id = fields.Many2one('stock.picking', setring="Stock",
                               help="Stock")

    def process(self):
        """Initialize variables to store pickings to be done and not to be done
                Iterate through backorder_confirmation_line_ids to categorize pickings,
                 Get pickings to be validated from the context,Retrieve pickings to
                 validate from the context,If there are pickings_not_to_do,
                 check quantities and update context, If pickings_to_validate
                 are not auto-generated, create Inter company transfer"""
        pickings_to_do = self.env['stock.picking']
        pickings_not_to_do = self.env['stock.picking']
        for line in self.backorder_confirmation_line_ids:
            if line.to_backorder is True:
                pickings_to_do |= line.picking_id
            else:
                pickings_not_to_do |= line.picking_id
        pickings_to_validate = self.env.context.get(
            'button_validate_picking_ids')
        if pickings_to_validate:
            pickings_to_validate = self.env['stock.picking'].browse(
                pickings_to_validate).with_context(skip_backorder=True)
            if pickings_not_to_do:
                self._check_less_quantities_than_expected(pickings_not_to_do)
                pickings_to_validate = pickings_to_validate.with_context(
                    picking_ids_not_to_backorder=pickings_not_to_do.ids)
            result_validate = pickings_to_validate.button_validate()
            result_transfer = ''
            if not pickings_to_validate.auto_generated:
                result_transfer = pickings_to_validate.create_intercompany_transfer()
                pickings_to_validate.write(
                    {'is_backorder_button_clicked': True})
            return result_validate, result_transfer
        return True

    def process_cancel_backorder(self):
        """ Retrieve pickings to be validated from the context,If
        pickings_to_validate_ids is specified, validate and cancel backorders"""
        pickings_to_validate_ids = self.env.context.get(
            'button_validate_picking_ids')
        if pickings_to_validate_ids:
            pickings_to_validate = self.env['stock.picking'].browse(
                pickings_to_validate_ids)
            self._check_less_quantities_than_expected(pickings_to_validate)
            result_validate = pickings_to_validate.with_context(
                skip_backorder=True,
                picking_ids_not_to_backorder=self.pick_ids.ids).button_validate()
            result_transfer = ''
            if not pickings_to_validate.auto_generated:
                result_transfer = pickings_to_validate.create_intercompany_transfer()
            return result_validate, result_transfer
        return True
