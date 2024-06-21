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
from odoo import models, fields, api


class AddRecipient(models.TransientModel):
    """To add more recipients in the chatter"""
    _name = 'mail.wizard.recipient'
    _description = 'Add more Recipients'

    partner_id = fields.Many2one('res.users', string='Recipients',
                                 help="Choose the user to whom we have to "
                                      "sent the reply mail")
    model = fields.Char(string='Related Model', help="Related Model")
    model_reference = fields.Integer(string="Related Document Id",
                                     help="Related Document Id")

    def add_recipients(self):
        """On selecting the user to whom the mail is sent, the user is then
        added to config parameters"""
        self.env['ir.config_parameter'].set_param('reply_to',
                                                  self.partner_id.id)

    @api.model
    def get_user(self, user_id):
        """if reply mail is sent to the person who sent the mail,
        then default person will be set in config parameters"""
        self.env['ir.config_parameter'].set_param('reply_to', user_id)
