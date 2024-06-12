# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
from odoo import fields, models


class WhatsappMessage(models.Model):
    """Create a new model to capture all messages sent through WhatsApp."""
    _name = "whatsapp.message"
    _description = "Whatsapp Message"
    _rec_name = 'res_name'

    res_name = fields.Char(related="attachment_id.res_name",
                           help='The name of the attachment '
                                'that is sent to WhatsApp.')
    status = fields.Char(string="Status",
                         help="Status of whatsapp messages")
    from_user_id = fields.Many2one('res.users', string="Sent From",
                                   help="From user in whatsapp messages",
                                   required=True)
    to_user = fields.Char(string="Sent to",
                          help="To user in whatsapp messages", required=True)
    user_name = fields.Char(string="Partner Name",
                            help="Name of partner in whatsapp messages",
                            required=True)
    body = fields.Char(string="Message",
                       help="Message body in whatsapp messages", required=True)
    attachment_id = fields.Many2one('ir.attachment', string='Attachments',
                                    help='Added POS attachments')
    date_and_time_sent = fields.Datetime(string="Date and Time",
                                         help='The date and time when the '
                                              'message was sent to WhatsApp.')
