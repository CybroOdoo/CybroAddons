# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (Contact : odoo@cybrosys.com)
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
################################################################################
from odoo import http
from odoo.http import request


class WebsiteForm(http.Controller):
    """
    The WebsiteForm class provides the data to the page when it's loaded.
        Methods:
            gdpr_data_management(self):
                When the page is loaded passing the values related to the gdpr
                template and requests.
                Return a dict variable.
            data_management_confirm(self,**kw):
               Creating gdpr requests based the type of request and the user.
            create_request_submit(self):
                Opening the submit window.
            request_delete_done(self):
                Opening the deleted window.
            request_canceled(self):
                opening the cancelled window.
    """

    @http.route(['/my/data_management'], type='http', auth="user",
                website=True)
    def gdpr_data_management(self):
        """
        Summary:
            Transferring data to the frontend
        Returns:
            Type:dict , it contains the data for the opening window.
        """
        return request.render("website_gdpr_odoo.gdpr_manager", {
            'values': [{'name': gdpr_template_id['name'],
                        'description': gdpr_template_id['description'],
                        'id': gdpr_template_id['id'], } for gdpr_template_id in
                       request.env['gdpr.template'].sudo().search_read([],
                                                                       ['name',
                                                                        'description'])],
            'request_values': [{
                'name': gdpr_request_id.req_name,
                'partner': gdpr_request_id.partner_id.name,
                'date': gdpr_request_id.create_date,
                'state': gdpr_request_id.state,
                'type': gdpr_request_id.req_type,
                'template': gdpr_request_id.template_id.name,
                'id': gdpr_request_id.id
            } for gdpr_request_id in request.env['gdpr.request'].sudo().search(
                [('partner_id', '=', request.env.user.partner_id.id)])],
        })

    @http.route(['/gdpr_management/confirm'], type='json', auth="public",
                website=True)
    def data_management_confirm(self, **kw):
        """
        Summary:
            Transferring data to the frontend
        Arguments:
            kw: dictionary
                It contains selected template id user id.
        """
        if kw.get('user_id'):
            partner_id = request.env['res.users'].browse(
                kw.get('user_id')).partner_id
            request.env['gdpr.request'].sudo().create({
                'req_name': f"{partner_id.name}'s {kw.get('type')} data",
                'partner_id': partner_id.id,
                'req_type': kw.get('type'),
                'state': 'pending',
                'template_id': kw.get('template_id')
            })
        else:
            request.redirect('/my/home')

    @http.route(['/gdpr_management/submit'], type='http', auth="user",
                website=True)
    def create_request_submit(self):
        """
        Summary:
            Opening submit window
        """
        return request.render("website_gdpr_odoo.gdpr_submit")

    @http.route(['/gdpr_management/success/delete'], type='http',
                auth="user", website=True)
    def request_delete_done(self):
        """
        Summary:
            Opening delete window
        """
        return request.render("website_gdpr_odoo.gdpr_delete_success")

    @http.route(['/gdpr_management/canceled'], type='http', auth="user",
                website=True)
    def request_canceled(self):
        """
        Summary:
            Opening cancel window
        """
        return request.render("website_gdpr_odoo.gdpr_cancel_success")
