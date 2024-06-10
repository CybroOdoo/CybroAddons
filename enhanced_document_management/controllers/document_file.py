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


class DocumentPortalView(http.Controller):
    """Controller class for accessing documents from portal."""

    @http.route('/my/documents', type="http", auth="user", website=True)
    def document_in_portal(self):
        """
            Http controller to all user document from portal
            :return Http response with all Documents data
        """
        document_ids = request.env['document.file'].search([
            ('user_id.id', '=', request.uid)
        ])
        extensions = set(item.extension for item in document_ids)
        groups = [[rec for rec in document_ids if rec.extension == item
                   ] for item in extensions]
        return request.render(
            "enhanced_document_management.portal_my_documents", {
                'extensions': extensions,
                'base_url': request.httprequest.host_url[:-1],
                'document_ids': groups,
                'page_name': 'document',
            })

    @http.route('/my/document_request', type="http", auth="user",
                website=True)
    def document_request_in_portal(self):
        """
        Http controller to access user requests for document from portal
        :return Http response with all Documents data
        """
        request_ids = request.env['request.document'].search([
            ('user_id.id', '=', request.uid),
            ('state', '=', 'requested')
        ])
        context = [{
            'id': item.id,
            'needed_doc': item.needed_doc,
            'workspace_id': [item.workspace_id.id, item.workspace_id.name],
            'requested_by': [item.requested_by.id, item.requested_by.name],
            'user_id': [item.user_id.id, item.user_id.name],
            'date': item.create_date.date()
        } for item in request_ids]
        return request.render(
            "enhanced_document_management.portal_my_document_request",
            {
                'requests': context,
                'page_name': 'document_requests',
            })

    @http.route('/my/documents/<model("document.file"):doc>', type="http",
                auth="user", website=True)
    def document_view(self, doc):
        """
        Http controller to access document from portal
        :param doc: primary key of a record
        :return Http response with the selected Documents data
        """
        context = {
            'page_name': 'document',
            'document': True,
            'name': doc.name,
            'id': doc.id,
            'owner': doc.user_id,
            'attachment_id': doc.attachment_id.id,
            'brochure_url': doc.brochure_url,
            'workspace_id': doc.workspace_id.name,
            'date': doc.date,
            'url': f"""{request.httprequest.host_url[:-1]}/web/content/
                        {doc.attachment_id.id}/{doc.name}
                    """.replace('\n', '').replace(" ", ""),
            'partner_id': doc.partner_id.name,
            'extension': doc.extension,
            'preview': doc.preview,
            'content_url': doc.content_url,
            }
        return request.render("enhanced_document_management.portal_my_document_view",
                              context)
