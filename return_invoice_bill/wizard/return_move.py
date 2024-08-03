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
from odoo import fields, models
from odoo.exceptions import ValidationError


class ReturnMove(models.TransientModel):
    """Transient model for ,enter the cancel reason credit and debit note."""
    _name = 'return.move'
    _description = 'Return Move'

    reason = fields.Char(string='Reason',
                         help='Specify the reason for credit note',
                         required=True)

    def action_apply_reverse_entry(self):
        """Return the invoice or bill and create credit and debit note."""
        active_id = self.env.context.get('active_id')
        if not active_id:
            raise ValidationError("No active_id found in the context.")
        return_id = self.env['stock.return.picking'].browse(active_id)
        new_picking_id = return_id.create_returns()
        new_picking = self.env['stock.picking'].browse(int(new_picking_id['res_id']))
        picking_id = return_id.picking_id
        sale_invoice_ids = picking_id.sale_id.invoice_ids
        purchase_invoice_ids = picking_id.purchase_id.invoice_ids
        sale_all_posted = all(element == 'posted' for element in sale_invoice_ids.mapped('state')) if sale_invoice_ids else False
        purchase_all_posted = all(element == 'posted' for element in purchase_invoice_ids.mapped('state')) if purchase_invoice_ids else False
        if sale_all_posted or purchase_all_posted:
            new_picking.button_validate()
            if picking_id.sale_id:
                action = self.env['sale.advance.payment.inv'].create({'sale_order_ids': [fields.Command.link(picking_id.sale_id.id)]})
                invoice = action.create_invoices()
                move_id = self.env['account.move'].browse(invoice.get('res_id'))
            else:
                invoice = picking_id.purchase_id.action_create_invoice()
                move_id = self.env['account.move'].browse(invoice.get('res_id'))
                move_id.invoice_date = fields.Date.today()
            move_id.action_post()
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'account.move',
                'target': 'current',
                'res_id': move_id.id,
            }
        else:
            raise ValidationError(
                "The selected picking should have at least one posted invoice.")
