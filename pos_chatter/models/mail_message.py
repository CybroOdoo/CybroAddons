# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Gee Paul Joby (odoo@cybrosys.com)
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
################################################################################
from odoo import models, fields , api


class MailMessage(models.Model):
    _inherit = "mail.message"

    is_read = fields.Boolean(string="Read", default=False)

    @api.model
    def compute_read_message(self, datas):
        try:
            messages = self.env['mail.message'].search([
                ('model', '=', 'discuss.channel'),
                ('res_id', '=', datas),
                ('is_read', '=', False)
            ])
            for message in messages:
                if message.is_read is False:
                    message.write({'is_read': True})
                    print(f"Marked messages as read: {message.ids}")
                else:
                    print("No unread messages found.")
        except Exception as e:
            print(f"An error occurred: {str(e)}")
