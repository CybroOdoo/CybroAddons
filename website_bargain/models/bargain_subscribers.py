# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anfas Faisal K (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models


class BargainSubscribers(models.Model):
    """Model for adding the subscriber details """
    _name = 'bargain.subscribers'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Subscriber details"

    subscriber_id = fields.Many2one('res.partner', required=True,
                                    help="Subscribers id will be here ")
    name = fields.Char(related='subscriber_id.name', string='Name',
                       readonly=False, help="Subscribers name",
                       required=True)
    email = fields.Char(related='subscriber_id.email', string='Email',
                        readonly=False, help="Subscribers email")
    auction_id = fields.Many2one('website.bargain', string='Auction',
                                 required=True, help="Auction details")
    subscribe_time = fields.Datetime(string='Subscribe On',
                                     default=fields.Datetime.today(),
                                     readonly=True,
                                     help="Time of subscription")
    is_subscribed = fields.Boolean(string="Is Subscribed",
                                   help="Check if Subscribed or not")
