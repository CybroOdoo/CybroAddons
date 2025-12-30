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
from odoo import http
from odoo.http import request


class DocumentRequest(http.Controller):

    @http.route(['/document_request'], type='http', auth="user", website=True)
    def get_document_request(self):
        """This route is called whenever the user clicks on the
         'Document Request' menu on the website.
        It checks if the user is an internal user and retrieves
         their document requests, if authorized.
        :return: HTTP response containing the 'my_document_request'
         template with relevant data for the user's document requests.
        """
        if request.env.user.has_group(
                'enhanced_document_management.view_all_document'):
            values = {'document_requests': request.env[
                'document.template.request'].sudo().search(
                [('employee_id', '=', request.env.user.employee_id.id)]),
                'document_req_count': request.env[
                    'document.template.request'].sudo().
                search_count(
                    [('employee_id', '=', request.env.user.employee_id.id)])}
            return request.render(
                "enhanced_document_management.document_request_template",
                values)
        else:
            # Return an error message or redirect to an unauthorized page
            return "You are not authorized to access this page."

    @http.route(['/document_request/all'], type='http', auth="user",
                website=True)
    def get_all_document_request(self):
        """ This route is called whenever the user clicks on 'My' menu"""
        values = {
            'document_requests': request.env['document.template.request'].
            sudo().search([]), 'document_req_count': request.env[
                'document.template.request'].sudo().search_count([])}
        return request.render("enhanced_document_management.document_request_template",
                              values)

    @http.route(['/document_request/draft'], type='http', auth="user",
                website=True)
    def get_draft_document_request(self):
        """ This route is called whenever the user clicks on 'New' menu"""
        values = {'document_requests': request.env[
            'document.template.request'].sudo().search(
            [('state', '=', 'new')]),
            'document_req_count': request.env[
                'document.template.request'].sudo().search_count(
                [('state', '=', 'new')])}
        return request.render("enhanced_document_management.document_request_template",
                              values)

    @http.route(['/document_request/document_approval'], type='http',
                auth="user",
                website=True)
    def get_approval_document_request(self):
        """ This route is called whenever the user clicks on
        'Document Approval' menu"""
        values = {'document_requests': request.env[
            'document.template.request'].sudo().search(
            [('state', '=', 'document_approval')]),
            'document_req_count': request.env[
                'document.template.request'].sudo().search_count(
                [('state', '=', 'document_approval')])}
        return request.render("enhanced_document_management.document_request_template",
                              values)

    @http.route(['/document_request/new'], type='http', auth="user",
                website=True)
    def document_request_form(self):
        """ This route is called whenever the user clicks on
        'Document Request' menu in website"""
        values = {
            'employees': request.env['hr.employee'].sudo().search([]),
            'users': request.env['res.users'].sudo().search([]),
            'templates': request.env[
                'document.request.template'].sudo().search(
                []),
        }
        return request.render("enhanced_document_management.document_request_form",
                              values)

    @http.route(['/document_request/submit'], type='http', auth="user",
                website=True)
    def document_request_submit(self, **kwargs):
        """ This route is called whenever the user hits the 'Submit' button
        after filling the Service Request Form."""
        request_template = request.env['document.request.template'].browse(
            int(kwargs.get('document_request_template_id')))
        request.env['document.template.request'].sudo().create({
            'document_id': request_template.id,
            'manager_id': request_template.manager_id,
            'template': request_template.template,
            'stamp': request_template.stamp,
        })
        return request.render(
            'enhanced_document_management.document_request_submit_template')

    @http.route('/document_request/templates', type='json', auth="public")
    def get_document_request_template(self, **kw):
        """This route is called whenever a template is selected to render
        that template in UI"""
        return request.env['document.request.template'].browse(
            int(kw.get('template_id'))).template

    @http.route(['/document_request/details/request/<int:req_id>'],
                type='http', auth="user", website=True)
    def get_document_request_details(self, req_id):
        """ This route is called whenever the user clicks on
         'Document Request' menu in website"""
        values = {
            'document_request': request.env[
                'document.template.request'].sudo().browse(
                req_id)}
        return request.render("enhanced_document_management.document_request_details",
                              values)
