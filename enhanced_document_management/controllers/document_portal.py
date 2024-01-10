# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request


class WebsiteCustomerPortal(CustomerPortal):
    """ Functon : Prepare portal values, datas are searched from document.file
        :return document count, request count
    """
    def _prepare_home_portal_values(self, counters):
        """Functon : Prepare portal values,
            datas are searched from document.file"""
        values = super(
            WebsiteCustomerPortal, self)._prepare_home_portal_values(counters)
        if 'document_count' in counters:
            values['document_count'] = request.env[
                'document.file'].sudo().search_count([
                    ('user_id.id', '=', request.uid)
                ])
            values['request_count'] = request.env[
                'request.document'].sudo().search_count([
                    ('user_id.id', '=', request.uid),
                    ('state', '=', 'requested')
                ])
        return values
