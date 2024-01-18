# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models


class AccountMove(models.Model):
    """This class inherit the model 'account.move' and super the function
     'action post' to have the details of current transfer """
    _inherit = 'account.move'

    def action_post(self):
        """This function is used to add the transfer reference to the model
        'account.analytic.line' """
        res = super(AccountMove, self).action_post()
        transfer_rec = self.env['stock.picking'].search(
            [('origin', '=', self.invoice_origin)], order='create_date desc',
            limit=1).name
        account_move_line_rec = self.env['account.move.line'].search(
            [('move_id', '=', int(self.id)),
             ('display_type', '=', 'product')])
        for rec in account_move_line_rec:
            self.env['account.analytic.line'].search(
                [('move_line_id', '=', rec.id)]).update(
                {'transfer_reference': transfer_rec})
        return res
