# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.http.stream import content_disposition


class PurchaseFormatEditor(http.Controller):
    """The PurchaseFormatEditor class provides the functionality to
    download the preview of PDF"""

    @http.route('/purchase/pdf/preview', type="http", auth="user",
                methods=['GET'])
    def purchase_pdf_preview(self, layout_id=None, **kwargs):
        """The demo PDFs are downloaded using this controller.
        The HTML file from the preview compute field is then converted into
        binary PDFs and then returns a response to download it."""
        try:
            layout_id = int(layout_id)
        except (TypeError, ValueError):
            return request.not_found()

        layout = request.env['base.document.layout'].browse(layout_id).exists()
        if not layout:
            return request.not_found()
        try:
            layout.check_access('read')
        except AccessError:
            return request.not_found()

        pdf_data = request.env["ir.actions.report"]._run_wkhtmltopdf(
            [layout.preview])
        name = layout.document_layout_purchase_id.name or "preview"
        filename = f"{layout.base_layout_purchase or 'layout'} {name}.pdf"
        return request.make_response(pdf_data,
            headers=[
                ("Content-Type", "application/pdf"),
                ("Content-Length", len(pdf_data)),
                ("Content-Disposition", content_disposition(filename)),
                ("X-Content-Type-Options", "nosniff"),
            ],
        )
