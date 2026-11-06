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

# Contact fields that a GDPR template can export and clear: a contact always
# keeps its name, and archiving the contact of a user is not allowed
GDPR_FIELD_DOMAIN = [
    ('model', '=', 'res.partner'),
    ('name', 'not in', ['name', 'active']),
    ('store', '=', True),
    ('readonly', '=', False),
    ('required', '=', False),
    ('ttype', 'not in', ['one2many', 'many2one_reference']),
]


class GdprTemplate(models.Model):
    """Group of contact fields that customers can download or delete."""
    _name = 'gdpr.template'
    _description = 'GDPR Template'

    name = fields.Char(string='Title', required=True,
                       help='Title of the template shown to the customers.')
    description = fields.Html(
        string='Short Description', required=True,
        help='Description of the data shown to the customers.')
    active = fields.Boolean(default=True)
    allow_messages = fields.Boolean(
        string='Send Emails', default=True,
        help='Inform the customer by email when a request of this template '
             'is approved or cancelled.')
    field_ids = fields.Many2many(
        'ir.model.fields', string='Data Fields', required=True,
        domain=GDPR_FIELD_DOMAIN,
        help='Contact fields exported or cleared by the requests of this '
             'template.')
