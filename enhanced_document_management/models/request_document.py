# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import base64
from io import BytesIO
import re

from odoo import api, fields, models, _
from odoo.tools import mimetypes


class RequestDocumentUser(models.Model):
    """Module to store document requests """
    _name = 'request.document'
    _description = 'Request document from user'
    _rec_name = 'needed_doc'

    user_id = fields.Many2one('res.users', string='User')
    requested_by = fields.Many2one(
        'res.users', help="User who created request",
        default=lambda self: self.env.user)
    needed_doc = fields.Text(string='Document Needed', required=True,
                             help="Document needed by requestor")
    workspace_id = fields.Many2one(
        'document.workspace', string='Work space', required=True)
    reject_reason = fields.Text(string='Reason', help="Reason for rejection")
    state = fields.Selection(selection=[
        ('requested', 'Requested'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected')], default='requested')
    company_id = fields.Many2one(
        related='workspace_id.company_id', string='Company',
        help="Company Name")
    hide_accept_button = fields.Boolean(string="Accept Upload",
                                        help='Boolean for checking the request '
                                             'is accepted or not')
    hide_accept_for_user_button = fields.Boolean(string="Accept",
                                                 compute="_compute_hide_accept_for_user_button",
                                                 help='Boolean for checking '
                                                      'the accept button only '
                                                      'visible for '
                                                      'corresponding users',
                                                 store=True)
    boolean_user_default = fields.Boolean(string="User Default",
                                          help='Boolean for compute '
                                               'accept button')

    def action_send_document_request(self):
        """Function to send document request through email """
        user_id = self.env['res.users'].browse(self.env.uid)
        mail_content = f'Hello <br/> {user_id.name} Requested Document <br/>' \
                       f'{self.needed_doc}'

        main_content = {
            'subject': _('Document Request'),
            'body_html': mail_content,
            'email_to': self.user_id.partner_id.email,
        }
        self.env['mail.mail'].sudo().create(main_content).send()
        self.write({
            'hide_accept_button': True,
        })

    def read(self, values):
        res = super(RequestDocumentUser, self).read(values)
        self.boolean_user_default = True
        return res

    @api.depends('boolean_user_default')
    def _compute_hide_accept_for_user_button(self):
        for rec in self:
            if rec.env.uid == rec.user_id.id:
                rec.hide_accept_for_user_button = True

    @api.model
    def get_request(self):
        """Function to fetch all request for login user """
        request_ids = self.env['request.document'].search(
            [('user_id', '=', self.env.uid)])
        context = [{
            'request_id': rec.id,
            'user_id': rec.user_id.name,
            'manager_id': rec.manager_id.name,
            'needed_doc': rec.needed_doc,
            'workspace': rec.workspace.name,
            'workspace_id': rec.workspace.id,
        } for rec in request_ids]
        return context

    def action_accept_request(self):
        return {
            'name': _("Upload Document"),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'document.file',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_workspace_id': self.workspace_id.id}
        }
