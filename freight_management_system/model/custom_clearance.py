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
from odoo import api, fields, models, _


class CustomClearance(models.Model):
    _name = 'custom.clearance'
    _description = 'Custom Clearance'

    name = fields.Char('Name', compute='_compute_name')
    freight_id = fields.Many2one('freight.order', required=True)
    date = fields.Date('Date')
    agent_id = fields.Many2one('res.partner', 'Agent', required=True)
    loading_port_id = fields.Many2one('freight.port', string="Loading Port")
    discharging_port_id = fields.Many2one('freight.port',
                                          string="Discharging Port")
    line_ids = fields.One2many('custom.clearance.line', 'line_id')
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'),
                              ('done', 'Done')], default='draft')

    @api.depends('freight_id')
    def _compute_name(self):
        """Compute the name of custom clearance"""
        for rec in self:
            if rec.freight_id:
                rec.name = 'CC - ' + str(rec.freight_id.name)
            else:
                rec.name = 'CC - '

    @api.onchange('freight_id')
    def _onchange_freight_id(self):
        """Getting default values for loading and discharging port"""
        for rec in self:
            rec.date = rec.freight_id.order_date
            rec.loading_port_id = rec.freight_id.loading_port_id
            rec.discharging_port_id = rec.freight_id.discharging_port_id
            rec.agent_id = rec.freight_id.agent_id

    def action_confirm(self):
        """Send mail to inform agents to custom clearance is confirmed"""
        for rec in self:
            rec.name = 'CC' \
                       ' - ' + rec.freight_id.name
            rec.state = 'confirm'
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            Urls = urls.url_join(base_url, 'web#id=%(id)s&model=custom.clearance&view_type=form' % {'id': self.id})
            Urls_ = urls.url_join(base_url, 'web#id=%(id)s&model=freight.order&view_type=form' % {'id': self.freight_id.id})

            mail_content = _('Hi %s,<br>'
                             'The Custom Clearance %s is confirmed'
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
                             ) % (rec.agent_id.name, rec.name, Urls,
                                  rec.name, Urls_, self.freight_id.name)
            main_content = {
                'subject': _('Custom Clerance For %s') % self.freight_id.name,
                'author_id': self.env.user.partner_id.id,
                'body_html': mail_content,
                'email_to': rec.agent_id.email,
            }
            mail_id = self.env['mail.mail'].create(main_content)
            mail_id.mail_message_id.body = mail_content
            mail_id.send()

    def action_revision(self):
        """Creating custom revision"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Received/Delivered',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'custom.clearance.revision.wizard',
            'context': {
                'default_custom_id': self.id
            }
        }

    def get_revision(self):
        """Getting details of custom revision"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Custom Revision',
            'view_mode': 'tree,form',
            'res_model': 'custom.clearance.revision',
            'domain': [('clearance_id', '=', self.id)],
            'context': "{'create': False}"
        }


class CustomClearanceLine(models.Model):
    _name = 'custom.clearance.line'
    _description = 'Custom Clearance Line'

    name = fields.Char('Document Name')
    document = fields.Binary(string="Documents", store=True, attachment=True)
    line_id = fields.Many2one('custom.clearance')


class CustomClearanceRevision(models.Model):
    _name = 'custom.clearance.revision'
    _description = 'Custom Clearance Revision'

    name = fields.Char('Name')

    name = fields.Char()
    reason = fields.Text()
    clearance_id = fields.Many2one('custom.clearance')
