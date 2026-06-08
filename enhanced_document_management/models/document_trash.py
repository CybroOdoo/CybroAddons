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

class DocumentTrash(models.Model):
    """Module to store deleted documents for a specific time,
    then it automatically"""
    _name = "document.trash"
    _description = "Document Trash"

    name = fields.Char(string="Name", help="Document name")
    attachment = fields.Binary(string="File", readonly=True,
                               help="Document data")
    document_create_date = fields.Datetime(string="Date",
                                           help="Document creation date")
    workspace_id = fields.Many2one(
        "document.workspace", string="Workspace", required=True,
        help="Workspace associated with this document."
    )
    user_id = fields.Many2one(
        "res.users",
        string="Owner",
        default=lambda self: self.env.user,
        help="User who owned the document",
    )
    brochure_url = fields.Char(string="URL", store=True,
                               help="Document sharable URL")
    extension = fields.Char(string="Extension",
                            help="Helps to determine the file type.")
    priority = fields.Selection(
        selection=[("0", "None"), ("1", "Favorite")],
        string="Priority",
        help="Priority/Favorite status.",
    )
    attachment_id = fields.Many2one(
        "ir.attachment",
        string="Attachment",
        help="Attachment linked to this trashed document.",
    )
    content_url = fields.Char(
        string="Content Url", help="It stores the URL for URL type documents"
    )
    content_type = fields.Selection(
        [("file", "File"), ("url", "Url")],
        help="Document content type",
        string="Content type",
    )
    preview = fields.Char(
        string="Preview", help="Preview URL for link-based documents."
    )
    active = fields.Boolean(
        string="Active", default=True, help="It specifies the archived file"
    )
    days = fields.Integer(string="Days", help="Automatic deletion after specified number of days.")
    deleted_date = fields.Date(string="Deleted Date", help="File deleted date")
    mimetype = fields.Char(string="Mime Type", help="Document mimetype")
    description = fields.Text(string="Description", help="Short description")
    security = fields.Selection(
        string="Security",
        selection=[
            ("private", "Private"),
            ("managers_and_owner", "Managers & Owner"),
            ("specific_users", "Specific Users"),
        ],
        default="managers_and_owner",
        help=(
            "Private: only the uploaded user can view. "
            "Managers & Owner: Document shared with managers and the owner."
        )
    )
    user_ids = fields.Many2many(
        "res.users", help="Users allowed to access this document.", string="User Access"
    )
    partner_id = fields.Many2one(
        "res.partner", help="Partner related to this document.",
        string="Related Partner"
    )
    is_auto_delete = fields.Boolean(
        string="Auto Delete", default=False, help="Enable automatic document deletion."
    )
    delete_date = fields.Date(
        string="Date Delete",
        readonly=True,
        help="Date when the document will be removed from the trash.",
    )
    file_url = fields.Char(
        string="File URL", help="It stores the URL while adding an URL document"
    )
    size = fields.Char(string="Size", help="Size of the document.")
    company_id = fields.Many2one(
        related='workspace_id.company_id', string='Company',
        help="Company Name")

    def cron_delete_doc(self):
        """Delete all documents whose trash retention period has elapsed."""
        trash_limit = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("enhanced_document_management.trash")
        )
        if not trash_limit:
            return

        try:
            trash_limit = int(trash_limit)
        except ValueError:
            return

        cutoff_date = fields.Date.subtract(
            fields.Date.today(), days=trash_limit
        )
        self.search([
            ('deleted_date', '<=', cutoff_date)
        ]).unlink()

    def action_restore_document(self):
        """
        Restore a previously deleted document from the trash.
        This function restores a deleted document by creating a new record in
        the 'document.file' model with the same attributes as the deleted
        document. It then unlinks the deleted document and returns to the
        'Trash' view.
        :return: Window action to view the 'Trash' or restore the document.
        :rtype: dict
        """
        doc_id = self.env['document.file'].create({
            'name': self.name,
            'extension': self.extension,
            'attachment': self.attachment,
            'date': self.document_create_date or fields.Datetime.now(),
            'workspace_id': self.workspace_id.id,
            'user_id': self.user_id.id,
            'content_type': self.content_type,
            'brochure_url': self.brochure_url,
            'active': self.active,
            'mimetype': self.mimetype,
            'description': self.description,
            'content_url': self.content_url,
            'security': self.security,
            'priority': self.priority,
            'user_ids': [(6, 0, self.user_ids.ids)],
            'partner_id': self.partner_id.id,
            'days': self.days,
            'file_url': self.file_url,
        })
        attachment_id = self.env['ir.attachment'].sudo().create(
            {'name': self.name,
             'datas': self.attachment,
             'res_model': 'document.file',
             'res_id': doc_id.id,
             }
        )
        doc_id.attachment_id = attachment_id.id
        self.unlink()
        return {
            'name': _('Trash'),
            'target': 'main',
            'view_mode': 'tree,form',
            'res_model': 'document.trash',
            'type': 'ir.actions.act_window',
        }

    @api.onchange('days')
    def _onchange_days(self):
        """
        Set the delete date for a record based on the specified number of days.
        This function calculates and sets the delete date for a record by
        adding the specified number of days to the current date.
        The record will be automatically deleted on the calculated delete date.
        :return: None
        """
        self.delete_date = fields.Date.add(fields.Date.today(), days=self.days)

    def auto_delete_doc(self):
        """
        Automatically delete documents based on a schedule action.
        This function searches for documents marked for automatic deletion
        (is_auto_delete=True) and with a delete date less than or equal to the
        current date. It then deletes these documents from the system.
        :return: None
        """
        self.search([
            ('is_auto_delete', '=', True),
            ('delete_date', '!=', False),
            ('delete_date', '<=', fields.Date.today())
        ]).unlink()
