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


class MyCertificatesSearch(http.Controller):
    """This is used to search feature in certificates portal tree view"""

    @http.route(['/certificatesearch'], type='json', auth="public",
                website=True)
    def certificates_search(self, **kwargs):
        """It gives the values and return the response to corresponding
        template"""
        search_value = kwargs.get("search_value")
        if not search_value:
            certificates = request.env["certificates"].sudo().search(
                [('customer_id', '=', request.env.user.partner_id.id)])
        else:
            certificates = request.env["certificates"].sudo().search(
                [('certificate_number', '=', search_value),
                 ('customer_id', '=', request.env.user.partner_id.id)])
        values = {
            'certificates': certificates,
        }
        response = http.Response(
            template='certificate_license_expiry.portal_my_certificates_tree',
            qcontext=values)
        return response.render()
