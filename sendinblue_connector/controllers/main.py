import json
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class SendinBlueRequest(http.Controller):

    @http.route(['/send-in-blue'], auth='public', csrf=False, type='json', methods=['POST'])
    def sent(self, **kw):
        data = json.loads(request.httprequest.data)
        _request = data
        _logger.info(data)
        blue_message_id = data['message-id']
        event = data['event']
        partner_email = data['email']
        message_id = request.env['mail.message'].sudo().search([('message_id', 'ilike', blue_message_id)])
        message_id.sudo().write({
            'status': event,
            'to': partner_email,
        })
        if event == 'click':
            links_clicked = data['link']
        else:
            links_clicked = ''
            return 'ok', 200
