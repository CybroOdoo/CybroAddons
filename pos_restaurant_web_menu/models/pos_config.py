# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
from typing import Optional
from odoo import Command, fields, models, _
from odoo.exceptions import UserError


class PosConfig(models.Model):
    """Inherit pos configuration and add new fields."""
    _inherit = 'pos.config'

    web_menu_view_mode = fields.Boolean(
        string="POS web Menu",
        help="Allow customers to view the menu on their phones.")
    web_qr_code = fields.Binary(
        string='QRcode',
        help='Qr code of POS App that allows customers to view the menu on '
             'their smartphone.')

    def _get_web_menu_route(self, table_id: Optional[int] = None) -> str:
        """Return url for pos web menu with pos config_id and table_id."""
        self.ensure_one()
        base_route = f"/menu/{self.id}"
        table_route = ""
        table = self.env["restaurant.table"].search(
            [("active", "=", True), ("id", "=", table_id)], limit=1)
        if table:
            table_route = f"&table_identifier={table.identifier}"
        return f"{base_route}?{table_route}"

    def preview_pos_web_menu_url(self):
        """Return Url action for the pos web menu on clicking the menu item on
        dashboard."""
        self.ensure_one()
        # Raise user error if session not opened yet
        if not self.current_session_id:
            raise UserError(
                _('The restaurant is closed. You cannot browse the menu'))
        return {"type": "ir.actions.act_url",
                "url": self._get_web_menu_route(),
                "target": "new"}

    def _generate_unique_id(self, pos_session_id: int, table_id: int,
                            item_number: int) -> str:
        """A unique pos reference will be generated."""
        first_part = f"{int(pos_session_id):05d}"
        second_part = f"{int(table_id):03d}"
        third_part = f"{int(item_number):04d}"
        return f"Web-Order {first_part}-{second_part}-{third_part}"

    def create_order_from_web(self, cart_item, table, customer):
        """Pos order created
        :param dict cart_item: items added to pos web cart;
        :param int table: id of selected table from pos cart;
        :param int customer: id of selected customer;
        """
        session_id = self.current_session_id
        pos_order = self.env['pos.order'].sudo().search(
            [('user_id', '=', self.env.user.id), ('state', '=', 'draft'),
             ('table_id', '=', int(table))], limit=1)
        total = sum(item['lst_price'] for item in cart_item)
        unique_id = self._generate_unique_id(session_id.id, table,
                                             len(cart_item))
        # if there is no existing order in draft stage of pos order new
        # order will be created. Otherwise, product will be added to existing order.
        if not pos_order:
            order_item = {
                'session_id': session_id.id,
                'pos_reference': unique_id,
                'table_id': int(table),
                'partner_id': int(customer),
                'amount_total': total,
                'amount_tax': 0.0,
                'amount_paid': 0.0,
                'amount_return': 0.0}
            pos_order = self.env['pos.order'].create(order_item)
        for item in cart_item:
            if pos_order.partner_id.id != int(customer):
                return "False"
            line_product = pos_order.lines.filtered(
                lambda p: p.full_product_name == item['display_name'])
            if not line_product:
                total += item['lst_price']
                pos_lines = {'full_product_name': item['display_name'],
                             'product_id': int(item['id']),
                             'customer_note': item['cust_note'],
                             'price_unit': item['lst_price'],
                             'price_subtotal': item['lst_price'],
                             'price_subtotal_incl': item['lst_price'],
                             'total_cost': 50}
                pos_order.write({'lines': [Command.create(pos_lines), ]})
            quantity = line_product.qty
            line_product.write({'qty': quantity + 1})
