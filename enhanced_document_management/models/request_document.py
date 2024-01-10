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
from odoo import api, fields, models, _


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
