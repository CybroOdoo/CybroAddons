# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anjhana A K (odoo@cybrosys.com)
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
###############################################################################
import re
from odoo import api, models


class MailMessage(models.Model):
    """
    It inherits mail.message.
    Here adds a new function get_message()
     that searches messages in the html field
     mail_message, removes the markup,
     and returns the data.
    """
    _inherit = 'mail.message'

    @api.model
    def get_message(self):
        """
        Search messages in mail_message which is a html field
        and remove the markup and return the data.
        """
        value = []
        search = self.env['mail.message'].search_read(
            [('model', '=', 'discuss.channel')], ['body'])
        search_item = [values.get('body') for values in search]
        for record in search_item:
            pattern = re.compile('<.*?>')
            result = re.sub(pattern, '', record)
            value.append(result)
        return value
