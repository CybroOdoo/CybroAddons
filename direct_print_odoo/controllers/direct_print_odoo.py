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
import base64
import json
import logging
from printnodeapi.gateway import Gateway
import werkzeug
import werkzeug.exceptions
import werkzeug.utils
import werkzeug.wrappers
import werkzeug.wsgi
from odoo import http, _
from odoo.addons.web.controllers.report import ReportController
from odoo.exceptions import ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)


class ReportControllers(ReportController):
    """Supering the report controllers for overriding the report_routes
    method"""

    # ------------------------------------------------------
    # Report controllers
    # ------------------------------------------------------
    @http.route([
        '/report/<converter>/<reportname>',
        '/report/<converter>/<reportname>/<docids>',
    ], type='http', auth='user', website=True)
    def report_routes(self, reportname, docids=None, converter=None, **data):
        """Overrides ReportController for printing the
        report to the corresponding printer"""
        report = request.env['ir.actions.report']
        context = dict(request.env.context)

        if docids:
            docids = [int(rec) for rec in docids.split(',')]
        if data.get('options'):
            data.update(json.loads(data.pop('options')))
        if data.get('context'):
            data['context'] = json.loads(data['context'])
            context.update(data['context'])
        if converter == 'html':
            html = report.with_context(context)._render_qweb_html(reportname,
                                                                  docids,
                                                                  data=data)[0]
            return request.make_response(html)
        elif converter == 'pdf':
            pdf = report.with_context(context)._render_qweb_pdf(reportname,
                                                                docids,
                                                                data=data)[0]
            default_printer = request.env.company.available_printers_id
            printer_det = request.env['printer.details'].browse(
                int(default_printer))
            multi_printer_details = [printer.id_of_printer for printer in
                                     request.env.company.printers_ids]
            if request.env.company.multiple_printers:
                gateway = Gateway(url='https://api.printnode.com/',
                                  apikey=request.env.company.api_key_print_node)
                data_record = base64.b64encode(pdf)
                ir_values = {
                    'name': "Customer Report",
                    'type': 'binary',
                    'datas': data_record,
                    'store_fname': data_record,
                    'mimetype': 'application/pdf',
                    'file_size': 25,
                    'public': True,
                }
                att = request.env['ir.attachment'].create(ir_values)
                request.env.cr.flush()
                request.env.cr.commit()
                request.env.cr.execute(
                    """ select id from public.ir_attachment where id=%s""",
                    [att.id])
                base_url = request.env['ir.config_parameter'].sudo().get_param(
                    'web.base.url')
                base_urls = '%s/web/content/%s' % (
                    base_url, request.env.cr.dictfetchone()['id'])
                if multi_printer_details:
                    for rec in multi_printer_details:
                        gateway.PrintJob(printer=int(rec),
                                         options={"copies": 1},
                                         uri=base_urls)
                else:
                    raise ValidationError(_(
                        'please select at least one printer'))
            else:
                gateway = Gateway(url='https://api.printnode.com/',
                                  apikey=request.env.company.api_key_print_node)
                data_record = base64.b64encode(pdf)
                ir_values = {
                    'name': "Customer Report",
                    'type': 'binary',
                    'datas': data_record,
                    'store_fname': data_record,
                    'mimetype': 'application/pdf',
                    'file_size': 25,
                    'public': True,
                }
                att = request.env['ir.attachment'].create(ir_values)
                request.env.cr.flush()
                request.env.cr.commit()
                request.env.cr.execute(
                    """ select id from public.ir_attachment where id=%s""",
                    [att.id])
                base_url = request.env['ir.config_parameter'].sudo().get_param(
                    'web.base.url')
                base_urls = '%s/web/content/%s' % (
                    base_url, request.env.cr.dictfetchone()['id'])
                if default_printer:
                    gateway.PrintJob(printer=int(printer_det.id_of_printer),
                                     options={"copies": 1},
                                     uri=base_urls)
                else:
                    raise ValidationError(_('Please select a printer.'))
            pdfhttpheaders = [('Content-Type', 'application/pdf'),
                              ('Content-Length', len(pdf))]
            return request.make_response(pdf, headers=pdfhttpheaders)
        elif converter == 'text':
            text = report.with_context(context)._render_qweb_text(reportname,
                                                                  docids,
                                                                  data=data)[0]
            texthttpheaders = [('Content-Type', 'text/plain'),
                               ('Content-Length', len(text))]
            return request.make_response(text, headers=texthttpheaders)
        else:
            raise werkzeug.exceptions.HTTPException(
                description='Converter %s not implemented.' % converter)
