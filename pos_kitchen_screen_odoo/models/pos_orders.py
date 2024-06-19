# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gokul P I (odoo@cybrosys.com)
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
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PosOrder(models.Model):
    """Inheriting the pos order model """
    _inherit = "pos.order"

    order_status = fields.Selection(string="Order Status",
                                    selection=[("draft", "Draft"),
                                               ("waiting", "Cooking"),
                                               ("ready", "Ready"),
                                               ("cancel", "Cancel")],
                                    help='To know the status of order')
    order_ref = fields.Char(string="Order Reference",
                            help='Reference of the order')
    is_cooking = fields.Boolean(string="Is Cooking",
                                help='To identify the order is  kitchen orders')
    order_time = fields.Char(string="Order Time", readonly=True,
                             help='To set the time of each order')

    def write(self, vals):
        """Super the write function for adding order status in vals"""
        message = {
            'res_model': self._name,
            'message': 'pos_order_created'
        }
        self.env["bus.bus"]._sendone('pos_order_created',
                                     "notification",
                                     message)
        for order in self:
            if order.order_status == "waiting" and vals.get(
                    "order_status") != "ready":
                vals["order_status"] = order.order_status
            if vals.get("state") and vals[
                "state"] == "paid" and order.name == "/":
                vals["name"] = self._compute_order_name()
        return super(PosOrder, self).write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        """Override create function for the validation of the order"""
        """Override create function for the validation of the order"""
        message = {
            'res_model': self._name,
            'message': 'pos_order_created'
        }
        self.env["bus.bus"]._sendone('pos_order_created',
                                     "notification",
                                     message)
        for vals in vals_list:
            pos_orders = self.search(
                [("pos_reference", "=", vals["pos_reference"])])
            if pos_orders:
                for rec in pos_orders.lines:
                    for lin in vals_list[0]["lines"]:
                        if lin[2]["product_id"] == rec.product_id.id:
                            lin[2]["order_status"] = rec.order_status
                vals_list[0]["order_status"] = pos_orders.order_status
                if pos_orders.order_status != "ready":
                    for rec in pos_orders:
                        rec.sudo().unlink()
                    pos_orders.create(vals_list[0])
                else:
                    raise ValidationError(
                        'There Order is Completed please create a new Order')
            else:
                session = self.env["pos.session"].browse(vals["session_id"])
                self._complete_values_from_session(session, vals)
                return super().create(vals_list)

    def get_details(self, shop_id, order=None):
        """For getting the kitchen orders for the cook"""
        dic = order

        if order:
            orders = self.search(
                [("pos_reference", "=", order[0]['pos_reference'])])
            if not orders:
                self.create(dic)
            else:
                orders.lines = False
                orders.lines = dic[0]['lines']
        kitchen_screen = self.env["kitchen.screen"].sudo().search(
            [("pos_config_id", "=", shop_id)])

        pos_orders = self.env["pos.order.line"].search(
            ["&", ("is_cooking", "=", True),
             ("product_id.pos_categ_id", "in",
              [rec.id for rec in kitchen_screen.pos_categ_ids])])
        pos = self.env["pos.order"].search(
            [("lines", "in", [rec.id for rec in pos_orders])],
            order="date_order")
        pos_lines = pos.lines.search(
            [("product_id.pos_categ_id", "in",
              [rec.id for rec in kitchen_screen.pos_categ_ids])])
        values = {"orders": pos.read(), "order_lines": pos_lines.read()}
        return values
    def action_pos_order_paid(self):
        """Supering the action_pos_order_paid function for setting its kitchen
        order and setting the order reference"""
        res = super().action_pos_order_paid()
        kitchen_screen = self.env["kitchen.screen"].search(
            [("pos_config_id", "=", self.config_id.id)]
        )
        for order_line in self.lines:
            order_line.is_cooking = True
        if kitchen_screen:
            for line in self.lines:
                line.is_cooking = True
            self.is_cooking = True
            self.order_ref = self.name
        return res

    @api.onchange("order_status")
    def onchange_order_status(self):
        """To set is_cooking false"""
        if self.order_status == "ready":
            self.is_cooking = False

    def order_progress_draft(self):
        """Calling function from js to change the order status"""
        self.order_status = "waiting"
        for line in self.lines:
            if line.order_status != "ready":
                line.order_status = "waiting"

    def order_progress_cancel(self):
        """Calling function from js to change the order status"""
        # order = self.browse(int(id))
        self.order_status = "cancel"
        for line in self.lines:
            if line.order_status != "ready":
                line.order_status = "cancel"

    def order_progress_change(self):
        """Calling function from js to change the order status"""
        kitchen_screen = self.env["kitchen.screen"].search(
            [("pos_config_id", "=", self.config_id.id)])
        stage = []
        for line in self.lines:
            for categ in line.product_id.pos_categ_id:
                if categ.id in [rec.id for rec in
                                kitchen_screen.pos_categ_ids]:
                    stage.append(line.order_status)
        if "waiting" in stage or "draft" in stage:
            self.order_status = "ready"
        else:
            self.order_status = "ready"

    def check_order(self, order_name):
        """Calling function from js to know status of the order"""
        pos_order = self.sudo().search([('pos_reference', '=', order_name)])
        kitchen_order = self.env['kitchen.screen'].sudo().search(
            [('pos_config_id', '=', pos_order.config_id.id)])
        if kitchen_order:
            if pos_order.order_status != 'ready':
                if pos_order.order_status == 'cancel':
                    return False
                return True
            else:
                return False
        else:
            return False


class PosOrderLine(models.Model):
    """Inheriting the pos order line"""
    _inherit = "pos.order.line"

    order_status = fields.Selection(
        selection=[('draft', 'Draft'), ('waiting', 'Cooking'),
                   ('ready', 'Ready'), ('cancel', 'Cancel')], default='draft',
        help='The status of orderliness')
    order_ref = fields.Char(related='order_id.order_ref',
                            string='Order Reference',
                            help='Order reference of order')
    is_cooking = fields.Boolean(string="Cooking", default=False,
                                help='To identify the order is  kitchen orders')
    customer_id = fields.Many2one('res.partner', string="Customer",
                                  related='order_id.partner_id',
                                  help='Id of the customer')

    def get_product_details(self, ids):
        """To get the product details"""
        lines = self.env['pos.order'].browse(ids)
        res = []
        for rec in lines:
            res.append({
                'product_id': rec.product_id.id,
                'name': rec.product_id.name,
                'qty': rec.qty
            })
        return res

    def order_progress_change(self):
        """Calling function from js to change the order_line status"""
        if self.order_status == 'ready':
            self.order_status = 'waiting'
        else:
            self.order_status = 'ready'