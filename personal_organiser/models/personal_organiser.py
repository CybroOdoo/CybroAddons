# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Aleena K(<https://www.cybrosys.com>)
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
from odoo import models, fields


class PersonalOrganiser(models.Model):
    """This class is used to deal with tasks"""
    _name = "personal.organiser"
    _description = "Personal Organiser"

    user_id = fields.Many2one('res.users', string="User")
    task_title = fields.Char(required=True, string="Title", help="For title")
    date = fields.Datetime(required=True, string="Date", help="Date field")
    calendar_event_id = fields.Many2one('calendar.event',
                                        string='Calendar Event',
                                        ondelete='set null')

