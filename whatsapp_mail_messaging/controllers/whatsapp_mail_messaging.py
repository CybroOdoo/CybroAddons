# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
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
from odoo import http
from odoo.http import request


class SendMessage(http.Controller):
    """ Controller for whatsapp message templates """
    @http.route('/whatsapp_message', type='json', auth='public')
    def whatsapp_message(self, **kwargs):
        """ Whatsapp message templates """
        messages = request.env['selection.message'].sudo().search_read(
            fields=['name', 'message'])
        return {'messages': messages}

    @http.route('/mobile_number', type='json', auth='public')
    def mobile_number(self, **kwargs):
        """ Mobile number of website """
        mobile_number = request.env['website'].sudo().search_read(
            fields=['mobile_number']
        )
        return {'mobile': mobile_number}
