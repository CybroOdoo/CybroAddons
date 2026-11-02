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
from odoo import api, fields, models


class WebsiteInquiry(models.Model):
    """Inquiry submitted from the textile inquiry form of the website."""
    _name = 'website.inquiry'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Website Inquiry'
    _order = 'id desc'

    name = fields.Char(help="Name of the website inquiry")
    inquirer = fields.Char(required=True, help="Person who asks a question")
    email = fields.Char(required=True, help="Email of inquirer")
    phone_number = fields.Char(help="Phone number of Inquirer")
    created_date = fields.Date(default=fields.Date.today,
                               help="Created date")
    description = fields.Html(help="Description of inquiry")
    state = fields.Selection(
        [('draft', 'Draft'), ('verified', 'Verified'),
         ('replied', 'Replied')],
        default='draft', tracking=True, help="State of Website Inquiry")
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company, readonly=True)

    def action_verified(self):
        """Mark the inquiry as verified."""
        self.state = 'verified'

    def action_replied(self):
        """Mark the inquiry as replied."""
        self.state = 'replied'

    @api.model_create_multi
    def create(self, vals_list):
        """Name the inquiry after the inquirer and its date."""
        for vals in vals_list:
            vals.setdefault('created_date', fields.Date.today())
            if vals.get('inquirer') and not vals.get('name'):
                vals['name'] = f"{vals['inquirer']} / {vals['created_date']}"
        return super().create(vals_list)
