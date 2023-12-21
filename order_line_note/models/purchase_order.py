# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra MP (odoo@cybrosys.com)
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


class PurchaseOrder(models.Model):
    """This class extends the 'purchase.order' model to add additional
    functionality related to purchase orders."""
    _inherit = 'purchase.order'

    def button_confirm(self):
        """Override of the button_confirm method to copy notes from purchase
        order lines to correspond stock moves."""
        res = super().button_confirm()
        for rec in self.order_line:
            self.env['stock.move'].search([('purchase_line_id', '=', rec.id)])[
                'note'] = rec.note
        return res

    def action_create_invoice(self):
        """Override of the action_create_invoice method to copy notes from
        purchase order lines to correspond account move lines."""
        res = super().action_create_invoice()
        for rec in self.order_line:
            self.env['account.move.line'].search(
                [('purchase_line_id', '=', rec.id)])[
                'note'] = rec.note
        return res
