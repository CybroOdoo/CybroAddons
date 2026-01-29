# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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

from odoo import http
from odoo.http import request


class MessagePost(http.Controller):

    @http.route('/message/post', methods=['POST'], type='json', auth='public')
    def message_post(self, thread_model, thread_id, post_data):
        """
            this function is for message sending
        """
        data = json.loads(request.httprequest.data)
        channel = request.env['mail.channel'].browse(int(thread_id))
        channel.message_post(body=post_data['body'], message_type='comment',
                             subtype_xmlid='mail.mt_comment')
