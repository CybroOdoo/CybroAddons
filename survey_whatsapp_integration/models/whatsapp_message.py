# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ammu Raj(odoo@cybrosys.com)
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
from odoo import fields, models


class WhatsappMessage(models.Model):
    """Create new model for viewing the History"""
    _name = "whatsapp.message"
    _description = "Whatsapp Message"
    _rec_name = 'to_user'

    status = fields.Char(string="Status",
                         help="status of whatsapp messages")
    from_user = fields.Many2one('res.users', string="Sent From",
                                help="from user in whatsapp messages",
                                required=True)
    to_user = fields.Char(string="Sent to",
                          help="to user in whatsapp messages", required=True)
    body = fields.Char(string="Message",
                       help="Message body in whatsapp messages", required=True)
