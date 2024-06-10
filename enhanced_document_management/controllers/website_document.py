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
import base64
from odoo import fields
from odoo import http
from odoo.http import request


class WebsiteDocumentsUpload(http.Controller):
    """Controller for accept document upload form submission"""

    @http.route('/website/documents', type="http", auth="user",
                website=True, csrf=False)
    def website_docs(self, **post):
        """
        Function : website form submit controller,
        it creates a record in document.file
        :param post: form-data
        :return: redirect
        """
        val_list = {
            'name': post['file'].filename,
            'attachment': base64.b64encode(post['file'].read()),
            'workspace_id': int(post['workspace']),
            'date': fields.Date.today(),
            'user_id': request.uid,
            'description':  post['reason'],
            'security': 'private',
            'extension': post['file'].filename.split(".")[
                len(post['file'].filename.split(".")) - 1]
        }
        if post['security'] == 'Private':
            val_list['security'] = 'private'
        else:
            val_list['security'] = 'managers_and_owner'
        file_id = request.env['document.file'].create(val_list)
        file_id.action_upload_document()
        return request.redirect("/my/documents")

    @http.route('/website/documents_request', type="http", auth="user",
                website=True, csrf=False)
    def website_docs_request(self, **post):
        """
            Function : website form submit controller for requested documents,
            it creates a record in document.file
            :param post: form-data
            :return: redirect to /my/document_request
        """
        request_id = request.env['request.document'].browse(
            int(post['rec_id']))
        file_id = request.env['document.file'].sudo().create({
            'name': post['file'].filename,
            'attachment': base64.b64encode(post['file'].read()),
            'workspace_id': int(post['workspace']),
            'date': fields.Date.today(),
            'user_id': request.uid,
            'description': post['reason'],
            'security': 'specific_users',
            'user_ids': [post['requested_by']],
            'extension': post['file'].filename.split(".")[
                len(post['file'].filename.split(".")) - 1]
        })
        file_id.action_upload_document()
        request_id.state = 'accepted'
        return request.redirect("/my/document_request")

    @http.route('/website/documents_request_reject', type="http",
                auth="user", website=True, csrf=False)
    def document_request_reject(self, **post):
        """
        Function accept document reject and update document.request
        :param post: form-data
        :return: redirect to /my/document_request
        """
        request_id = request.env['request.document'].browse(
            int(post['req_id']))
        request_id.state = 'rejected'
        request_id.reject_reason = post['reason']
        return request.redirect("/my/document_request")
