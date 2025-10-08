# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import api, models


class MailMessage(models.Model):
    """To manage recipients in the reply mail"""
    _inherit = "mail.message"

    @api.model
    def _get_reply_to(self, values):
        """ Return a specific reply_to for the document """
        model = values.get('model', self._context.get('default_model'))
        res_id = values.get('res_id',
                            self._context.get('default_res_id')) or False
        email_from = values.get('email_from')
        reply_to_id = self.env['ir.config_parameter'].sudo().get_param('reply_to')
        author1 = self.env['res.users'].browse(int(reply_to_id))
        self.env['ir.config_parameter'].sudo().set_param('reply_to', self.env.user.id)
        email_from1 = author1.email_formatted
        message_type = values.get('message_type')
        records = None
        if self.is_thread_message({'model': model, 'res_id': res_id,
                                   'message_type': message_type}):
            records = self.env[model].browse([res_id])
        else:
            records = self.env[model] if model else self.env['mail.thread']
        if author1.id == self.env.user:
            return records._notify_get_reply_to(default=email_from)[res_id]
        else:
            return records._notify_get_reply_to(default=email_from1)[res_id]
