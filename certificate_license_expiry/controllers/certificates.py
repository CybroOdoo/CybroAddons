# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo.http import request
from odoo.addons.portal.controllers import portal


class MyCertificates(http.Controller):
    """It returns the login person"""

    def _get_tickets_domain(self):
        """It returns the login person"""
        return [('customer_id', '=', request.env.user.partner_id.id)]

    @http.route(['/my/certificates'], type='http', auth="user", website=True)
    def get_my_certificates(self):
        """Take values from certificates and render to portal tree template """
        domain = self._get_tickets_domain()
        certificates = request.env['certificates'].sudo().search(domain)
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
        certificates = request.env['certificates'].sudo().search(
            [('id', '=', cer_id)])
        values = {
            'my_certificates': certificates,
        }
        return request.render(
            "certificate_license_expiry.certificates_portal_form_template",
            values)


class Return(portal.CustomerPortal):
    """This will take the count of total certificates"""

    def _prepare_home_portal_values(self, counters):
        """This will return the certificates count"""
        values = super(Return, self)._prepare_home_portal_values(counters)
        certificates = request.env['certificates'].sudo().search(
            [('customer_id', '=', request.env.user.partner_id.id)])
        count = len(certificates)
        values.update({
            'certificates': count
        })
        return values
