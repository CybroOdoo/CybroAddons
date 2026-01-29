# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Busthana Shirin (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models


class TwilioSmsGroup(models.Model):
    """Make group can send sms to group with more than one receiver at time"""
    _name = 'twilio.sms.group'
    _description = 'Twilio SmS Group'

    name = fields.Char('Name', help='Name of Group', required=True)
    contact_ids = fields.One2many('res.partner',
                                  'twilio_sms_id',
                                  string='Partner Group',
                                  help='Group Contacts')
