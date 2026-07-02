# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sruthi pavithran(<https://www.cybrosys.com>)
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
from odoo import api, fields, models
from odoo.tools import html_escape


class MailingMailing(models.Model):
    _inherit = 'mailing.mailing'

    template_id = fields.Many2one('mailchimp.template',
                                  string="Template", help="Mailing Template")

    @api.onchange('template_id')
    def _onchange_template_id(self):
        """Add Mailchimp Template in Mail Body"""
        image_url = self.template_id.share_url
        if image_url:
            image_html = f'<span/><img src="{html_escape(image_url)}"/>'
            self.write({
                'body_arch': image_html
            })
