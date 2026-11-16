# -*- coding: utf-8 -*-
#############################################################################
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
#############################################################################
import logging
from odoo import api, models
from printnodeapi.gateway import Gateway

_logger = logging.getLogger(__name__)

class PosOrder(models.Model):
    _inherit = "pos.order"

    def _get_printnode_api_key(self):
        """Retrieve PrintNode API key supporting Odoo 20 get_str and legacy get_param."""
        param_model = self.env['ir.config_parameter'].sudo()
        if hasattr(param_model, 'get_str'):
            return param_model.get_str('pos_direct_kitchen_print.api_key_print_node')
        return param_model.get_param('pos_direct_kitchen_print.api_key_print_node')

    @api.model
    def print_kitchen_order(self, order_data):
        """
        Entry point from POS JS to print kitchen tickets via PrintNode.
        Returns a dict with 'success' and 'message' to provide UI feedback.
        """
        pos_config_id = order_data.get("pos_config_id")
        printers = self.env["pos.kitchen.printer"].search([
            ("pos_config_ids", "in", [pos_config_id])
        ])

        if not printers:
            _logger.info("No kitchen printers configured for POS %s", pos_config_id)
            return {
                "success": False,
                "message": self.env._("No kitchen printers configured for this Point of Sale."),
            }

        api_key = self._get_printnode_api_key()
        if not api_key:
            _logger.warning("PrintNode API key not configured in Settings.")
            return {
                "success": False,
                "message": self.env._("PrintNode API Key is not configured. Please check POS settings."),
            }

        tickets = self._prepare_kitchen_tickets(order_data, printers)
        if not tickets:
            _logger.info("No order lines match configured kitchen printer categories.")
            return {
                "success": False,
                "message": self.env._("No order items match the configured kitchen printer categories."),
            }

        order_name = order_data.get("name", "New")
        success_printers = []
        failed_printers = []

        for printer, lines in tickets.items():
            success, err_msg = self._send_to_printnode(printer, lines, order_name, order_data=order_data)
            if success:
                success_printers.append(printer.name)
            else:
                failed_printers.append(f"{printer.name}: {err_msg}" if err_msg else printer.name)

        if failed_printers and not success_printers:
            return {
                "success": False,
                "message": self.env._("Failed to send print job: %(failed)s", failed="; ".join(failed_printers)),
            }
        elif failed_printers and success_printers:
            return {
                "success": True,
                "partial": True,
                "message": self.env._(
                    "Printed to: %(success)s. Failed: %(failed)s",
                    success=", ".join(success_printers),
                    failed="; ".join(failed_printers),
                ),
            }
        else:
            return {
                "success": True,
                "message": self.env._(
                    "Kitchen order printed successfully on: %(printers)s",
                    printers=", ".join(success_printers),
                ),
            }

    def _prepare_kitchen_tickets(self, order_data, printers):
        """
        Split order lines per printer based on product categories.
        """
        tickets = {}

        for printer in printers:
            printer_lines = []
            for line in order_data.get("lines", []):
                product = self.env["product.product"].browse(line["product_id"])
                # If printer has no specific categories configured, print all lines.
                # Otherwise, check if any printer category matches the product's POS categories.
                if not printer.category_ids or any(cat.id in product.pos_categ_ids.ids for cat in printer.category_ids):
                    printer_lines.append({
                        "qty": line.get("qty", 0),
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
        Returns tuple of (bool, str) representing success and error message.
        """
        if not lines:
            return False, self.env._("No lines to print.")

        api_key = self._get_printnode_api_key()
        if not api_key:
            _logger.error("PrintNode API Key not configured.")
            return False, self.env._("PrintNode API Key not configured in Settings.")

        if not printer.printer_id or not printer.printer_id.id_of_printer:
            _logger.error("Printer '%s' has no mapped PrintNode printer.", printer.name)
            return False, self.env._("Printer '%(name)s' has no mapped PrintNode printer.", name=printer.name)

        # Helper to parse internal note JSON
        def parse_internal_note(note_str):
            if not note_str or note_str == "[]":
                return ""
            try:
                import json
                note_data = json.loads(note_str)
                if isinstance(note_data, list):
                    return "\n".join([n.get('text', '') for n in note_data if n.get('text')])
            except Exception as e:
                _logger.debug("Could not parse internal note as JSON: %s", e)
            return note_str

        # Format the ticket message
        message = "━━━━━━━━━━━━━KITCHEN ORDER━━━━━━━━━━━━━\n"
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
            printer_id = int(printer.printer_id.id_of_printer)

            _logger.info("Sending kitchen job to PrintNode printer %s (%s)", printer_id, printer.name)
            gateway.PrintJob(
                printer=printer_id,
                job_type='raw',
                title=f"Kitchen Order - {order_name}",
                binary=message.encode('utf-8')
            )
            return True, ""
        except Exception as e:
            _logger.error("Failed to send print job to PrintNode for printer %s: %s", printer.name, str(e))
            return False, str(e)
