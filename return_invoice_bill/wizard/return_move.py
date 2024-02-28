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
from odoo import models, fields


class ReturnMove(models.TransientModel):
    """Transient model for ,enter the cancel reason credit and debit note."""
    _name = 'return.move'
    _description = 'Return Move'
    _rec_name = 'reason'

    reason = fields.Char(string='Reason',
                         help='Specify the reason for credit note',
                         required=True)

    def apply_reverse_entry(self):
        """Returning the invoice or bill and create credit and debit note. """
        active_id = self.env.context['active_id']
        return_id = self.env['stock.return.picking'].browse(active_id)
        return_id.create_returns()
        if return_id.picking_id.sale_id.invoice_ids or return_id.picking_id.purchase_id.invoice_ids:
            if return_id.picking_id.picking_type_code == 'outgoing':
                reverse_move = return_id.picking_id.sale_id.invoice_ids._reverse_moves()
                reverse_move._post(soft=False)
                return
            reverse_move = return_id.picking_id.purchase_id.invoice_ids._reverse_moves()
            reverse_move.write({
                'invoice_date': fields.date.today()
            })
            reverse_move._post(soft=False)
        else:
            raise ValidationError(
                "The selected picking should have at least one invoice.")
