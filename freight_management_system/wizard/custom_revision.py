# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Megha K (<https://www.cybrosys.com>)
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
###################################################################################
from werkzeug import urls
from odoo import models, fields, _


class CustomClearanceRevisionReason(models.TransientModel):
    _name = 'custom.clearance.revision.wizard'
    _description = 'Custom Clearance Revision'

    name = fields.Text('Reason', required=True)
    custom_id = fields.Many2one('custom.clearance')
    text = fields.Char()

    def create_revision(self):
        """create revision"""
        for rec in self.custom_id:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            Urls = urls.url_join(base_url,
                                 'web#id=%(id)s&model=custom.clearance&view_type=form' % {'id': self.custom_id.id})
            Urls_ = urls.url_join(base_url,
                                  'web#id=%(id)s&model=freight.order&view_type=form' % {'id': self.custom_id.freight_id.id})

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
                'subject': _('Custom Clerance Revision For %s') % self.custom_id.freight_id.name,
                'author_id': self.env.user.partner_id.id,
                'body_html': mail_content,
                'email_to': rec.agent_id.email,
            }
            mail_id = self.env['mail.mail'].create(main_content)
            mail_id.mail_message_id.body = mail_content
            mail_id.send()

            self.env['custom.clearance.revision'].create({
                'clearance_id': self.custom_id.id,
                'reason': self.name,
                'name': 'RE: ' + self.custom_id.name
            })
