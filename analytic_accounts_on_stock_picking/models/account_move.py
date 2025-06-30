# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
##############################################################################
from odoo import models


class AccountMove(models.Model):
    """ This class inherits the model 'account.move' and super the function
     'action post' to have the details of current transfer. """
    _inherit = 'account.move'

    def create(self, vals_list):
        """ Supering the function 'create' to transfer analytic_account_id from
        sale order lines to account move lines. """
        res = super().create(vals_list)
        if vals_list and type(vals_list) == list:
            if vals_list[0]['invoice_origin']:
                sale_order = self.env['sale.order'].search([
                    ('name', '=', vals_list[0]['invoice_origin'])])
                if sale_order:
                    for rec in res.line_ids:
                        rec.analytic_account_id = rec.sale_line_ids.analytic_account_id
        return res

    def action_post(self):
        """ Supering the function 'action_post' to add the transfer reference to
        the model 'account.analytic.line'. """
        res = super(AccountMove, self).action_post()
        transfer_rec = self.env['stock.picking'].search(
            [('origin', '=', self.invoice_origin)], order='create_date desc',
            limit=1).name
        for rec in self.line_ids:
            self.env['account.analytic.line'].search(
                [('move_id', '=', rec.id)]).update(
                {'transfer_reference': transfer_rec})
        return res
