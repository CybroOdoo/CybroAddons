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


class LicenseGroupBy(http.Controller):
    """This is used to license group by in tree view"""

    @http.route(['/licensegroupby'], type='json', auth="public", website=True)
    def license_group_by(self, **kwargs):
        """Call from rpc for group by, and it returns the corresponding
        values"""
        context = []
        group_value = kwargs.get("search_value")
        if group_value == '1':
            context = []
            type_ids = request.env['license.types'].sudo().search([])
            for types in type_ids:
                license_ids = request.env['license'].sudo().search([
                    ('license_types_id', '=', types.id),
                    ('customer_id', '=', request.env.user.partner_id.id)
                ])
                if license_ids:
                    context.append({
                        'name': types.license_type,
                        'data': license_ids
                    })
        if group_value == '2':
            context = []
            tag_ids = request.env['license.tags'].sudo().search([])
            for tags in tag_ids:
                license_ids = request.env['license'].sudo().search([
                    ('license_tags_ids', '=', tags.id),
                    ('customer_id', '=', request.env.user.partner_id.id)
                ])
                if license_ids:
                    context.append({
                        'name': tags.license_tags_ids,
                        'data': license_ids
                    })
        values = {
            'license': context,
        }
        response = http.Response(
            template='certificate_license_expiry.license_group_by_template',
            qcontext=values)
        return response.render()
