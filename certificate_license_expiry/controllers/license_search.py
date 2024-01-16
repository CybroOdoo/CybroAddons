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


class MyLicenseSearch(http.Controller):
    """This is used to search feature in license portal tree view"""

    @http.route(['/licensesearch'], type='json', auth="public", website=True)
    def license_search(self, **kwargs):
        """It gives the values and return the response to corresponding
        template"""
        search_value = kwargs.get("search_value")
        license = request.env["license"].sudo().search(
            [('customer_id', '=',
              request.env.user.partner_id.id)]) if not search_value else \
        request.env["license"].sudo().search(
            [('license_number', '=', search_value),
             ('customer_id', '=', request.env.user.partner_id.id)])
        values = {
            'license': license,
        }
        response = http.Response(
            template='certificate_license_expiry.portal_my_license_tree',
            qcontext=values)
        return response.render()
