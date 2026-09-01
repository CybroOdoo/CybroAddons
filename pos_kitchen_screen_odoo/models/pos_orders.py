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
            kitchen_screens = self.env["kitchen.screen"].search(
                [("pos_config_id", "=", order.config_id.id)]
            )
            kitchen_categ_ids = set(kitchen_screens.pos_categ_ids.ids)
            if kitchen_screens:
                has_kitchen_items = False
                for order_line in order.lines:
                    if order_line.product_id.pos_categ_ids and any(
                            cat.id in kitchen_categ_ids for cat
                            in order_line.product_id.pos_categ_ids):
                        order_line.is_cooking = True
                        order_line.kitchen_sent_qty = order_line.qty
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
        # Internal recompute writes must not re-trigger the kitchen logic.
        if self.env.context.get('kitchen_skip_recompute'):
            return super(PosOrder, self).write(vals)
        res = super(PosOrder, self).write(vals)
        for order in self:
            kitchen_screens = self.env["kitchen.screen"].search(
                [("pos_config_id", "=", order.config_id.id)]
            )
            kitchen_categ_ids = set(kitchen_screens.pos_categ_ids.ids)
            if kitchen_screens:
                has_kitchen_items = False
                for line in order.lines:
                    if not order._line_in_categs(line, kitchen_categ_ids):
                        continue
                    has_kitchen_items = True
                    line_vals = {}
                    if not line.is_cooking:
                        # Brand-new kitchen line: starts cooking.
                        line_vals['is_cooking'] = True
                        line_vals['order_status'] = line.order_status or 'draft'
                        line_vals['kitchen_sent_qty'] = line.qty
                    elif line.qty > line.kitchen_sent_qty:
                        # Extra quantity added to an existing line = new work,
                        # even if that line was already completed -> re-open it.
                        # kitchen_sent_qty == 0 means a legacy line whose qty was
                        # never tracked yet, so we only initialise it (no reopen)
                        # to avoid spuriously reviving old orders on upgrade.
                        if line.kitchen_sent_qty:
                            line_vals['order_status'] = 'draft'
                        line_vals['kitchen_sent_qty'] = line.qty
                    elif line.qty < line.kitchen_sent_qty:
                        # Quantity reduced (line partially cancelled): keep the
                        # tracker in sync and make sure the advertised "new"
                        # count can never exceed what is actually on the line.
                        line_vals['kitchen_sent_qty'] = line.qty
                        if line.kitchen_new_qty > line.qty:
                            line_vals['kitchen_new_qty'] = line.qty
                    if line_vals:
                        line.write(line_vals)
                if has_kitchen_items and not order.is_cooking:
                    order.with_context(kitchen_skip_recompute=True).write({
                        'is_cooking': True,
                    })
                # Order-level status is a derived aggregate of its kitchen
                # lines. Recomputing here means that adding a new line to a
                # completed order automatically re-opens it for the kitchen.
                order._recompute_kitchen_status()
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
    def get_details(self, shop_id, kitchen_screen_id=None, *args, **kwargs):
        """Method to fetch kitchen orders for display on the kitchen screen.

        When ``kitchen_screen_id`` is provided the orders are filtered on the
        categories of that specific screen, which allows several screens
        (e.g. bar, hot, cold) to share the same POS while each only shows the
        lines that belong to it. ``shop_id`` is then re-derived from the screen
        so the caller cannot send an inconsistent pair.
        """
        if kitchen_screen_id:
            kitchen_screen = self.env["kitchen.screen"].sudo().browse(
                kitchen_screen_id)
            if not kitchen_screen.exists():
                return {"orders": [], "order_lines": []}
            shop_id = kitchen_screen.pos_config_id.id
        else:
            kitchen_screen = self.env["kitchen.screen"].sudo().search(
                [("pos_config_id", "=", shop_id)], limit=1)
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
        line_values = []
        for line in pos_lines:
            # kitchen_qty (>= 0) is the authoritative quantity set from the
            # client order at the last send; -1 means "never set" so we fall
            # back to the raw order line quantity. A line reduced to 0 (fully
            # cancelled) is dropped from the kitchen screen.
            effective_qty = line.qty if line.kitchen_qty < 0 else line.kitchen_qty
            if effective_qty <= 0:
                continue
            data = line.read()[0]
            data['qty'] = effective_qty
            line_values.append(data)
        values = {"orders": pos_orders.read(), "order_lines": line_values}
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
        kitchen_screens = self.env["kitchen.screen"].search(
            [("pos_config_id", "=", self.config_id.id)]
        )
        kitchen_categ_ids = set(kitchen_screens.pos_categ_ids.ids)
        if kitchen_screens:
            vals = {}
            has_kitchen_items = False
            for order_line in self.lines:
                if order_line.product_id.pos_categ_ids and any(
                        cat.id in kitchen_categ_ids for cat in
                        order_line.product_id.pos_categ_ids):
                    # Paying the order closes its kitchen items: mark the lines
                    # ready so the aggregate status becomes 'ready' (completed).
                    order_line.write({
                        'is_cooking': True,
                        'order_status': 'ready',
                        'kitchen_new_qty': 0.0,
                    })
                    has_kitchen_items = True
            if has_kitchen_items:
                vals.update({
                    'is_cooking': True,
                    'order_ref': self.name,
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

    def _kitchen_screen_categ_ids(self, kitchen_screen_id=None):
        """Return the set of POS category ids handled by a kitchen screen.

        With ``kitchen_screen_id`` the categories of that single screen are
        returned (so an action only affects the lines shown on that screen).
        Without it, the union of every screen of the POS is returned.
        """
        self.ensure_one()
        if kitchen_screen_id:
            screen = self.env['kitchen.screen'].sudo().browse(kitchen_screen_id)
            return set(screen.pos_categ_ids.ids) if screen.exists() else set()
        screens = self.env['kitchen.screen'].sudo().search(
            [('pos_config_id', '=', self.config_id.id)])
        return set(screens.pos_categ_ids.ids)

    def _line_in_categs(self, line, categ_ids):
        """True if the line's product belongs to one of the given categories."""
        return bool(line.product_id.pos_categ_ids) and any(
            cat.id in categ_ids for cat in line.product_id.pos_categ_ids)

    def _recompute_kitchen_status(self):
        """Derive the order-level status from its kitchen lines.

        The line status is the single source of truth. The order is considered
        'ready' (completed) only when ALL its kitchen lines are ready, which is
        what allows several screens (bar, hot, cold) to complete their own part
        independently without flipping the whole order on the other screens.
        """
        for order in self:
            kitchen_lines = order.lines.filtered(lambda l: l.is_cooking)
            if not kitchen_lines:
                # Every kitchen line was removed (fully cancelled): the order no
                # longer belongs on the kitchen screen.
                if order.is_cooking:
                    order.with_context(kitchen_skip_recompute=True).write(
                        {'is_cooking': False})
                continue
            active = kitchen_lines.filtered(lambda l: l.order_status != 'cancel')
            if not active:
                new_status = 'cancel'
            elif all(l.order_status == 'ready' for l in active):
                new_status = 'ready'
            elif any(l.order_status == 'draft' for l in active):
                # New / unstarted work present -> show as cooking, so that
                # adding an item to a completed order brings it back to the
                # kitchen instead of leaving it in the 'ready' column.
                new_status = 'draft'
            else:
                new_status = 'waiting'
            if order.order_status != new_status:
                order.with_context(kitchen_skip_recompute=True).write(
                    {'order_status': new_status})

    def order_progress_draft(self, kitchen_screen_id=None):
        """Action for "Accept" button: move this screen's lines from 'draft'
        (cooking) to 'waiting' (in preparation). Only the lines belonging to the
        calling screen are affected; the order status is then recomputed."""
        self.ensure_one()
        old_status = self.order_status
        categ_ids = self._kitchen_screen_categ_ids(kitchen_screen_id)
        for line in self.lines:
            if line.order_status not in ("ready", "cancel") and (
                    not categ_ids or self._line_in_categs(line, categ_ids)):
                line.order_status = "waiting"
                # The cook is now taking on the current new units: reset the
                # counter so a later addition shows only its own delta.
                if line.kitchen_new_qty:
                    line.kitchen_new_qty = 0.0
        self._recompute_kitchen_status()
        if old_status != self.order_status:
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

    def order_progress_change(self, kitchen_screen_id=None):
        """Action for "Done" button: mark this screen's lines as 'ready'
        (completed). The order only becomes globally 'ready' once every screen
        has completed its own lines, computed by ``_recompute_kitchen_status``."""
        self.ensure_one()
        categ_ids = self._kitchen_screen_categ_ids(kitchen_screen_id)
        for line in self.lines:
            if line.order_status != "cancel" and (
                    not categ_ids or self._line_in_categs(line, categ_ids)):
                line.order_status = "ready"
                # The newly added units are now prepared: stop advertising them.
                if line.kitchen_new_qty:
                    line.kitchen_new_qty = 0.0
        self._recompute_kitchen_status()
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
        kitchen_screens = self.env['kitchen.screen'].sudo().search(
            [("pos_config_id", "=", pos_order.config_id.id)])
        kitchen_categ_ids = set(kitchen_screens.pos_categ_ids.ids)
        if not kitchen_screens:
            return False
        unhandled_categories = []
        for line in pos_order.lines:
            if line.product_id.pos_categ_ids and not any(
                    cat.id in kitchen_categ_ids for cat in line.product_id.pos_categ_ids):
                unhandled_categories.extend(
                    [c.name for c in line.product_id.pos_categ_ids if c.id not in kitchen_categ_ids])
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
        kitchen_screens = self.env["kitchen.screen"].search([
            ("pos_config_id", "=", config_id)
        ])
        kitchen_categ_ids = set(kitchen_screens.pos_categ_ids.ids)
        if not kitchen_screens:
            return False
        kitchen_lines = []
        for line in pos_order.lines:
            product = line.product_id
            if product.pos_categ_ids and any(
                    cat.id in kitchen_categ_ids
                    for cat in product.pos_categ_ids):
                kitchen_lines.append(line)
        if not kitchen_lines:
            return False
        for line in kitchen_lines:
            # Only ensure the line is flagged for the kitchen. Do NOT reset its
            # status: accepted/cooking/ready lines must keep their progress.
            # Re-opening on new quantities is handled by apply_kitchen_new_quantities.
            if not line.is_cooking:
                line.write({
                    'is_cooking': True,
                    'order_status': line.order_status or 'draft',
                })
        if not pos_order.is_cooking:
            pos_order.with_context(kitchen_skip_recompute=True).write(
                {'is_cooking': True})
        pos_order._recompute_kitchen_status()
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
        kitchen_screens = self.env["kitchen.screen"].search([
            ("pos_config_id", "=", config_id)
        ])
        kitchen_categ_ids = set(kitchen_screens.pos_categ_ids.ids)
        if not kitchen_screens:
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
                                                     cat.id in kitchen_categ_ids
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
        """Check whether items can still be added to an order.

        In a restaurant workflow new items (e.g. a coffee at the end of the
        meal) may be added after the kitchen has completed the first round, so a
        'ready' (completed) order is NOT a blocker: adding a line re-opens it for
        the kitchen via ``write``. Only a cancelled order is refused."""
        pos_order = self.env['pos.order'].sudo().search([
            ('pos_reference', '=', str(order_reference))
        ], limit=1)
        if not pos_order:
            return True
        return pos_order.order_status != 'cancel'

    @api.model
    def apply_kitchen_new_quantities(self, order_uuid, new_qty_by_uuid,
                                     current_qty_by_uuid=None):
        """Record kitchen changes computed on the client at send time.

        ``new_qty_by_uuid`` maps a line uuid to the quantity ADDED since the
        previous send (drives the "+N new" badge). ``current_qty_by_uuid`` maps
        a line uuid to the AUTHORITATIVE current quantity from the client order
        (0 when the line was removed); it is stored as ``kitchen_qty`` so the
        kitchen screen reflects reductions/cancellations even when the POS keeps
        the original order line. Lines reaching 0 leave the kitchen screen.
        Matched by stable uuid, so robust regardless of name/reference format."""
        if not order_uuid:
            return False
        new_qty_by_uuid = new_qty_by_uuid or {}
        current_qty_by_uuid = current_qty_by_uuid or {}
        if not new_qty_by_uuid and not current_qty_by_uuid:
            return False
        order = self.sudo().search([('uuid', '=', order_uuid)], limit=1)
        if not order:
            return False
        kitchen_categ_ids = order._kitchen_screen_categ_ids()
        touched = False
        changed_uuids = set(new_qty_by_uuid) | set(current_qty_by_uuid)
        for line in order.lines:
            if line.uuid not in changed_uuids:
                continue
            if not order._line_in_categs(line, kitchen_categ_ids):
                continue
            vals = {}
            if line.uuid in current_qty_by_uuid:
                cur = current_qty_by_uuid[line.uuid]
                vals['kitchen_qty'] = cur
                if cur <= 0:
                    # Fully cancelled: drop it from the kitchen screen.
                    vals['is_cooking'] = False
            diff = new_qty_by_uuid.get(line.uuid, 0)
            if diff and diff > 0 and vals.get('kitchen_qty', 1) > 0:
                vals['is_cooking'] = True
                vals['order_status'] = 'draft'
                vals['kitchen_new_qty'] = line.kitchen_new_qty + diff
                vals['kitchen_sent_qty'] = line.qty
            if vals:
                line.write(vals)
                touched = True
        if touched:
            if not order.is_cooking and any(
                    l.is_cooking for l in order.lines):
                order.with_context(kitchen_skip_recompute=True).write(
                    {'is_cooking': True})
            order._recompute_kitchen_status()
            message = {
                'res_model': 'pos.order',
                'message': 'pos_order_updated',
                'order_id': order.id,
                'config_id': order.config_id.id,
            }
            channel = f'pos_order_created_{order.config_id.id}'
            self.env["bus.bus"]._sendone(channel, "notification", message)
        return touched


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
    kitchen_sent_qty = fields.Float(
        string="Kitchen Sent Qty", default=0.0, copy=False,
        help="Quantity of this line already known by the kitchen. Any extra "
             "quantity added later is treated as new work and re-opens the "
             "line for cooking.")
    kitchen_new_qty = fields.Float(
        string="Kitchen New Qty", default=0.0, copy=False,
        help="Number of units newly sent to the kitchen and not yet completed, "
             "computed from Odoo's native preparation-change diff. Shown on the "
             "kitchen screen so the cook knows exactly how many to prepare; "
             "reset to 0 once the line is marked ready.")
    kitchen_qty = fields.Float(
        string="Kitchen Qty", default=-1.0, copy=False,
        help="Authoritative quantity the kitchen must prepare for this line, "
             "set from the client order at each send (-1 means not set yet, in "
             "which case the order line quantity is used). Lets cancellations / "
             "reductions be reflected on the kitchen screen even when the POS "
             "keeps the original order line.")
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
            # Completed: the newly added units have been prepared.
            if self.kitchen_new_qty:
                self.kitchen_new_qty = 0.0

        if old_status != self.order_status:
            # Keep the order-level (aggregate) status in sync with its lines.
            self.order_id._recompute_kitchen_status()
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

class KitchenOrderCancellation(models.Model):
    """Persistent record of a kitchen item that was cancelled/reduced after it
    had already been sent to the kitchen.

    A cancelled order line is removed from the order, so it can no longer be
    shown through ``get_details``. This model keeps an independent trace so the
    kitchen screen can warn the cook (who may be preparing it right now) until
    the alert is explicitly acknowledged."""
    _name = "kitchen.order.cancellation"
    _description = "Kitchen Order Cancellation Alert"
    _order = "create_date desc"

    config_id = fields.Many2one("pos.config", string="POS Config",
                                required=True, ondelete="cascade",
                                help="POS the cancellation belongs to")
    product_id = fields.Many2one("product.product", string="Product",
                                 help="Cancelled product")
    product_name = fields.Char(string="Product Name",
                               help="Name shown on the kitchen alert")
    qty = fields.Float(string="Cancelled Qty", help="Cancelled quantity")
    order_ref = fields.Char(string="Order Reference",
                            help="Reference of the related order")
    table_name = fields.Char(string="Table", help="Table of the related order")
    acknowledged = fields.Boolean(string="Acknowledged", default=False,
                                  help="Set once the cook has seen the alert")

    @api.model
    def record_cancellations(self, config_id, order_ref, table_name,
                             cancellations):
        """Store cancellations captured on the client from the native
        preparation-change diff, and notify the kitchen screens."""
        if not config_id or not cancellations:
            return False
        created = self.env[self._name]
        for change in cancellations:
            qty = change.get("quantity") or 0
            if qty <= 0:
                continue
            product = self.env["product.product"].browse(
                change.get("product_id")) if change.get("product_id") else False
            created |= self.create({
                "config_id": config_id,
                "product_id": product.id if product else False,
                "product_name": change.get("name") or (
                    product.display_name if product else ""),
                "qty": qty,
                "order_ref": order_ref or "",
                "table_name": table_name or "",
            })
        if created:
            channel = f"pos_order_created_{config_id}"
            self.env["bus.bus"]._sendone(channel, "notification", {
                "res_model": self._name,
                "message": "kitchen_order_cancelled",
                "config_id": config_id,
            })
        return bool(created)

    @api.model
    def get_cancellations(self, config_id, kitchen_screen_id=None):
        """Return the pending (unacknowledged) cancellation alerts for a screen.

        When a screen id is given, only cancellations whose product belongs to
        that screen's categories are returned, so each screen sees its own."""
        if not config_id:
            return []
        records = self.search([
            ("config_id", "=", config_id),
            ("acknowledged", "=", False),
        ])
        if kitchen_screen_id:
            screen = self.env["kitchen.screen"].sudo().browse(kitchen_screen_id)
            categ_ids = set(screen.pos_categ_ids.ids) if screen.exists() else set()
            records = records.filtered(
                lambda r: not r.product_id or any(
                    c.id in categ_ids for c in r.product_id.pos_categ_ids))
        return records.read(
            ["id", "product_name", "qty", "order_ref", "table_name"])

    @api.model
    def acknowledge_cancellations(self, ids):
        """Mark cancellation alerts as seen so they stop being displayed."""
        if not ids:
            return False
        self.browse(ids).write({"acknowledged": True})
        return True
