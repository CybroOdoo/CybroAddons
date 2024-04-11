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
from odoo import api, fields, models, _


class CustomClearance(models.Model):
    """Model for custom clearance"""
    _name = 'custom.clearance'
    _description = 'Custom Clearance'

    name = fields.Char(string='Name', compute='_compute_name',
                       help='Name of custom clearance')
    freight_id = fields.Many2one('freight.order', required=True,
                                 string='Freight Order',
                                 help='Select the freight order')
    date = fields.Date(string='Date', help='Date of clearance')
    agent_id = fields.Many2one('res.partner', string='Agent', required=True,
                               help='Select the agent for the clearance')
    loading_port_id = fields.Many2one('freight.port', string="Loading Port",
                                      help='Select the port for loading')
    discharging_port_id = fields.Many2one('freight.port',
                                          string="Discharging Port",
                                          help='Specify the discharging port')
    line_ids = fields.One2many('custom.clearance.line', 'clearance_id',
                               string='Clearance Line',
                               help='Line for adding the document')
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'),
                              ('done', 'Done')],
                             default='draft', string="State",
                             help='Different states of custom clearance')
    company_id = fields.Many2one('res.company', string='Company',
                                 copy=False, readonly=True,
                                 help="Current company",
                                 default=lambda
                                     self: self.env.company.id)

    @api.depends('freight_id')
    def _compute_name(self):
        """Compute the name of custom clearance"""
        for freight in self:
            freight.name = 'CC - ' + str(
                freight.freight_id.name) if freight.freight_id else 'CC - '

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
            base_url = self.env['ir.config_parameter'].sudo().get_param(
                'web.base.url')
            Urls = urls.url_join(base_url,
                                 'web#id=%(id)s&model=custom.clearance&view_type=form' % {
                                     'id': self.id})
            Urls_ = urls.url_join(base_url,
                                  'web#id=%(id)s&model=freight.order&view_type=form' % {
                                      'id': self.freight_id.id})
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
                'subject': _('Custom Clearance For %s') % self.freight_id.name,
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
            'res_model': 'custom.clearance.revision',
            'context': {
                'default_custom_id': self.id
            }
        }

    def action_get_revision(self):
        """Getting details of custom revision"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Custom Revision',
            'view_mode': 'tree,form',
            'res_model': 'custom.clearance.revision',
            'domain': [('custom_id', '=', self.id)],
            'context': "{'create': False}"
        }


class CustomClearanceLine(models.Model):
    """Uploading the documents for custom clearance"""
    _name = 'custom.clearance.line'
    _description = 'Custom Clearance Line'

    name = fields.Char(string='Document Name',
                       help='Name of the document attaching')
    document = fields.Binary(string="Documents", store=True, attachment=True,
                             help='Upload the document')
    clearance_id = fields.Many2one('custom.clearance',
                                   string='Custom Clearance',
                                   help='Relation from custom clearance')
    company_id = fields.Many2one('res.company', string='Company',
                                 copy=False, readonly=True,
                                 help="Current company",
                                 default=lambda
                                     self: self.env.company.id)
