# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Albin PJ (odoo@cybrosys.com)
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
###############################################################################
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers import portal


class MyLicense(http.Controller):
    """It returns the login person"""

    def _get_tickets_domain(self):
        """It returns the login person"""
        return [('customer_id', '=', request.env.user.partner_id.id)]

    @http.route(['/my/license'], type='http', auth="user", website=True)
    def get_my_license(self):
        """Take values from licenses and render to portal tree template """
        domain = self._get_tickets_domain()
        license = request.env['license'].sudo().search(domain)
        values = {'license': license,
                  }
        return request.render(
            "certificate_license_expiry.portal_my_license", values)

    @http.route(['/my/license/form/<int:lic_id>'], type='http', auth="user",
                website=True)
    def get_my_license_form(self, lic_id):
        """Take values from license and render to portal form template.It
        also passes the id in the root for rendering the corresponding form
        template"""
        license = request.env['license'].sudo().search([('id', '=', lic_id)])
        values = {
            'my_license': license,
        }
        return request.render(
            "certificate_license_expiry.license_portal_form_template",
            values)


class Return(portal.CustomerPortal):
    """This will take the count of total license"""

    def _prepare_home_portal_values(self, counters):
        """This will return the license count"""
        values = super(Return, self)._prepare_home_portal_values(counters)
        license = request.env['license'].sudo().search(
            [('customer_id', '=', request.env.user.partner_id.id)])
        count = len(license)
        values.update({
            'license': count
        })
        return values
