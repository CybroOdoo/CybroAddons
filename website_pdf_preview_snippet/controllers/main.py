# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anfas Faisal K (odoo@cybrosys.info)
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
################################################################################
import base64

from odoo.http import request
from odoo import http


class WebsitePDFPreviewController(http.Controller):
    @http.route('/file/uploaded/', type='http', auth="public", website=True,
                csrf=False)
    def upload_files(self, **post):
        """Upload files"""
        if post.get('attachment', False):
            if not post.get('attachment').filename.endswith('.pdf'):
                return request.render('website_pdf_preview_snippet.upload_error_template', {
                })
            attachment = post.get('attachment').read()
            request.env['ir.attachment'].create([{
                'name': post.get('attachment').filename,
                'datas': base64.b64encode(attachment),
            }])
            pdfhttpheaders = [
                ("Content-Type", "application/pdf"),
                ("Content-Length", len(attachment)),
            ]
            res = request.make_response(attachment, headers=pdfhttpheaders)
            return res
