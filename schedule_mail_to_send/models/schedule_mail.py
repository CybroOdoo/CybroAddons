# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import fields, models


class ScheduleMail(models.Model):
    """Used to save the scheduled mail, since the model mail.compose.message is
    a transient model, so there is a chance of losing data"""
    _name = 'schedule.mail'
    _description = 'Save the Scheduled Mail'

    subject = fields.Char(string='Subject',help='Subject for the mail')
    body = fields.Html(string='Contents', default='', sanitize_style=True,
                       help='Body of the Mail')
    partner_ids = fields.Many2many('res.partner', 'partner_id',
                                   string='Partners', help='To whom want to '
                                                           'send the mail')
    schedule_time = fields.Datetime(string='Schedule Time',
                                    help='Schedule date and time')
    email_from = fields.Char(string='Email From', help='Who send the mail')
    attachment_ids = fields.Many2many('ir.attachment',string='Attachments',
                                      help='Attach the files')
