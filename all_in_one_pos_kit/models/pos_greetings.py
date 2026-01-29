# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Haseen (odoo@cybrosys.com)
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


class POSGreetings(models.Model):
    """Model representing POS Greetings."""
    _name = 'pos.greetings'
    _description = 'POS Greetings'
    _rec_name = 'order_id'

    customer_id = fields.Many2one(
        comodel_name='res.partner', string='Customer', help="Customer"
    )
    order_id = fields.Many2one(
        comodel_name='pos.order', string='Order', help="Order"
    )
    auth_token = fields.Char(
        string='Token', help='Token'
    )
    twilio_number = fields.Char(
        string='Twilio Number', help='Twilio Number'
    )
    to_number = fields.Char(
        string='Customer Number', help='Customer Number'
    )
    sms_body = fields.Char(
        string='Body', required=True, help='Body'
    )
    session_id = fields.Many2one(
        comodel_name='pos.session', string='Session', help='Session'
    )
    send_sms = fields.Boolean(
        string='Send SMS', default=False, help='Send SMS'
    )
