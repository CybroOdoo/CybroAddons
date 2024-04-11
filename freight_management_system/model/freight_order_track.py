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
from odoo import fields, models, _


class FreightTracking(models.Model):
    _name = 'freight.order.track'
    _description = 'Freight Order Track'

    date = fields.Date('Date', default=fields.Date.today())
    freight_id = fields.Many2one('freight.order')
    source_loc_id = fields.Many2one('freight.port', 'Source Location')
    destination_loc_id = fields.Many2one('freight.port', 'Destination Location')
    transport_type = fields.Selection([('land', 'Land'), ('air', 'Air'),
                                       ('water', 'Water')], "Transport")
    type = fields.Selection([('received', 'Received'),
                             ('delivered', 'Delivered')], 'Received/Delivered')
    company_id = fields.Many2one('res.company', string='Company',
                                 copy=False, readonly=True,
                                 help="Current company",
                                 default=lambda
                                     self: self.env.company.id)

    def action_order_submit(self):
        """Create tracking details of order"""
        self.env['freight.track'].create({
            'freight_id': self.freight_id.id,
            'source_loc_id': self.source_loc_id.id,
            'destination_loc_id': self.destination_loc_id.id,
            'transport_type': self.transport_type,
            'date': self.date,
            'type': self.type,
        })
        for rec in self.freight_id:
            base_url = self.env['ir.config_parameter'].sudo().get_param(
                'web.base.url')
            Urls = urls.url_join(base_url,
                                 'web#id=%(id)s&model=freight.order&view_type=form' % {
                                     'id': self.id})

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
                                  self.destination_loc_id.name, Urls, rec.name)
            email_to = self.env['res.partner'].search([
                ('id', 'in', (rec.shipper_id.id, rec.consignee_id.id,
                              rec.agent_id.id))])
            for mail in email_to:
                main_content = {
                    'subject': _('Freight Order %s is %s at %s') % (rec.name,
                                                                    self.type,
                                                                    self.destination_loc_id.name,),
                    'author_id': rec.env.user.partner_id.id,
                    'body_html': mail_content,
                    'email_to': mail.email
                }
                mail_id = rec.env['mail.mail'].create(main_content)
                mail_id.mail_message_id.body = mail_content
                mail_id.send()