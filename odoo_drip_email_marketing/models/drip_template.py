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


class DripTemplate(models.Model):
    """Mail sent by the drip email marketing: its subject, body and
    attachments."""
    _name = 'drip.template'
    _description = 'Drip Template'

    name = fields.Char(string="Subject", required=True,
                       help="Subject of the mail")
    mail_body = fields.Html(help="Body of the mail")
    attachment_ids = fields.Many2many(
        'ir.attachment', string='Attachments',
        help="Files attached to the mail")
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company,
        help="Company of the template")
