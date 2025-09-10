# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
############################################################################
from odoo import api, fields, models
from datetime import datetime
import pytz


class PosOrder(models.Model):
    """Inheriting the pos order model """
    _inherit = "pos.order"

    order_status = fields.Selection(string="Order Status",
                                    selection=[("draft", "Cooking Orders"),
                                               ("waiting", "Ready Orders"),
                                               ("ready", "Completed Orders"),
                                               ("cancel", "Cancelled Orders")],
                                    default='draft',
                                    help='Kitchen workflow status: draft=cooking, waiting=ready, ready=completed')
    order_ref = fields.Char(string="Order Reference",
                            help='Reference of the order')
    is_cooking = fields.Boolean(string="Is Cooking",
                                help='To identify the order is kitchen orders')
    hour = fields.Char(string="Order Time", readonly=True,
                       help='To set the time of each order')
    minutes = fields.Char(string='Order time')
    floor = fields.Char(string='Floor time')
    avg_prepare_time = fields.Float(string="Avg Prepare Time", store=True)

    @api.model_create_multi
    def create(self, vals_list):
        """Override create function for the validation of the order"""
        processed_vals_to_create = []
        for vals in vals_list:
            product_ids = [item[2]['product_id'] for item in vals.get('lines')]
            if product_ids:
                prepare_times = self.env['product.product'].search(
                    [('id', 'in', product_ids)]).mapped(
                    'prepair_time_minutes')
                vals['avg_prepare_time'] = max(prepare_times)
            existing_order = self.search(
                [("pos_reference", "=", vals.get("pos_reference"))], limit=1)
            if existing_order:
                continue
            if not vals.get("order_status"):
                vals["order_status"] = 'draft'
            if not vals.get('name'):
                if vals.get('order_id'):
                    config = self.env['pos.order'].browse(
                        vals['order_id']).session_id.config_id
                    vals[
                        'name'] = config.sequence_line_id._next() if config.sequence_line_id else \
                    self.env['ir.sequence'].next_by_code('pos.order') or '/'
                else:
                    vals['name'] = self.env['ir.sequence'].next_by_code(
                        'pos.order') or '/'
            processed_vals_to_create.append(vals)
        res = super().create(
            processed_vals_to_create) if processed_vals_to_create else self.browse()
        orders_to_notify = []
        for order in res:
            kitchen_screen = self.env["kitchen.screen"].search(
                [("pos_config_id", "=", order.config_id.id)], limit=1
            )
            if kitchen_screen:
                has_kitchen_items = False
                for order_line in order.lines:
                    if order_line.product_id.pos_categ_ids and any(
                            cat.id in kitchen_screen.pos_categ_ids.ids for cat
                            in order_line.product_id.pos_categ_ids):
                        order_line.is_cooking = True
                        has_kitchen_items = True
                if has_kitchen_items:
                    order.is_cooking = True
                    order.order_ref = order.name  # Set order_ref here
                    if order.order_status != 'draft':
                        order.order_status = 'draft'
                    orders_to_notify.append(order)
        self.env.cr.commit()
        for order in orders_to_notify:
            message = {
                'res_model': self._name,
                'message': 'pos_order_created',
                'order_id': order.id,
                'config_id': order.config_id.id,
                'order_ref': order.order_ref
                # Include order_ref in notification
            }
            channel = f'pos_order_created_{order.config_id.id}'
            self.env["bus.bus"]._sendone(channel, "notification", message)
        return res

    def write(self, vals):
        """Override write function for adding order status in vals"""
        res = super(PosOrder, self).write(vals)
        for order in self:
            kitchen_screen = self.env["kitchen.screen"].search(
                [("pos_config_id", "=", order.config_id.id)], limit=1
            )
            if kitchen_screen:
                has_kitchen_items = False
                for line in order.lines:
                    if line.product_id.pos_categ_ids and any(
                            cat.id in kitchen_screen.pos_categ_ids.ids
                            for cat in line.product_id.pos_categ_ids):
                        if not line.is_cooking:
                            line.write({
                                'is_cooking': True,
                                'order_status': line.order_status or 'draft'
                            })
                        has_kitchen_items = True
                if has_kitchen_items and not order.is_cooking:
                    order.write({
                        'is_cooking': True,
                        'order_status': order.order_status or 'draft'
                    })
                message = {
                    'res_model': self._name,
                    'message': 'pos_order_updated',
                    'order_id': order.id,
                    'config_id': order.config_id.id,
                    'lines': order.lines.read([
                        'id', 'product_id', 'qty', 'order_status', 'is_cooking'
                    ])
                }
                channel = f'pos_order_created_{order.config_id.id}'
                self.env["bus.bus"]._sendone(channel, "notification", message)
        return res

    @api.model
    def get_details(self, shop_id, *args, **kwargs):
        """Method to fetch kitchen orders for display on the kitchen screen."""
        kitchen_screen = self.env["kitchen.screen"].sudo().search(
            [("pos_config_id", "=", shop_id)])
        if not kitchen_screen:
            return {"orders": [], "order_lines": []}
        pos_orders = self.env["pos.order"].search([
            ("is_cooking", "=", True),
            ("config_id", "=", shop_id),
            ("state", "not in", ["cancel"]),
            ("order_status", "in", ["draft", "waiting", "ready"])
        ], order="date_order")
        pos_lines = pos_orders.lines.filtered(
            lambda line: line.is_cooking and any(
                categ.id in kitchen_screen.pos_categ_ids.ids
                for categ in line.product_id.pos_categ_ids
            )
        )
        values = {"orders": pos_orders.read(), "order_lines": pos_lines.read()}
        user_tz_str = self.env.user.tz or 'UTC'
        user_tz = pytz.timezone(user_tz_str)
        utc = pytz.utc
        for value in values['orders']:
            if value.get('table_id'):
                value['floor'] = value['table_id'][1].split(',')[0].strip()
            date_str = value['date_order']
            try:
                if isinstance(date_str, str):
                    utc_dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                    utc_dt = utc.localize(utc_dt)
                else:
                    utc_dt = utc.localize(value['date_order'])
                local_dt = utc_dt.astimezone(user_tz)
                value['hour'] = local_dt.hour
                value['formatted_minutes'] = f"{local_dt.minute:02d}"
                value['minutes'] = local_dt.minute
            except Exception:
                value['hour'] = 0
                value['minutes'] = 0
                value['formatted_minutes'] = "00"
        return values

    def action_pos_order_paid(self):
        """Inherited method called when a POS order transitions to 'paid' state."""
        res = super().action_pos_order_paid()
        kitchen_screen = self.env["kitchen.screen"].search(
            [("pos_config_id", "=", self.config_id.id)], limit=1
        )
        if kitchen_screen:
            vals = {}
            has_kitchen_items = False
            for order_line in self.lines:
                if order_line.product_id.pos_categ_ids and any(
                        cat.id in kitchen_screen.pos_categ_ids.ids for cat in
                        order_line.product_id.pos_categ_ids):
                    order_line.write({'is_cooking': True})
                    has_kitchen_items = True
            if has_kitchen_items:
                vals.update({
                    'is_cooking': True,
                    'order_ref': self.name,
                    'order_status': 'ready'
                })
                self.write(vals)
                message = {
                    'res_model': self._name,
                    'message': 'pos_order_created',
                    'order_id': self.id,
                    'config_id': self.config_id.id
                }
                channel = f'pos_order_created_{self.config_id.id}'
                self.env["bus.bus"]._sendone(channel, "notification", message)
        return res

    @api.onchange("order_status")
    def _onchange_is_cooking(self):
        """Automatically unmark as 'cooking' when order status becomes 'ready'."""
        if self.order_status == "ready":
            self.is_cooking = False

    def order_progress_draft(self):
        """Action for "Accept" button: Move order from 'draft' (cooking) to 'waiting' (ready) status."""
        self.ensure_one()
        old_status = self.order_status
        self.order_status = "waiting"
        for line in self.lines:
            if line.order_status not in ["ready", "cancel"]:
                line.order_status = "waiting"

        if old_status != "waiting":
            message = {
                'res_model': self._name,
                'message': 'pos_order_accepted',
                'order_id': self.id,
                'config_id': self.config_id.id
            }
            channel = f'pos_order_created_{self.config_id.id}'
            self.env["bus.bus"]._sendone(channel, "notification", message)

    def order_progress_cancel(self):
        """Action for "Cancel" button: Move order to 'cancel' status."""
        self.ensure_one()
        self.order_status = "cancel"
        for line in self.lines:
            line.order_status = "cancel"
        message = {
            'res_model': self._name,
            'message': 'pos_order_cancelled',
            'order_id': self.id,
            'config_id': self.config_id.id
        }
        channel = f'pos_order_created_{self.config_id.id}'
        self.env["bus.bus"]._sendone(channel, "notification", message)

    def order_progress_change(self):
        """Action for "Done" button: Move order from 'waiting' (ready) to 'ready' (completed) status."""
        self.ensure_one()
        self.order_status = "ready"
        kitchen_screen = self.env["kitchen.screen"].search(
            [("pos_config_id", "=", self.config_id.id)], limit=1)
        if kitchen_screen:
            for line in self.lines:
                if line.product_id.pos_categ_ids and any(
                        cat.id in kitchen_screen.pos_categ_ids.ids for cat in line.product_id.pos_categ_ids):
                    line.order_status = "ready"
        message = {
            'res_model': self._name,
            'message': 'pos_order_completed',
            'order_id': self.id,
            'config_id': self.config_id.id
        }
        channel = f'pos_order_created_{self.config_id.id}'
        self.env["bus.bus"]._sendone(channel, "notification", message)

    @api.model
    def check_order(self, order_name):
        """Check if an order exists, has kitchen items, and is not yet completed/cancelled."""
        pos_order = self.env['pos.order'].sudo().search(
            [('pos_reference', '=', str(order_name))], limit=1)
        if not pos_order:
            return False
        kitchen_screen = self.env['kitchen.screen'].sudo().search(
            [("pos_config_id", "=", pos_order.config_id.id)], limit=1)
        if not kitchen_screen:
            return False
        unhandled_categories = []
        for line in pos_order.lines:
            if line.product_id.pos_categ_ids and not any(
                    cat.id in kitchen_screen.pos_categ_ids.ids for cat in line.product_id.pos_categ_ids):
                unhandled_categories.extend(
                    [c.name for c in line.product_id.pos_categ_ids if c.id not in kitchen_screen.pos_categ_ids.ids])
        if unhandled_categories:
            return {'category': ", ".join(list(set(unhandled_categories)))}
        if pos_order.order_status not in ['ready', 'cancel']:
            return True
        else:
            return False

    @api.model
    def process_order_for_kitchen(self, order_data):
        """Process already created POS order for kitchen screen display."""
        pos_reference = order_data.get('pos_reference')
        config_id = order_data.get('config_id')
        pos_order = self.search([
            ('name', '=', f"Order {pos_reference}"),
            ('config_id', '=', config_id)
        ], limit=1)
        if not pos_order:
            return False
        kitchen_screen = self.env["kitchen.screen"].search([
            ("pos_config_id", "=", config_id)
        ], limit=1)
        if not kitchen_screen:
            return False
        kitchen_lines = []
        for line in pos_order.lines:
            product = line.product_id
            if product.pos_categ_ids and any(
                    cat.id in kitchen_screen.pos_categ_ids.ids
                    for cat in product.pos_categ_ids):
                kitchen_lines.append(line)
        if not kitchen_lines:
            return False
        for line in kitchen_lines:
            line.write({
                'is_cooking': True,
                'order_status': 'draft'
            })
        pos_order.write({
            'is_cooking': True,
            'order_status': 'draft'
        })
        message = {
            'res_model': 'pos.order',
            'message': 'pos_order_updated',
            'config_id': config_id,
            'order_id': pos_order.id,
            'pos_reference': pos_reference
        }
        channel = f'pos_order_created_{config_id}'
        self.env["bus.bus"]._sendone(channel, "notification", message)
        return True

    @api.model
    def get_kitchen_orders(self, config_id):
        """Get all orders that have kitchen items for the kitchen screen."""
        kitchen_screen = self.env["kitchen.screen"].search([
            ("pos_config_id", "=", config_id)
        ], limit=1)
        if not kitchen_screen:
            return []
        kitchen_orders = self.search([
            ('config_id', '=', config_id),
            ('is_cooking', '=', True),
            ('order_status', 'not in', ['ready', 'cancel'])
        ])
        orders_data = []
        for order in kitchen_orders:
            # Get only kitchen lines
            kitchen_lines = order.lines.filtered(lambda l:
                                                 l.product_id.pos_categ_ids and any(
                                                     cat.id in kitchen_screen.pos_categ_ids.ids
                                                     for cat in
                                                     l.product_id.pos_categ_ids
                                                 )
                                                 )
            if kitchen_lines:
                line_data = []
                for line in kitchen_lines:
                    line_data.append({
                        'id': line.id,
                        'product_id': line.product_id.id,
                        'product_name': line.product_id.name,
                        'qty': line.qty,
                        'note': line.note or '',
                        'order_status': line.order_status or 'draft'
                    })
                orders_data.append({
                    'id': order.id,
                    'pos_reference': order.pos_reference,
                    'name': order.name,
                    'table_id': order.table_id.id if order.table_id else False,
                    'table_name': order.table_id.name if order.table_id else '',
                    'order_status': order.order_status,
                    'lines': line_data,
                    'date_order': order.date_order,
                    'amount_total': order.amount_total
                })
        return orders_data

    @api.model
    def update_kitchen_order_status(self, order_id, status):
        """Update kitchen order status."""
        order = self.browse(order_id)
        if order.exists():
            order.write({'order_status': status})
            kitchen_lines = order.lines.filtered(lambda l: l.is_cooking)
            kitchen_lines.write({'order_status': status})
            message = {
                'res_model': 'pos.order',
                'message': 'kitchen_order_status_updated',
                'config_id': order.config_id.id,
                'order_id': order.id,
                'status': status
            }
            channel = f'pos_order_created_{order.config_id.id}'
            self.env["bus.bus"]._sendone(channel, "notification", message)
            return True
        return False

    @api.model
    def check_order_status(self, dummy_param, order_reference):
        """Check if items can be added to an order based on its status."""
        pos_order = self.env['pos.order'].sudo().search([
            ('pos_reference', '=', str(order_reference))
        ], limit=1)
        if not pos_order:
            return True
        return pos_order.order_status in ['draft', 'waiting']


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    order_status = fields.Selection(
        selection=[('draft', 'Cooking'), ('waiting', 'Ready'),
                   ('ready', 'Completed'), ('cancel', 'Cancel')], default='draft',
        help='Kitchen workflow status: draft=cooking, waiting=ready, ready=completed')
    order_ref = fields.Char(related='order_id.order_ref',
                            string='Order Reference',
                            help='Order reference of order')
    is_cooking = fields.Boolean(string="Cooking", default=False,
                                help='To identify the order is kitchen orders')
    customer_id = fields.Many2one('res.partner', string="Customer",
                                  related='order_id.partner_id',
                                  help='Id of the customer')

    def get_product_details(self, ids):
        """Fetch details for specific order lines."""
        lines = self.env['pos.order.line'].browse(ids)
        res = []
        for rec in lines:
            res.append({
                'product_id': rec.product_id.id,
                'name': rec.product_id.name,
                'qty': rec.qty
            })
        return res

    def order_progress_change(self):
        """Toggle status of an order line between 'waiting' and 'ready'."""
        self.ensure_one()
        old_status = self.order_status
        if self.order_status == 'ready':
            self.order_status = 'waiting'
        else:
            self.order_status = 'ready'

        if old_status != self.order_status:
            message = {
                'res_model': 'pos.order.line',
                'message': 'pos_order_line_updated',
                'line_id': self.id,
                'order_id': self.order_id.id,
                'config_id': self.order_id.config_id.id,
                'new_status': self.order_status
            }
            channel = f'pos_order_created_{self.order_id.config_id.id}'
            self.env["bus.bus"]._sendone(channel, "notification", message)