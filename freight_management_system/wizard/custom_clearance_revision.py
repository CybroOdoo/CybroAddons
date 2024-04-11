# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from werkzeug import urls
from odoo import models, fields, _


class CustomClearanceRevision(models.TransientModel):
    """Create Revision for the custom clearance"""
    _name = 'custom.clearance.revision'
    _description = 'Custom Clearance Revision'

    name = fields.Text(string='Reason', required=True,
                       help='Mention the reason for revision')
    custom_id = fields.Many2one('custom.clearance', string='Custom clearance',
                                help='Select the custom clearance')
    text = fields.Char(string='Text', help='Note any points')
    company_id = fields.Many2one('res.company', string='Company',
                                 copy=False, readonly=True,
                                 help="Current company",
                                 default=lambda
                                     self: self.env.company.id)

    def action_create_revision(self):
        """Create revision against custom clearance"""
        for rec in self.custom_id:
            base_url = self.env['ir.config_parameter'].sudo().get_param(
                'web.base.url')
            Urls = urls.url_join(base_url,
                                 'web#id=%(id)s&model=custom.clearance&view_type=form' % {
                                     'id': self.custom_id.id})
            Urls_ = urls.url_join(base_url,
                                  'web#id=%(id)s&model=freight.order&view_type=form' % {
                                      'id': self.custom_id.freight_id.id})
            mail_content = _('Hi %s,<br>'
                             'The Custom Clearance Revision with reason: %s'
                             '<div style = "text-align: center; '
                             'margin-top: 16px;"><a href = "%s"'
                             'style = "padding: 5px 10px; font-size: 12px; '
                             'line-height: 18px; color: #FFFFFF; '
                             'border-color:#875A7B;text-decoration: none; '
                             'display: inline-block; '
                             'margin-bottom: 0px; font-weight: 400;'
                             'text-align: center; vertical-align: middle; '
                             'cursor: pointer; white-space: nowrap; '
                             'background-image: none; '
                             'background-color: #875A7B; '
                             'border: 1px solid #875A7B; border-radius:3px;">'
                             'View %s</a></div>'
                             '<div style = "text-align: center; '
                             'margin-top: 16px;"><a href = "%s"'
                             'style = "padding: 5px 10px; '
                             'font-size: 12px; line-height: 18px; '
                             'color: #FFFFFF; border-color:#875A7B;'
                             'text-decoration: none; display: inline-block; '
                             'margin-bottom: 0px; font-weight: 400;'
                             'text-align: center; vertical-align: middle; '
                             'cursor: pointer; white-space: nowrap; '
                             'background-image: none; '
                             'background-color: #875A7B; '
                             'border: 1px solid #875A7B; border-radius:3px;">'
                             'View %s</a></div>'
                             ) % (rec.agent_id.name, self.name, Urls,
                                  rec.name, Urls_,
                                  self.custom_id.freight_id.name)
            main_content = {
                'subject': _(
                    'Custom Clearance Revision For %s') % self.custom_id.freight_id.name,
                'author_id': self.env.user.partner_id.id,
                'body_html': mail_content,
                'email_to': rec.agent_id.email,
            }
            mail_id = self.env['mail.mail'].create(main_content)
            mail_id.mail_message_id.body = mail_content
            mail_id.send()
            self.env['custom.clearance.revision'].create({
                'custom_id': self.custom_id.id,
                'name': self.name,
            })
