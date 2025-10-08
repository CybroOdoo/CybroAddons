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
        # Define subtypes to exclude (Notes)
        excluded_subtypes = [
            request.env.ref('mail.mt_note').id,
        ]
        message_id = request.env['mail.message'].sudo().search([
            ('message_id', '=', data['message-id']),
            ('message_type', 'in', ['email', 'comment', 'user_notification', 'auto_comment']),
            ('subtype_id', 'not in', excluded_subtypes)], limit=1)
        if message_id:
            # Update the mail.message with status and receiver
            message_id.write({
                'status': data.get('event'),
                'receiver': data.get('email'),
            })
            # Handle click events (log the clicked link)
            if data.get('event') == 'click' and data.get('link'):
                _logger.info("Click event recorded for message %s: Link %s",
                             message_id.id, data.get('link'))
        return {'status': 'ok'}
