#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import fields, models


class MailingListTemplates(models.Model):
    """Drip template of a mailing list, sent the given number of days after
    the start date of its drip mass mailing."""
    _name = 'mailing.list.templates'
    _description = 'Mailing List Drip Template'
    _order = 'days_after, id'

    name = fields.Char(help="Name of the drip")
    days_after = fields.Integer(
        help="Number of days after the start date the template is sent")
    template_id = fields.Many2one(
        'drip.template', string="Drip Template", required=True,
        help="Template to send")
    mailing_id = fields.Many2one(
        'mailing.list', string="Mailing List", required=True,
        ondelete='cascade', help="Mailing list of the drip")
