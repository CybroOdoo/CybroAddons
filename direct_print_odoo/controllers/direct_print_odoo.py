# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Prathyunnan R (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#############################################################################
import base64
import logging

from printnodeapi.gateway import Gateway

from odoo import http
from odoo.addons.web.controllers.report import ReportController
from odoo.http import request

_logger = logging.getLogger(__name__)


class ReportControllers(ReportController):
    """Send generated PDF reports to the configured PrintNode printers."""

    @http.route([
        '/report/<converter>/<reportname>',
        '/report/<converter>/<reportname>/<docids>',
    ], type='http', auth='user', website=True, readonly=True)
    def report_routes(self, reportname, docids=None, converter=None, **data):
        response = super().report_routes(
            reportname, docids=docids, converter=converter, **data
        )
        if (converter != 'pdf' or response.status_code >= 400
                or response.mimetype != 'application/pdf'):
            return response

        company = request.env.company.sudo()
        if not company.api_key_print_node:
            return response

        if company.is_multiple_printers:
            printer_ids = [
                printer.id_of_printer for printer in company.printers_ids
                if printer.id_of_printer
            ]
        elif company.available_printers_id:
            printer_id = company.available_printers_id.id_of_printer
            printer_ids = [printer_id] if printer_id else []
        else:
            printer_ids = []

        if not printer_ids:
            _logger.warning(
                "PrintNode API key is set, but no printers are configured "
                "for company %s", company.name,
            )
            return response

        try:
            encoded_pdf = base64.b64encode(response.get_data()).decode('utf-8')
            gateway = Gateway(
                url='https://api.printnode.com/',
                apikey=company.api_key_print_node,
            )
            for printer_id in printer_ids:
                _logger.info("Sending job to PrintNode printer %s", printer_id)
                gateway.PrintJob(
                    printer=int(printer_id),
                    options={"copies": 1},
                    title=f"Report_{reportname}",
                    job_type="pdf",
                    base64=encoded_pdf,
                )
        except Exception:
            _logger.exception(
                "Failed to send report %s to PrintNode", reportname
            )

        return response
