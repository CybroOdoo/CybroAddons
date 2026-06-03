# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sruthi Pavithran(<https://www.cybrosys.com>)
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


class MailchimpTemplate(models.Model):
    """This class includes mailchimp template data"""
    _name = 'mailchimp.template'
    _description = 'Mailchimp Template'

    name = fields.Char(string="Name", required=True,
                       help="Name of the template")
    is_active = fields.Boolean(string="Active",
                               help="Mailchimp is active or not")
    type = fields.Char(string="Type", help="Type of mail template")
    is_drag_drop = fields.Boolean(string="Drag and Drop",
                                  help="Is template support drag and drop")
    is_responsive = fields.Boolean(string="Responsive",
                                   help="Is template responsive or not")
    share_url = fields.Char(string="Url", help="Url of template")
