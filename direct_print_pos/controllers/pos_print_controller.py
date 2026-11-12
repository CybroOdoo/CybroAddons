# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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

import base64
import logging
from printnodeapi.gateway import Gateway
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class DirectPrintPOSController(http.Controller):

    @http.route('/pos/print_receipt_custom', type='jsonrpc', auth='user')
    def print_receipt_custom(self, order_id=None):
        """Generate a POS receipt PDF with a custom QWeb template and send it
        to the configured PrintNode printers.

        :param int order_id: ID of the POS order to print the receipt for.
        :return: Dictionary indicating success or failure.
        :rtype: dict
        """
        enable_pos_templates = request.env['ir.config_parameter'].sudo(
        ).get_param('direct_print_pos.enable_pos_templates')
        if not enable_pos_templates or enable_pos_templates == 'False':
            return {
                "success": False,
                "error": "Please enable POS template in the settings."
            }
        if not order_id:
            return {"success": False, "error": "Order ID is required"}

        order = request.env['pos.order'].browse(order_id)
        if not order.exists():
            return {"success": False,
                    "error": f"Order with ID {order_id} not found"}

        # Generate PDF using your custom template
        pdf_content, _ = request.env['ir.actions.report']._render_qweb_pdf(
            'direct_print_pos.action_report_pos_receipt_direct_print',
            [order.id]
        )
        # ------------------ PrintNode Integration ------------------
        company = order.company_id or request.env.company

        # Validate printer selection
        if company.is_multiple_printers:
            printer_ids = [rec.id_of_printer for rec in company.printers_ids
                           if rec.id_of_printer]
            if not printer_ids:
                return {
                    "success": False,
                    "error": "Please select at least one printer."
                }

        else:
            if not company.available_printers_id:
                return {
                    "success": False,
                    "error": "Please select a printer."
                }
            printer_ids = [company.available_printers_id.id_of_printer]

        # Send the PDF directly to PrintNode to avoid download URL issues.
        encoded_pdf = base64.b64encode(pdf_content).decode('utf-8')
        gateway = Gateway(url='https://api.printnode.com/',
                          apikey=company.api_key_print_node)

        try:
            for printer in printer_ids:
                gateway.PrintJob(
                    printer=int(printer),
                    options={"copies": 1},
                    title=f"POS_{order.name}",
                    job_type="pdf",
                    base64=encoded_pdf,
                )
        except Exception as exc:
            _logger.exception(
                "POS direct print failed for order %s", order.name)
            return {
                "success": False,
                "error": f"PrintNode request failed: {exc}",
            }
        return {
            "success": True,
        }
