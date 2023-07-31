# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Muhsina V (<https://www.cybrosys.com>)
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


class PosCustomMessage(models.Model):
    """Model to manage custom popup messages for the Point of Sale system."""
    _name = 'pos.custom.message'
    _description = "Custom Popup Messages in Pos Screen"
    _rec_name = 'title'

    message_type = fields.Selection([('alert', 'Alert'), ('warn', 'Warning'),
                                     ('info', 'Information')], default='alert',
                                    string="Message Type",
                                    help="Choose the message type")
    title = fields.Char(string="Title", help="Title of the message")
    message_text = fields.Char(string="Message Text",
                               help="Content of the message")
    execution_time = fields.Float(string="Execution Time",
                                  help="Choose the time in 24-hour format at "
                                       "which the popup should be shown.")
    pos_config_ids = fields.Many2many('pos.config', string="Point of sale",
                                      help="Choose the point of sale")
