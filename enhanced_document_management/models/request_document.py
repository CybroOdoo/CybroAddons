# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mruthul Raj(<https://www.cybrosys.com>)
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
from odoo import _, api, fields, models


class RequestDocument(models.Model):
    """ module to store document requests """
    _name = 'request.document'
    _description = 'Request document from user'
    _rec_name = 'display_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    display_name = fields.Char(string="Display Name",
                               help='display name  document request',required=True)
    user_id = fields.Many2one('res.users', string='User', help="Choose User",
                              required=True)
    requested_by_id = fields.Many2one('res.users',
                                      help="User who created request",
                                      string="Requested User",
                                      default=lambda self: self.env.user,
                                      readonly=True)
    needed_doc = fields.Text(string='Document Needed', required=True,
                             help="Document needed by requestor")
    workspace_id = fields.Many2one('document.workspace',
                                   string='Workspace',
                                   required=True,
                                   help="Select the workspace associated with"
                                        " this item.")
    manager_id = fields.Many2one('res.users', string='Manager',
                                 help="Select Manager")
    workspace = fields.Char(related='workspace_id.name',
                            string='Workspace Name',
                            help='Workspace name')
    reject_reason = fields.Text(string='Reason', help="Reason for rejection")
    state = fields.Selection(selection=[('draft', 'Draft'),
                                        ('requested', 'Requested'),
                                        ('accepted', 'Accepted'),
                                        ('rejected', 'Rejected')],
                             default='draft', string="State",
                             help="Choose the current state of the item: Requested, Accepted, or "
                                  "Rejected.")

    def action_send_document_request(self):
        """ function to send document request through email """
        self.state = 'requested'
        user_id = self.env['res.users'].browse(self.env.uid)
        mail_content = f'Hello <br/> {user_id.name} Requested Document <br/>' \
                       f'{self.needed_doc}'
        main_content = {
            'subject': _('Document Request'),
            'body_html': mail_content,
            'email_to': self.user_id.partner_id.email,
        }
        self.env['mail.mail'].sudo().create(main_content).send()

    @api.model
    def get_request(self):
        """
        Function to fetch all requests for the currently logged-in user.
        This function retrieves all requests related to the current user from
        the 'request.document' model and formats
        the data into a list of dictionaries containing relevant information
         about each request.
        Returns:
            list of dict: A list of dictionaries containing information
             about the requests.
        """
        request_ids = self.env['request.document'].search(
            [('user_id', '=', self.env.uid)])
        context = [{
            'request_id': rec.id,
            'user_id': rec.user_id.name,
            'manager_id': rec.manager_id.name,
            'needed_doc': rec.needed_doc,
            'workspace': rec.workspace,
            'workspace_id': rec.workspace_id.id,
        } for rec in request_ids]
        return context

    @api.model
    def get_wizard_view(self, view_id):
        """ Method is used to get the wizard view xml id for wizard """
        return self.env.ref(view_id).id

    @api.model_create_multi
    def create(self, vals_list):
        """ Super the create function to generate sequences for document.request"""
        for vals in vals_list:
            if not vals.get('display_name') or vals['display_name'] == _('New'):
                vals['display_name'] = self.env['ir.sequence'].next_by_code(
                    'document.request') or _('New')
        return super().create(vals_list)
