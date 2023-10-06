# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Unnimaya C O (odoo@cybrosys.com)
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
from odoo import fields, models


class WebhookWebhook(models.Model):
    """Model that holds the webhook model and the urls to receive the payload"""
    _name = 'webhook.webhook'
    _description = 'Webhook'
    _rec_name = 'model_id'

    model_id = fields.Many2one('ir.model', string='Model',
                               help='Choose the model')
    create_url = fields.Char(string="Url for Create Event",
                             help="The URL to which payload to be send when a "
                                  "new record is created")
    edit_url = fields.Char(string="Url for Edit Event",
                           help="The URL to which payload to be send when a "
                                "record is modified")
    delete_url = fields.Char(string="Url for Delete Event",
                             help="The URL to which payload to be send when a "
                                  "record  is deleted")
