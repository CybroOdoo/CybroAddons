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
from zipfile import ZipFile
from odoo import api, fields, models
from odoo.http import request


class Document(models.Model):
    """ Model used to store documents, perform document related functions """
    _name = 'document.file'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Documents Community'

    name = fields.Char(string="Name", help="Document name")
    attachment = fields.Binary(string='File', help="Document data")
    date = fields.Datetime(string='Date', help="Document create date")
    workspace_id = fields.Many2one(
        'document.workspace', string='Workspace',
        required=True, help="workspace name")
    user_id = fields.Many2one(
        'res.users', string='Owner',
        default=lambda self: self.env.user,
        help="""Owner name, if the document belongs to a specific partner""")
    brochure_url = fields.Char(string="URL", help="Document sharable URL")
    extension = fields.Char(
        string='Extension',
        help="""Document extension, helps to determine the file type""")
    priority = fields.Selection(
        [('0', 'None'), ('1', 'Favorite')],
        string="Priority", help="Favorite button")
    activity_ids = fields.One2many(
        'mail.activity', string='Activities',
        help="Created activity for this attachment")
    attachment_id = fields.Many2one(
        'ir.attachment', string="Data",
        help="Used to access datas without search function")
    content_url = fields.Char(
        string='Content Url', help="It store the URL for url type documents")
    content_type = fields.Selection(
        [('file', 'File'), ('url', 'Url')], string="Content Type",
        help="Document content type")
    preview = fields.Char(
        string='Preview', help="Used to show a preview for URL file type")
    active = fields.Boolean(
        string='Active', default=True, help="It specify archived file")
    deleted_date = fields.Date(
        string="Deleted Date", help="File deleted date")
    mimetype = fields.Char(
        string='Mime Type', help="Document mimetype")
    description = fields.Text(string='Description', help="Short description")
    security = fields.Selection(
        selection=[
            ('private', 'Private'),
            ('managers_and_owner', 'Managers & Owner'),
            ('specific_users', 'Specific Users')
        ], default='managers_and_owner', string="Security",
        help="""Privet : only the uploaded user can view
                Managers & Owner : Document shared with Managers """)
    user_ids = fields.Many2many(
        'res.users', help="Can access the documents", string="User Access")
    partner_id = fields.Many2one(
        'res.partner', help="Document related partner name",
        string="Related Partner")
    auto_delete = fields.Boolean(
        string='Auto Delete', default=False,
        help="Document delete status")
    days = fields.Integer(string='Days', help="auto delete in days")
    trash = fields.Boolean(string='Trash', help="To specify deleted items")
    delete_date = fields.Date(
        string='Date Delete', readonly=True,
        help="Used to calculate file remove date from trash")
    file_url = fields.Char(
        string='File URL',
        help="""it store url while adding an url document""")
    size = fields.Char(
        string='Size', compute='_compute_size',
        help="it store size of the document")
    company_id = fields.Many2one(
        related='workspace_id.company_id', string='Company',
        help="Company Name")

    @api.depends('attachment_id')
    def _compute_size(self):
        """Function is used to fetch the file size of an attachment"""
        for rec in self:
            rec.size = str(rec.attachment_id.file_size / 1000) + ' Kb'

    @api.onchange('days')
    def _onchange_days(self):
        """Function is used to add delete date for a record ,
        it automatically deleted at the specified date"""
        self.delete_date = fields.Date.add(fields.Date.today(), days=self.days)

    def auto_delete_doc(self):
        """Function to delete document automatically using schedule action"""
        self.search([
            ('auto_delete', '=', True),
            ('delete_date', '<=', fields.Date.today())]).unlink()

    def action_upload_document(self):
        """Function it works while uploading a file, and it adds some basic
        information about the file"""
        # important to maintain extension and name as different
        attachment_id = self.env['ir.attachment'].sudo().create({
            'name': self.name,
            'datas': self.attachment,
            'res_model': 'document.file',
            'res_id': self.id,
            'public': True,
        })
        self.sudo().write({
            'name': self.name,
            'date': fields.Date.today(),
            'user_id': self.env.uid,
            'extension': self.name.split(".")[len(self.name.split(".")) - 1],
            'content_url':
                f"/web/content/{attachment_id.id}/{self.name}",
            'mimetype': attachment_id.mimetype,
            'attachment_id': attachment_id.id,
            'brochure_url': attachment_id.local_url
        })
        if self.env.context.get('active_model') == "request.document":
            self.env['request.document'].search(
                [('id', '=', self.env.context.get('active_id'))]).write({
                    'state': 'accepted'
                })
        return {
            'type': 'ir.actions.client',
            'tag': 'reload'
        }

    @api.model
    def archive_function(self, document_selected):
        """ Function to download document as a ZIP """
        zip_obj = ZipFile('attachments.zip', 'w')
        for doc in self.browse(document_selected):
            zip_obj.write(doc.attachment_id._full_path(
                doc.attachment_id.store_fname),
                doc.attachment_id.name)
        zip_obj.close()
        url = f"{request.httprequest.host_url[:-1]}/web/attachments/download"
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'self',
        }

    @api.model
    def document_file_delete(self, doc_ids):
        """Function works while deleting a document,
         it creates a record in document.trash"""
        for docs in self.browse(doc_ids):
            self.env['document.trash'].create({
                'name': docs.name,
                'attachment': docs.attachment,
                'document_create_date': docs.date,
                'workspace_id': docs.workspace_id.id,
                'user_id': docs.user_id.id,
                'brochure_url': docs.brochure_url,
                'extension': docs.extension,
                'priority': docs.priority,
                'attachment_id': docs.attachment_id.id,
                'content_url': docs.content_url,
                'content_type': docs.content_type,
                'preview': docs.preview,
                'active': docs.active,
                'deleted_date': fields.Date.today(),
                'mimetype': docs.mimetype,
                'description': docs.description,
                'security': docs.security,
                'user_ids': docs.user_ids.ids,
                'partner_id': docs.partner_id.id,
                'days': docs.days,
                'file_url': docs.file_url,
            })
            docs.unlink()

    @api.model
    def document_file_archive(self, documents_selected):
        """Function to archive document, it deleted automatically
            based on delete date"""
        for docs in self.browse(documents_selected):
            if docs.active:
                docs.active = False
            elif docs.delete_date:
                docs.delete_date = False
                docs.active = True
            else:
                docs.active = True

    @api.model
    def on_mail_document(self, doc_ids):
        """Function used to send document as an email attachment"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'mail',
            'res_model': 'mail.compose.message',
            'view_mode': 'form',
            'target': 'new',
            'views': [[False, 'form']],
            'context': {
                'default_attachment_ids': self.browse(
                    doc_ids).mapped('attachment_id').ids,
            }
        }

    @api.model
    def action_btn_create_task(self, doc):
        """Function used to create a task based on document """
        module_id = self.env['ir.module.module'].search(
            [('name', '=', 'project')])
        if module_id.state == 'installed':
            for rec in self.browse(doc):
                task_id = self.env['project.task'].create({
                    'name': rec['name']
                })
                rec.attachment_id.res_model = 'project.task'
                rec.attachment_id.res_id = task_id
            return True
        return False

    @api.model
    def action_btn_create_lead(self, doc):
        """Function to create a CRM lead based on a document """
        module_id = self.env['ir.module.module'].search([('name', '=', 'crm')])
        if module_id.state == 'installed':
            for rec in self.browse(doc):
                lead_id = self.env['crm.lead'].create({
                    'name': rec['name']
                })
                rec.attachment_id.res_model = 'crm.lead'
                rec.attachment_id.res_id = lead_id
            return True
        return False

    @api.model
    def delete_doc(self):
        """Function to delete document from trash """
        limit = self.env['ir.config_parameter'].sudo().get_param(
            'document_management.trash')
        for rec in self.env['document.trash'].search(
                ['deleted_date', '!=', False]):
            delta = fields.Date.today() - rec.deleted_date
            if delta.days == limit:
                rec.unlink()
