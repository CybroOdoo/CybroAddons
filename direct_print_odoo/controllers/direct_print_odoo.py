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
import json
import logging
import werkzeug
import werkzeug.exceptions
import werkzeug.utils
import werkzeug.wrappers
import werkzeug.wsgi
from printnodeapi.gateway import Gateway
from odoo import http, _
from odoo.addons.web.controllers.report import ReportController
from odoo.http import request

_logger = logging.getLogger(__name__)


class ReportControllers(ReportController):
    """Override Odoo report controller to send PDFs to PrintNode."""

    @http.route([
        '/report/<converter>/<reportname>',
        '/report/<converter>/<reportname>/<docids>',
    ], type='http', auth='user', website=True)
    def report_routes(self, reportname, docids=None, converter=None, **data):

        report_obj = request.env['ir.actions.report']
        context = dict(request.env.context)

        # ----- Parse docids -----
        if docids:
            docids = [int(i) for i in docids.split(',')]

        # ----- Parse options -----
        if data.get('options'):
            data.update(json.loads(data.pop('options')))

        # ----- Parse context -----
        if data.get('context'):
            data['context'] = json.loads(data['context'])
            context.update(data['context'])

        # ===========================================================
        # HTML Response
        # ===========================================================
        if converter == 'html':
            html = report_obj.with_context(context)._render_qweb_html(
                reportname, docids, data=data
            )[0]
            return request.make_response(html)

        # ===========================================================
        # TEXT Response
        # ===========================================================
        if converter == 'text':
            text = report_obj.with_context(context)._render_qweb_text(
                reportname, docids, data=data
            )[0]
            return request.make_response(text, headers=[
                ('Content-Type', 'text/plain'),
                ('Content-Length', len(text))
            ])

        # ===========================================================
        # PDF Response + PRINT TO PRINTNODE
        # ===========================================================
        if converter == 'pdf':

            pdf = report_obj.with_context(context)._render_qweb_pdf(
                reportname, docids, data=data
            )[0]

            # ------------------ PrintNode Integration ------------------

            company = request.env.company.sudo()

            # Optimization: Only attempt printing if API key is configured
            if company.api_key_print_node:
                printer_ids = []

                # Retrieve printer selection gracefully
                if company.is_multiple_printers:
                    printer_ids = [rec.id_of_printer for rec in company.printers_ids if rec.id_of_printer]
                else:
                    if company.available_printers_id:
                        printer_ids = [company.available_printers_id.id_of_printer]

                if not printer_ids:
                    _logger.warning("PrintNode API key is set, but no printers are configured for company %s",
                                    company.name)
                else:
                    try:
                        # Encode PDF to Base64
                        encoded_pdf = base64.b64encode(pdf).decode('utf-8')

                        # PrintNode Gateway
                        gateway = Gateway(
                            url='https://api.printnode.com/',
                            apikey=company.api_key_print_node
                        )

                        # Send Print Jobs
                        for printer in printer_ids:
                            _logger.info("Sending job to PrintNode printer %s", printer)
                            gateway.PrintJob(
                                printer=int(printer),
                                options={"copies": 1},
                                title=f"Report_{reportname}",
                                job_type="pdf",
                                base64=encoded_pdf
                            )
                    except Exception as e:
                        _logger.error("Failed to send job to PrintNode: %s", str(e))
                        # We specifically catch the error so that the user still 
                        # receives their PDF in the browser even if PrintNode fails.

            # Return PDF to Browser
            pdf_headers = [
                ('Content-Type', 'application/pdf'),
                ('Content-Length', len(pdf))
            ]
            return request.make_response(pdf, headers=pdf_headers)

        # ===========================================================
        # Unknown converter
        # ===========================================================
        raise werkzeug.exceptions.HTTPException(
            description=f"Converter {converter} not implemented."
        )
