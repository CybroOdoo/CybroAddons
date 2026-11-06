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
from odoo import http
from odoo.http import request

REQUEST_TYPES = ('download', 'delete')


class WebsiteGdpr(http.Controller):
    """Personal data page of the customer portal."""

    def _get_partner(self):
        """Return the contact of the logged in user."""
        return request.env.user.partner_id

    @http.route('/my/data_management', type='http', auth='user',
                website=True)
    def gdpr_data_management(self):
        """Show the GDPR templates and the requests of the customer."""
        partner = self._get_partner()
        return request.render('website_gdpr_odoo.gdpr_manager', {
            'templates': request.env['gdpr.template'].sudo().search([]),
            'gdpr_requests': request.env['gdpr.request'].sudo().search(
                [('partner_id', '=', partner.id)]),
        })

    @http.route('/gdpr_management/confirm', type='jsonrpc', auth='user',
                website=True)
    def data_management_confirm(self, template_id=None, req_type=None):
        """Create a download or delete request of the customer, unless the
        same request is already pending."""
        template = request.env['gdpr.template'].sudo().browse(
            int(template_id or 0)).exists()
        if not template or not template.active \
                or req_type not in REQUEST_TYPES:
            return {'status': 'error',
                    'message': request.env._('This request is not available.')}
        partner = self._get_partner()
        gdpr_request = request.env['gdpr.request'].sudo()
        domain = [('partner_id', '=', partner.id),
                  ('template_id', '=', template.id),
                  ('req_type', '=', req_type), ('state', '=', 'pending')]
        if gdpr_request.search_count(domain):
            return {'status': 'pending'}
        type_field = gdpr_request._fields['req_type']
        type_label = dict(type_field._description_selection(
            request.env))[req_type]
        gdpr_request.create({
            'req_name': f'{template.name}: {type_label}',
            'partner_id': partner.id,
            'req_type': req_type,
            'template_id': template.id,
        })
        return {'status': 'success'}

    @http.route('/gdpr_management/download/<int:request_id>', type='http',
                auth='user', website=True)
    def gdpr_download_pdf(self, request_id):
        """Download the PDF of an approved download request of the
        customer."""
        gdpr_request = request.env['gdpr.request'].sudo().browse(
            request_id).exists()
        if not gdpr_request \
                or gdpr_request.partner_id != self._get_partner() \
                or gdpr_request.req_type != 'download' \
                or gdpr_request.state != 'done':
            return request.redirect('/my/data_management')
        pdf_content, _type = request.env['ir.actions.report'].sudo(
        )._render_qweb_pdf('website_gdpr_odoo.action_pdf_download',
                           gdpr_request.ids)
        return request.make_response(pdf_content, headers=[
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf_content)),
            ('Content-Disposition',
             f'attachment; filename="{gdpr_request.name}.pdf"'),
        ])

    @http.route('/gdpr_management/submit', type='http', auth='user',
                website=True)
    def create_request_submit(self, status='success'):
        """Confirm to the customer that the request was sent."""
        return request.render('website_gdpr_odoo.gdpr_submit', {
            'status': status,
        })
