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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class CustomClearance(models.Model):
    """Model for custom clearance"""
    _name = 'custom.clearance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Custom Clearance'

    name = fields.Char(compute='_compute_name', store=True,
                       help='Name of custom clearance')
    freight_id = fields.Many2one('freight.order', required=True,
                                 tracking=True, ondelete='cascade',
                                 string='Freight Order',
                                 help='Select the freight order')
    date = fields.Date(tracking=True, help='Date of clearance')
    agent_id = fields.Many2one('res.partner', required=True,
                               tracking=True,
                               help='Select the agent for the clearance')
    loading_port_id = fields.Many2one('freight.port', tracking=True,
                                      help='Select the port for loading')
    discharging_port_id = fields.Many2one('freight.port',
                                          tracking=True,
                                          help='Specify the discharging port')
    line_ids = fields.One2many('custom.clearance.line', 'clearance_id',
                               string='Clearance Line',
                               help='Line for adding the document')
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm')],
                             default='draft', tracking=True,
                             help='Different states of custom clearance')
    company_id = fields.Many2one('res.company', copy=False, readonly=True,
                                 help="Current company",
                                 default=lambda self: self.env.company)

    @api.depends('freight_id')
    def _compute_name(self):
        """Compute the name of custom clearance"""
        for rec in self:
            if rec.freight_id:
                rec.name = 'CC - %s' % rec.freight_id.name
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
        """Confirm custom clearance and send email notification"""
        template = self.env.ref(
            'freight_management_system.'
            'mail_template_custom_clearance_confirmed',
            raise_if_not_found=False)
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(self.env._(
                    "Only draft custom clearances can be confirmed."))
            rec.state = 'confirm'
            if template and rec.agent_id.email:
                template.send_mail(
                    rec.id, force_send=False,
                    email_values={'recipient_ids': [(4, rec.agent_id.id)]})
            rec.message_post(body=self.env._(
                "Custom Clearance %s has been confirmed.", rec.name))

    def action_revision(self):
        """Creating custom revision"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Custom Clearance Revision'),
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'custom.clearance.revision',
            'context': {
                'default_custom_id': self.id,
            },
        }

    def action_get_revision(self):
        """Getting details of custom revision"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Custom Revision'),
            'view_mode': 'list',
            'res_model': 'clearance.revision',
            'domain': [('clearance_id', '=', self.id)],
            'context': {'create': False},
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
                                   ondelete='cascade',
                                   help='Relation from custom clearance')
    company_id = fields.Many2one('res.company', copy=False, readonly=True,
                                 help="Current company",
                                 default=lambda
                                     self: self.env.company.id)
