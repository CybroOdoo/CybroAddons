# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
##############################################################################
from odoo import api, fields, models


class StockReturnPicking(models.TransientModel):
    """Inherited this class to display the view, to add the cancel reason."""
    _inherit = 'stock.return.picking'

    picking_type_name = fields.Char(string='Picking Type Name',
                                    help='Name of the picking type')

    @api.model
    def default_get(self, fields):
        """Override of default_get method to set default values for fields
         in the wizard."""
        result = super(StockReturnPicking, self).default_get(fields)
        active_model = self.env.context['active_model']
        active_id = self.env.context['active_id']
        if active_model == 'stock.picking' and active_id:
            stock_picking = self.env[active_model].browse(active_id)
            result['picking_type_name'] = stock_picking.picking_type_id.name
        return result

    def _update_stock_picking(self):
        """Update the 'is_paid' field of the active stock picking to indicate
        payment. This function is typically called when processing returns with
        credit or debit notes."""
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')

        if active_model == 'stock.picking' and active_id:
            stock_picking = self.env[active_model].browse(active_id)
            stock_picking.is_paid = True

    def _get_return_action(self):
        """
        Retrieve the action for returning a move, specifically for credit notes.
        Returns:
            ir.actions.actions: Action object for returning moves with credit
            notes.
        """
        return self.env["ir.actions.actions"]._for_xml_id("return_invoice_bill.return_move_action")

    def action_returns_with_credit_note(self):
        """
        Perform the action of returning moves with credit notes and update the
        stock picking accordingly.

        Returns:
            ir.actions.actions: Action object for returning moves with credit
            notes.
        """
        self._update_stock_picking()
        return self._get_return_action()

    def action_returns_with_debit_note(self):
        """
        Perform the action of returning moves with debit notes and update the
        stock picking accordingly.

        Returns:
            ir.actions.actions: Action object for returning moves with debit
            notes.
        """
        self._update_stock_picking()
        return self._get_return_action()
