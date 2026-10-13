# -*- coding: utf-8 -*-
##############################################################################
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
##############################################################################
from odoo import api, fields, models, _


class StockPicking(models.Model):
    """This class extends the 'stock.picking' model to add a method for
    retrieving credit notes and debit notes related
    to the picking, and generating actions for viewing them."""
    _inherit = 'stock.picking'

    picking_type_name = fields.Char(related='picking_type_id.name',
                                    string='Picking Type Name',
                                    readonly=True,
                                    help='Name of picking type')
    return_invoice_count = fields.Integer(string="Counts",
                                          compute='_compute_return_invoice_count',
                                          help="Counts of return invoices")
    is_paid = fields.Boolean(string='Is Paid',
                             help='Value will be True when order has paid '
                                  'otherwise False.')

    def _compute_return_invoice_count(self):
        for record in self:
            if record.picking_type_code == 'outgoing' and record.sale_id:
                record.return_invoice_count = len(
                    record.sale_id.invoice_ids.filtered(lambda x: x.move_type == 'out_refund')
                )
            elif record.picking_type_code == 'incoming' and record.purchase_id:
                record.return_invoice_count = len(
                    record.purchase_id.invoice_ids.filtered(lambda x: x.move_type == 'in_refund')
                )
            else:
                record.return_invoice_count = 0

    def action_get_credit_note(self):
        """Generates an action to view reversal credit notes."""
        self.ensure_one()
        credit_notes = self.sale_id.invoice_ids.filtered(
            lambda x: x.move_type == 'out_refund')
        action = {
            'type': 'ir.actions.act_window',
            'name': _('Credit Notes'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', credit_notes.ids)],
        }
        if len(credit_notes) == 1:
            action['view_mode'] = 'form'
            action['res_id'] = credit_notes.id
        return action

    def action_get_debit_note(self):
        """Generates an action to view reversal debit notes."""
        self.ensure_one()
        debit_notes = self.purchase_id.invoice_ids.filtered(
            lambda x: x.move_type == 'in_refund')
        action = {
            'type': 'ir.actions.act_window',
            'name': _('Debit Notes'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', debit_notes.ids)],
        }
        if len(debit_notes) == 1:
            action['view_mode'] = 'form'
            action['res_id'] = debit_notes.id
        return action
