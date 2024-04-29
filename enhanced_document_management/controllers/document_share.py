# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Paid App Development Team (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from odoo import http
from odoo.http import request


class DocumentFile(http.Controller):
    """Http Controller to create sharable view for selected documents """

    @http.route('/web/content/share/', type='http', auth='public',
                website='True')
    def document_share(self, **kwargs):
        """Function that returns a list of documents
            that grouped by unique link"""
        folder_ids = request.env['document.share'].sudo().search([
            ('unique', '=', kwargs.get('unique'))
        ], limit=1)
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

    @http.route("/web/attachments/download", type="http")
    def download_zip(self):
        """ Http Controller to download selected file as a ZIP """
        return http.send_file(
            filepath_or_fp='./attachments.zip',
            mimetype="application/zip",
            as_attachment=True,
            filename="attachments.zip",
        )
