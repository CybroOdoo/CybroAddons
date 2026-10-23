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
import json
import xml.etree.ElementTree as ET
from odoo import http
from odoo.http import request
from odoo.http.stream import content_disposition
from odoo.tools import html_escape


class XLSXReportController(http.Controller):
    """Excel report for one2many fields"""

    @http.route('/xlsx_reports', type='http', auth='user', methods=['POST'],
                csrf=False)
    def get_report_xlsx(self, report_name='excel', **kwargs):
        """Used to get the report data that are fetched from the one2many"""
        model = kwargs.get('current_model')
        model_id = kwargs.get('id')
        field = kwargs.get('field')

        # Security check: Model must be valid and registered in the environment
        if not model or model not in request.env:
            return request.not_found()

        model_pool = request.env[model]

        # Enforce read access permissions for the current user (NO sudo)
        try:
            model_pool.check_access('read')
        except Exception:
            return request.make_response("Access Denied", status=403)

        model_id_val = False
        if model_id and str(model_id).lower() not in ('false', 'none', 'undefined', '0', ''):
            try:
                model_id_val = int(model_id)
            except (ValueError, TypeError):
                model_id_val = False

        # Determine column names from list view arch or model fields
        names = []
        views = request.env['ir.ui.view'].search([
            ('model', '=', model),
            ('type', '=', 'list')
        ], order='priority asc, id asc', limit=1)
        if views and views.arch:
            try:
                arch_str = views.arch if isinstance(views.arch, str) else str(views.arch)
                tree = ET.fromstring(arch_str)
                names = [f.get('name') for f in tree.findall('.//field') if f.get('name')]
            except Exception:
                names = []

        # Filter names to existing fields on the model
        names = [fn for fn in names if fn in model_pool._fields]

        # Fallback if names empty
        if not names:
            names = [fn for fn, fobj in model_pool._fields.items()
                     if fobj.store and fobj.type not in ('one2many', 'many2many', 'binary')]

        # Prevent data leakage: only search if model_id is a valid integer and field exists.
        # If id=False (unsaved record) or field is missing, return empty data (NEVER domain = [])
        if model_id_val and field and field in model_pool._fields:
            domain = [(field, '=', model_id_val)]
            # Use standard user environment without sudo to respect ACLs and record rules
            report_data = model_pool.search_read(
                domain=domain,
                fields=names
            )
        else:
            report_data = []

        report_obj = request.env['one2many.report.excel']
        try:
            response = request.make_response(
                None,
                headers=[
                    ('Content-Type', 'application/vnd.ms-excel'),
                    ('Content-Disposition',
                     content_disposition(report_name + '.xlsx'))
                ]
            )
            report_obj.get_xlsx_report(report_data, names or ['id'], response)
            return response
        except Exception as e:
            try:
                from odoo.http.dispatcher import serialize_exception
                se = serialize_exception(e)
            except Exception:
                se = {'name': type(e).__name__, 'message': str(e)}
            error = {
                'code': 200,
                'message': 'Odoo Server Error',
                'data': se
            }
            return request.make_response(html_escape(json.dumps(error)))

