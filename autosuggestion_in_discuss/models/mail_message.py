# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
import re
from odoo import api, models


HTML_TAG_PATTERN = re.compile(r'<.*?>')


class MailMessage(models.Model):
    """
    It inherits mail.message.
    Here adds a new function get_message()
     that searches previous messages of the current user,
     removes the markup, and returns the data.
    """
    _inherit = 'mail.message'

    @api.model
    def get_message(self):
        """
        Search previous messages of the current user in discuss.channel,
        remove the HTML markup, and return clean suggestion texts.
        """
        messages = self.search_read(
            [
                ('model', '=', 'discuss.channel'),
                ('author_id', '=', self.env.user.partner_id.id),
            ],
            ['body'],
        )
        suggestions = []
        for record in messages:
            body = record.get('body')
            if body:
                result = HTML_TAG_PATTERN.sub('', body).strip()
                if result and result not in suggestions:
                    suggestions.append(result)
        return suggestions

