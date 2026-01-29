# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Dhanya Babu (odoo@cybrosys.com)
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
from odoo.exceptions import ValidationError, UserError
from odoo import fields, models, _


class ReturnMove(models.TransientModel):
    """Transient model for ,enter the cancel reason credit and debit note."""
    _name = 'return.move'
    _description = 'Return Move'

    reason = fields.Char(string='Reason',
                         help='Specify the reason for credit note',
                         required=True)


    def action_apply_reverse_entry(self):
        """Returning the invoice or bill and create credit and debit note."""
        active_id = self.env.context['active_id']
        return_id = self.env['stock.return.picking'].browse(active_id)
        return_data = return_id.create_returns()
        return_picking = self.env['stock.picking'].browse(return_data.get('res_id'))
        return_picking.action_set_quantities_to_reservation()
        return_picking.button_validate()
        if return_id.picking_id.sale_id.invoice_ids or return_id.picking_id.purchase_id.invoice_ids:
            for invoice in (
                    return_id.picking_id.sale_id.invoice_ids + return_id.picking_id.purchase_id.invoice_ids):
                if invoice.reversed_entry_id:
                    raise ValidationError(
                        "The selected invoice has already been reversed.")
            move_type = 'out_refund' if return_id.picking_id.picking_type_code == 'outgoing' else 'in_refund'

            reverse_move = self.env['account.move'].create({
                'partner_id': return_picking.partner_id.id,
                'move_type': move_type,
                'picking_id':return_id.picking_id.id,
                'invoice_date': return_picking.date_done,
                    'ref': _('Reversal of Credit Notes: %s, %s') % (invoice.name,self.reason),
                'invoice_line_ids': [
                    (0, 0, {
                        'product_id': rec.product_id.id,
                        'name': rec.product_id.name,
                        'quantity': rec.quantity_done,
                        'price_unit': rec.product_id.list_price,
                        'price_subtotal': rec.quantity_done * rec.product_id.list_price,
                    }) for rec in return_picking.move_ids_without_package]
            })
            reverse_move.action_post()
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'account.move',
                'target': 'current',
                'res_id': reverse_move.id,
            }
        else:
            raise ValidationError(
                "The selected picking should have at least one invoice.")
