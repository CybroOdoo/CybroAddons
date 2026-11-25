# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import http
from odoo.addons.portal.controllers import portal
from odoo.http import request


class MyCertificates(http.Controller):
    """It returns the login person"""

    def _get_tickets_domain(self):
        """It returns the login person"""
        return [('customer_id', '=', request.env.user.partner_id.id)]

    @http.route(['/my/certificates'], type='http', auth="user", website=True)
    def get_my_certificates(self):
        """Take values from certificates and render to portal tree template """
        domain = self._get_tickets_domain()
        certificates = request.env['certificate.certificate'].sudo().search(domain)
        values = {
            'certificates': certificates,
        }
        return request.render(
            "certificate_license_expiry.portal_my_certificates", values)

    @http.route(['/my/certificates/form/<int:cer_id>'], type='http',
                auth="user", website=True)
    def get_my_certificates_form(self, cer_id):
        """Take values from certificates and render to portal form
        template.It also passes the id in the root for rendering the
        corresponding form template"""
        certificates = request.env['certificate.certificate'].sudo().search([
            ('id', '=', cer_id),
            ('customer_id', '=', request.env.user.partner_id.id),
        ])
        if not certificates:
            return request.redirect('/my/certificates')
        values = {
            'my_certificates': certificates,
        }
        return request.render(
            "certificate_license_expiry.certificates_portal_form_template",
            values)


class CertificatePortal(portal.CustomerPortal):
    """This will take the count of total certificates"""

    def _prepare_home_portal_values(self, counters):
        """This will return the certificates count"""
        values = super()._prepare_home_portal_values(counters)
        if 'certificates' in counters:
            values['certificates'] = request.env['certificate.certificate'].sudo().search_count([
                ('customer_id', '=', request.env.user.partner_id.id),
            ])
        return values
