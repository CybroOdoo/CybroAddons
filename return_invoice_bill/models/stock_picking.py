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


class StockPicking(models.Model):
    """This class extends the 'stock.picking' model to add a method for
    retrieving credit notes and debit notes related
    to the picking, and generating actions for viewing them."""
    _inherit = 'stock.picking'

    picking_type_name = fields.Char(string='Picking Type Name',
                                    help='Name of picking type')
    return_invoice_count = fields.Char(string="Counts",
                                       compute='_compute_return_invoice_count',
                                       help="counts of return invoices")
    is_paid = fields.Boolean(string='Is Paid',
                             help='Value will be True when order has paid '
                                  'otherwise False.')

    @api.model
    def create(self, vals):
        """This method overrides the default create method to set the
        'picking_type_name' field based on the 'picking_type_id' field
        before creating the record."""

        self.picking_type_name = self.picking_type_id.name
        return super(StockPicking, self).create(vals)

    def action_get_credit_note(self):
        """Generates an action to view reversal credit notes
         based on the context."""
        self.ensure_one()
        credit_notes = self.sale_id.invoice_ids.filtered(
            lambda x: x.move_type == 'out_refund')
        return {
            'type': 'ir.actions.act_window',
            'name': _(
                'Reversal of Credit Note: %s') % self.sale_id.invoice_ids.filtered(
                lambda x: x.move_type == 'out_invoice').name,
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', credit_notes.ids)],
        }

    def action_get_debit_note(self):
        """Generates an action to view reversal  debit notes
                based on the context."""
        debit_notes = self.purchase_id.invoice_ids.filtered(
            lambda x: x.move_type == 'in_refund')
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _(
                'Reversal of Debit Note: %s') % self.purchase_id.invoice_ids.filtered(
                lambda x: x.move_type == 'in_invoice').name,
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', debit_notes.ids)]
        }

    @api.depends('return_invoice_count')
    def _compute_return_invoice_count(self):
        self.return_invoice_count = self.return_count
