# -*- coding: utf-8 -*-
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
from odoo.tools import _

class DocumentTemplateRequest(models.Model):
    """Model representing document requests."""
    _name = "document.template.request"
    _description = "Document Template Request"

    name = fields.Char(string="Name",
                       help='Display name of the document request.',
                       default=lambda self: _('New'))
    document_id = fields.Many2one('document.request.template',
                                  help="Selected document template",
                                  string="Document", required=True)
    user_id = fields.Many2one('res.users',
                              string="User", help="User creating the request",
                              default=lambda self: self.env.user)
    manager_id = fields.Many2one('res.users', string="Manager",
                                 help="Manager of the document",
                                 related="document_id.manager_id")
    requested_date = fields.Date(string="Requested Date",
                                 help="Date when the request was made",
                                 default=fields.Date.today)
    template = fields.Html(string="Template",
                           help="HTML template content")
    stamp = fields.Image(string="Image",
                         help="Image associated with the document")
    create_user_avatar = fields.Binary(help="User's image",
                                       string="Author",
                                       related='create_uid.image_1920')
    state = fields.Selection(
        [('new', 'New'),
         ('document_approval', 'Document Approval'),
         ('approved', 'Approved')], default='new', help="Current state of the document request.",
        tracking=True, string="State")
    employee_id = fields.Many2one('hr.employee', string="Employee",
                                 default=lambda self: self.env.user.employee_id)

    @api.model_create_multi
    def create(self, vals_list):
        """Super the create function in document.template.request to generate
        sequences"""
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == _(
                    'New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'document.template.request') or _('New')
        return super().create(vals_list)

    def copy(self, default=None):
        """Generate a fresh sequence when duplicating a request."""
        default = dict(default or {})
        default['name'] = self.env['ir.sequence'].next_by_code(
            'document.template.request'
        ) or _('New')
        return super().copy(default)

    def action_sent_document_approval(self):
        """Function to change the state to 'document_approval'."""
        self.write({'state': 'document_approval'})

    def action_approve(self):
        """Function to change the state to 'approved'."""
        self.write({'state': 'approved'})

    def action_preview_document(self):
        """Open the client-side document preview.

        Returns:
            dict: Client action descriptor for the 'preview_document' OWL component.
        """
        self.ensure_one()
        stamp_value = self.stamp
        if isinstance(stamp_value, bytes):
            stamp_value = stamp_value.decode("utf-8")

        return {
            "type": "ir.actions.client",
            "tag": "preview_document",
            "params": {
                "body_html": self.template or "",
                "stamp": stamp_value or False,
            },
        }

    def action_download_document(self):
        """method to download the document"""
        data = {'template': self.template,
                'image': self.stamp}
        return self.env.ref(
            'enhanced_document_management.action_download_doc').report_action(
            None,
            data=data)

    def _get_report_base_filename(self):
        """Method to return document's name"""
        self.ensure_one()
        return f'{self.document_id.name}'

    @api.onchange('document_id')
    def _onchange_document_id(self):
        """Onchange function to set the template and stamp based on the
        document template selected"""
        if self.document_id:
            self.template = self.document_id.template
            self.stamp = self.document_id.stamp
