# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anfas Faisal K (odoo@cybrosys.info)
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


class SmsHistory(models.Model):
    """A model for SMS history"""
    _name = 'sms.history'
    _description = "SMS History of Sent Sms"

    name = fields.Char(string="Name", help="Name of the Receiver")
    number = fields.Char(string='Number', help="Mobile number of the Receiver")
    state = fields.Selection([('outgoing', 'In Queue'),
                              ('sent', 'Sent'),
                              ('canceled', 'Canceled')
                              ], string='SMS Status', readonly=True,
                             help="State of SMS")
    message = fields.Text(string="Message", help="SMS Message")
