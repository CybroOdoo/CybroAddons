# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
###############################################################################
import logging
from odoo import api, models
from printnodeapi.gateway import Gateway

_logger = logging.getLogger(__name__)

class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model
    def print_kitchen_order(self, order_data):
        """
        Entry point from POS JS to print kitchen tickets via PrintNode.
        """
        # Find printers configured for this POS
        pos_config_id = order_data.get("pos_config_id")
        printers = self.env["pos.kitchen.printer"].search([
            ("pos_config_ids", "in", [pos_config_id])
        ])
        
        if not printers:
            return True

        tickets = self._prepare_kitchen_tickets(order_data, printers)

        # Send to PrintNode
        order_name = order_data.get("name", "New")
        for printer, lines in tickets.items():
            self._send_to_printnode(printer, lines, order_name, order_data=order_data)

        return True

    def _prepare_kitchen_tickets(self, order_data, printers):
        """
        Split order lines per printer based on product categories.
        """
        tickets = {}

        for printer in printers:
            printer_lines = []
            printer_cat_ids = printer.category_ids.ids
            for line in order_data.get("lines", []):
                product = self.env["product.product"].browse(line["product_id"])
                prod_cat_ids = product.pos_categ_ids.ids
                is_match = not printer.category_ids or any(cat_id in prod_cat_ids for cat_id in printer_cat_ids)
                if is_match:
                    printer_lines.append({
                        "qty": line["qty"],
                        "name": line.get("full_product_name") or product.display_name,
                        "customer_note": line.get("customer_note", ""),
                        "internal_note": line.get("internal_note", ""),
                    })
            
            if printer_lines:
                tickets[printer] = printer_lines

        return tickets

    def _send_to_printnode(self, printer, lines, order_name, order_data=None):
        """
        Send formatted text to PrintNode via Enterprise API.
        """
        if not lines:
            return

        # Get API Key from config
        api_key = self.env['ir.config_parameter'].sudo().get_param('pos_direct_kitchen_print.api_key_print_node')
        if not api_key:
            _logger.error("[pos_direct_kitchen_print] PrintNode API Key not configured in System Parameters (pos_direct_kitchen_print.api_key_print_node).")
            return

        # Helper to parse internal note JSON
        def parse_internal_note(note_str):
            if not note_str or note_str == "[]":
                return ""
            try:
                import json
                note_data = json.loads(note_str)
                if isinstance(note_data, list):
                    return "\n".join([n.get('text', '') for n in note_data if n.get('text')])
            except Exception:
                pass
            return note_str

        # Format the ticket message
        message = f"━━━━━━━━━━━━━KITCHEN ORDER━━━━━━━━━━━━━\n"
        message += f"Order: {order_name}\n"
        
        if order_data:
            order_type = order_data.get('order_type')
            if order_type:
                message += f"Type: {order_type}\n"

            table_name = order_data.get('table_name')
            if table_name:
                message += f"Table: {table_name}\n"
            
            cust_note = order_data.get('order_customer_note')
            int_note = parse_internal_note(order_data.get('order_internal_note'))
            if cust_note:
                message += f"Order Note: {cust_note}\n"
            if int_note:
                message += f"Order Message: {int_note}\n"

        message += "━━" * 20 + "\n"
        for line in lines:
            name = line.get('name', '')
            if '(' in name:
                parts = name.split('(', 1)
                main_name = parts[0].strip()
                extras = '(' + parts[1].strip()
                message += f"{line['qty']} x {main_name}\n"
                message += f"  {extras}\n"
            else:
                message += f"{line['qty']} x {name}\n"
            if line.get('customer_note'):
                message += f"  Customer Note: {line['customer_note']}\n"
            
            line_int_note = parse_internal_note(line.get('internal_note'))
            if line_int_note:
                message += f"  Note: {line_int_note}\n"
        message += "━━" * 20 + "\n"

        try:
            gateway = Gateway(url="https://api.printnode.com", apikey=api_key)
            if not printer.printer_id or not printer.printer_id.id_of_printer:
                _logger.error("[pos_direct_kitchen_print] Kitchen printer '%s' has no valid PrintNode printer ID associated.", printer.name)
                return

            printer_id = int(printer.printer_id.id_of_printer)

            job = gateway.PrintJob(
                printer=printer_id,
                job_type='raw',
                title="Kitchen Order",
                binary=message.encode('utf-8')
            )
        except Exception as e:
            _logger.error("[pos_direct_kitchen_print] Failed to send print job to PrintNode: %s", str(e), exc_info=True)
