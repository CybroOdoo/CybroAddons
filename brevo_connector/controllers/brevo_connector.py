# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Farhana Jahan PT(odoo@cybrosys.com)
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
#############################################################################
import json
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class BrevoRequest(http.Controller):
    """Controller for setting routes. Pass all statuses of mail to odoo"""

    @http.route('/brevo', type='json', auth='public', methods=['POST'])
    def sent(self):
        """Function for getting statuses into odoo"""
        data = json.loads(request.httprequest.data)
        _logger.info(data)
        message_id = request.env['mail.message'].sudo().search(
            [('message_id', 'ilike', data['message-id'])], limit=1)
        if message_id:
            message_id.write({
                'status': data.get('event'),
                'receiver': data.get('email'),
            })
        if data.get('event') == 'click':
            data.get('link')
        else:
            return 'ok', 200
