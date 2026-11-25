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
from werkzeug.exceptions import NotFound

from odoo import http
from odoo.http import request
from odoo.http.stream import content_disposition


class TenderExportController(http.Controller):
    """Download of the product lines of a tender as an XLSX template."""

    @http.route('/tender/<int:tender_id>/product_template', type='http', auth='user')
    def download_product_template(self, tender_id, **_kwargs):
        """Return the XLSX file of the tender product lines."""
        tender = request.env['tender.management'].browse(tender_id).exists()
        if not tender:
            raise NotFound()
        tender.check_access('read')
        return request.make_response(tender._get_product_template_xlsx(), headers=[
            ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('Content-Disposition', content_disposition(f'{tender.name} - Products.xlsx')),
        ])
