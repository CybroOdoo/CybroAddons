# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mruthul Raj(<https://www.cybrosys.com>)
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
import io
import zipfile
from odoo import http
from odoo.http import request


class DocumentFile(http.Controller):
    """Http Controller to create sharable view for selected documents """

    @http.route('/web/content/share/', type='http', auth='public',
                website='True')
    def document_share(self, **kwargs):
        """Share a document and prepare the context for rendering.
        :param kwargs: A dictionary containing the 'unique' key for
         identifying the document to share.
        :type kwargs: Dict
        :return: Rendered document_share_preview
         template with the prepared context.
        :rtype: Http.Response"""
        folder_ids = request.env['document.share'].sudo().search([
            ('unique_id', '=', kwargs.get('unique'))])
        context = ({
            'doc_id': document.id,
            'doc_name': document.name,
            'doc_extension': document.extension,
            'doc_owner': document.user_id,
            'doc_date': document.date,
            'doc_url': document.content_url,
        } for document in folder_ids.document_ids)
        return http.request.render(
            'enhanced_document_management.document_share_preview', {'context': context}
        )

    @http.route("/get/document", type="http", auth='public',
                website='True')
    def download_zip(self):
        """
        HTTP controller to download selected files as a ZIP archive.
        This controller takes a list of document IDs as input,
         creates a ZIP archive
        containing those documents, and sends it as a response for download.
        :return: HTTP response containing the ZIP archive.
        :rtype: Http.Response
        """
        param_value = request.params.get('param')
        param_list = eval(param_value)
        zip_data = io.BytesIO()
        with zipfile.ZipFile(zip_data, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for doc in request.env['document.file'].sudo().browse(param_list):
                if doc.content_type != "url":
                    zipf.write(doc.attachment_id._full_path(
                        doc.attachment_id.store_fname), doc.attachment_id.name)
        headers = [
            ('Content-Type', 'application/zip'),
            ('Content-Disposition', http.content_disposition('archive.zip')),
        ]
        return request.make_response(zip_data.getvalue(), headers)
