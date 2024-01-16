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


class CertificatesGroupBy(http.Controller):
    """This is used to certificates group by in tree view"""

    @http.route(['/certificatesgroupby'], type='json', auth="public",
                website=True)
    def certificates_group_by(self, **kwargs):
        """Call from rpc for group by, and it returns the corresponding
        values"""
        context = []
        group_value = kwargs.get("search_value")
        if group_value == '1':
            context = []
            type_ids = request.env['certificates.types'].sudo().search([])
            for types in type_ids:
                certificates_ids = request.env['certificates'].sudo().search([
                    ('certificates_types_id', '=', types.id),
                    ('customer_id', '=', request.env.user.partner_id.id)
                ])
                if certificates_ids:
                    context.append({
                        'name': types.certificate_type,
                        'data': certificates_ids
                    })
        if group_value == '2':
            context = []
            tag_ids = request.env['certificates.tags'].sudo().search([])
            for tags in tag_ids:
                certificates_ids = request.env['certificates'].sudo().search([
                    ('certificates_tags_ids', '=', tags.id),
                    ('customer_id', '=', request.env.user.partner_id.id)
                ])
                if certificates_ids:
                    context.append({
                        'name': tags.certificates_tags_ids,
                        'data': certificates_ids
                    })
        values = {
            'certificates': context,
        }
        response = http.Response(
            template='certificate_license_expiry'
                     '.certificates_group_by_template',
            qcontext=values)
        return response.render()
