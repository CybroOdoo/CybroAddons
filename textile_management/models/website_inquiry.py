# -*- coding: utf-8 -*-
######################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Prathyunnan R(<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#    or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
######################################################################################
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

    def action_verified(self):
        """To change the state to verified"""
        self.state = 'verified'

    def action_replied(self):
        """To change the state to replied"""
        self.state = 'replied'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('created_date'):
                vals['created_date'] = fields.Date.today()


            if vals.get('inquirer'):
                vals['name'] = "%s / %s" % (
                    vals['inquirer'],
                    vals['created_date']
                )

        return super().create(vals_list)
