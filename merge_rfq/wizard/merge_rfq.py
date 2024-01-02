# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Yadhukrishnan K (odoo@cybrosys.com)
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
################################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MergeRfq(models.TransientModel):
    """ MergeRfq class displaying the wizard for the purchase order selection or
     the rfq selection and this class have many functions for merging,
     cancelling, deleting and creating the orders """
    _name = 'merge.rfq'
    _description = 'Merge RFQ'

    merge_type = fields.Selection(selection=[
        ('cancel_and_new',
         'Cancel all selected purchase order and Create new order'),
        ('delete_and_new',
         'Delete all selected purchase order and Create new order'),
        ('cancel_and_merge',
         'Merge order on existing selected order and cancel others'),
        ('delete_and_merge',
         'Merge order on existing selected order and delete others')],
        default='cancel_and_new', help='Select which type of merge is to done.'
    )
    purchase_order_id = fields.Many2one('purchase.order',
                                        string='Purchase Order',
                                        help='Select RFQ to which others to '
                                             'be merged')
    partner_id = fields.Many2one('res.partner', string='Vendor',
                                 help='Select Vendor for new order')

    @api.onchange('merge_type')
    def _onchange_merge_type(self):
        """This function passes a domain to the field purchase_order_id for
        getting the selected RFQ"""
        for order in self:
            order.purchase_order_id = False
            if order.merge_type in ['cancel_and_merge', 'delete_and_merge']:
                return {
                    'domain': {'purchase_order_id': [(
                        "id", "in", self._context.get("active_ids"))]}}

    def merge_orders(self):
        """This function merge the selected RFQs"""
        purchase_orders = self.env["purchase.order"].browse(
            self._context.get("active_ids", []))
        if len(self._context.get("active_ids", [])) < 2:
            raise UserError(_("Please select at least two purchase orders."))
        if any(order.state not in ["draft", "sent"] for order in
               purchase_orders):
            raise UserError(_(
                "Please select Purchase orders which are in RFQ or RFQ sent "
                "state."))
        if self.merge_type in ['cancel_and_new', 'delete_and_new']:
            new_po = self.env["purchase.order"].create(
                {"partner_id": self.partner_id.id})
            for order in purchase_orders:
                for line in order.order_line:
                    order_line = False
                    if new_po.order_line:
                        for new_line in new_po.order_line:
                            if (line.product_id == new_line.product_id and
                                    line.price_unit == new_line.price_unit):
                                order_line = new_line
                                break
                    if order_line:
                        order_line.product_qty += line.product_qty
                    else:
                        line.copy(default={"order_id": new_po.id})
            for order in purchase_orders:
                order.sudo().button_cancel()
                if self.merge_type == "delete_and_new":
                    order.sudo().unlink()
        else:
            selected_po = self.purchase_order_id
            for order in purchase_orders:
                if order == selected_po:
                    continue
                for line in order.order_line:
                    order_line = False
                    for new_line in selected_po.order_line:
                        if (line.product_id == new_line.product_id and
                                line.price_unit == new_line.price_unit):
                            order_line = new_line
                            break
                    if order_line:
                        order_line.product_qty += line.product_qty
                    else:
                        line.copy(
                            default={"order_id": self.purchase_order_id.id})
            for order in purchase_orders:
                if order != selected_po:
                    order.sudo().button_cancel()
                    if self.merge_type == "delete_and_merge":
                        order.sudo().unlink()
