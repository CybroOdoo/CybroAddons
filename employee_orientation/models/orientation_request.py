# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana Haseen @cybrosys(odoo@cybrosys.com)
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
from odoo import models, fields, _


class OrientationChecklistRequest(models.Model):
    """This class creates a model 'orientation.request' and adds
    required fields"""
    _name = 'orientation.request'
    _description = "Employee Orientation Request"
    _rec_name = 'request_name'
    _inherit = 'mail.thread'

    request_name = fields.Char(string='Name', help="Name the sequence")
    request_orientation_id = fields.Many2one('employee.orientation',
                                             string='Employee Orientation',
                                             help="Give the employee "
                                                  "orientation.")
    employee_company_id = fields.Many2one('res.company',
                                          string='Employees Company',
                                          required=True,
                                          default=lambda
                                              self: self.env.user.company_id,
                                          help="Give the company.")
    partner_id = fields.Many2one('res.users',
                                 string='Responsible User',
                                 help="Specify the responsible user.")
    request_date = fields.Date(string="Date", help="Mention the request date.")
    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  help="Give the employee name.")
    request_expected_date = fields.Date(string="Expected Date", help="Request"
                                                                     "expected "
                                                                     "date.")
    attachment_ids = fields.Many2many('ir.attachment',
                                      'orientation_rel_1',
                                      string="Attachment", help="Attachments "
                                                                "related.")
    note = fields.Text('Description', help="Give notes if any.")
    user_id = fields.Many2one('res.users', string='users',
                              default=lambda self: self.env.user,
                              help="Give the user.")
    company_id = fields.Many2one('res.company',
                                 string='Company', required=True,
                                 default=lambda self: self.env.user.company_id,
                                 help="Give the related company.")
    state = fields.Selection([
        ('new', 'New'),
        ('cancel', 'Cancel'),
        ('complete', 'Completed'),
    ], string='Status', readonly=True, copy=False, index=True,
        default='new', help="Status of the "
                            "request.")

    def action_confirm_send_mail(self):
        """Function executes on confirming mail"""
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data._xmlid_lookup(
                'employee_orientation.orientation_request_mailer')[2]
            print(template_id)
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data._xmlid_lookup(
                'mail.email_compose_message_wizard_form')[2]
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

    def action_confirm_request(self):
        """Function on confirm button of request"""
        self.write({'state': "complete"})

    def action_cancel_request(self):
        """Function on cancel button"""
        self.write({'state': "cancel"})
