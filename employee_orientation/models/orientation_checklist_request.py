# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anusha @cybrosys(odoo@cybrosys.com)
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
#############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _


class OrientationChecklistRequest(models.Model):
    _name = 'orientation.request'
    _description = "Employee Orientation Request"
    _rec_name = 'request_name'
    _inherit = 'mail.thread'

    request_name = fields.Char(string='Name')
    request_orientation = fields.Many2one('employee.orientation', string='Employee Orientation')
    employee_company = fields.Many2one('res.company', string='Company', required=True,
                                       default=lambda self: self.env.user.company_id)
    partner_id = fields.Many2one('res.users', string='Responsible User')
    request_date = fields.Date(string="Date")
    employee_id = fields.Many2one('hr.employee', string='Employee')
    request_expected_date = fields.Date(string="Expected Date")
    attachment_id_1 = fields.Many2many('ir.attachment', 'orientation_rel_1', string="Attachment")
    note_id = fields.Text('Description')
    user_id = fields.Many2one('res.users', string='users', default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)
    state = fields.Selection([
        ('new', 'New'),
        ('cancel', 'Cancel'),
        ('complete', 'Completed'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='new')

    def confirm_send_mail(self):
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('employee_orientation', 'orientation_request_mailer')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'orientation.request',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
        })

        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    def confirm_request(self):
        self.write({'state': "complete"})

    def cancel_request(self):
        self.write({'state': "cancel"})
