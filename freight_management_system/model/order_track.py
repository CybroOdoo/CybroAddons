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
from odoo import fields, models, _


class FreightTracking(models.Model):
    _name = 'freight.order.track'

    date = fields.Date('Date', default=fields.Date.today())
    freight_id = fields.Many2one('freight.order')
    source_loc = fields.Many2one('freight.port', 'Source Location')
    destination_loc = fields.Many2one('freight.port', 'Destination Location')
    transport_type = fields.Selection([('land', 'Land'), ('air', 'Air'),
                                       ('water', 'Water')], "Transport")
    type = fields.Selection([('received', 'Received'),
                             ('delivered', 'Delivered')], 'Received/Delivered')

    def order_submit(self):
        """Create tracking details of order"""
        self.env['freight.track'].create({
            'track_id': self.freight_id.id,
            'source_loc': self.source_loc.id,
            'destination_loc': self.destination_loc.id,
            'transport_type': self.transport_type,
            'date': self.date,
            'type': self.type,
        })
        for rec in self.freight_id:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            Urls = urls.url_join(base_url, 'web#id=%(id)s&model=freight.order&view_type=form' % {'id': self.id})

            mail_content = _('Hi<br>'
                             'The Freight Order %s is %s at %s'
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
                             ) % (rec.name, self.type,
                                  self.destination_loc.name, Urls, rec.name)
            email_to = self.env['res.partner'].search([
                ('id', 'in', (rec.shipper_id.id, rec.consignee_id.id,
                              rec.agent_id.id))])
            for mail in email_to:
                main_content = {
                    'subject': _('Freight Order %s is %s at %s') % (rec.name,
                                                                    self.type,
                                                                    self.destination_loc.name,),
                    'author_id': rec.env.user.partner_id.id,
                    'body_html': mail_content,
                    'email_to': mail.email
                }
                mail_id = rec.env['mail.mail'].create(main_content)
                mail_id.mail_message_id.body = mail_content
                mail_id.send()


class FreightTrackingLine(models.Model):
    _name = 'freight.order.track.line'

    track_line_id = fields.Many2one('freight.order.track')
    source_loc = fields.Many2one('freight.port', 'Source Location')
    destination_loc = fields.Many2one('freight.port', 'Destination Location')
    transport_type = fields.Selection([('land', 'Land'), ('air', 'Air'),
                                       ('water', 'Water')], "Transport")
    date = fields.Date('Date')
    type = fields.Selection([('receive', 'Received'), ('deliver', 'Delivered')],
                            'Received/Delivered')
