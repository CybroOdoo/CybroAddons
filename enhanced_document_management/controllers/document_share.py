# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
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
