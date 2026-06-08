# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################

from odoo import api, fields, models


class WebsiteInquiry(models.Model):
    """Create a new model for website inquiry"""
    _name = 'website.inquiry'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Website Inquiry'

    name = fields.Char(string="Name", help="Name of the website inquiry")
    inquirer = fields.Char(string="Inquirer", help="Person who asks a "
                                                   "question", required=True)
    email = fields.Char(string='Email', help="Email of inquirer",
                        required=True)
    phone_number = fields.Char(string="Phone Number", help="Phone number "
                                                           "of Inquirer")
    created_date = fields.Date(string="Created Date", help="Created date",
                               default=fields.Date.today)
    description = fields.Html(string='Description',
                              help="Description of inquiry")
    state = fields.Selection([
        ('draft', 'Draft'), ('verified', 'Verified'),
        ('replied', 'Replied')], string="State",
        default='draft', tracking=True, state="State of Website Inquiry")
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
        readonly=True
    )

    def action_verified(self):
        """To change the state to verified"""
        self.state = 'verified'

    def action_replied(self):
        """To change the state to replied"""
        self.state = 'replied'

    @api.model_create_multi
    def create(self, vals_list):
        """Generate inquiry name and set created date during record creation"""
        for vals in vals_list:
            if not vals.get('created_date'):
                vals['created_date'] = fields.Date.today()

            if vals.get('inquirer'):
                vals['name'] = "%s / %s" % (
                    vals['inquirer'],
                    vals['created_date']
                )

        return super().create(vals_list)
