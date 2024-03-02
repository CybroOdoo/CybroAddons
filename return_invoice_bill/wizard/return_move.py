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
from odoo.exceptions import ValidationError
from odoo import fields, models


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
        return_id.create_returns()
        picking_id = return_id.picking_id
        sale_invoice_ids = picking_id.sale_id.invoice_ids
        purchase_invoice_ids = picking_id.purchase_id.invoice_ids
        if sale_invoice_ids and sale_invoice_ids.state == 'posted' or \
                purchase_invoice_ids and purchase_invoice_ids.state == 'posted':
            invoice_ids = sale_invoice_ids if picking_id.picking_type_code == 'outgoing' else purchase_invoice_ids
            reverse_moves = invoice_ids._reverse_moves()
            reverse_moves.write({'invoice_date': fields.date.today()})
            reverse_moves._post(soft=False)
        else:
            raise ValidationError(
                "The selected picking should have at least one posted invoice.")
