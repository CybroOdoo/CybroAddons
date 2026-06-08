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


class DocumentFile(models.Model):
    """ Model used to store documents, perform document related functions """
    _name = 'document.file'
    _description = "Documents"

    name = fields.Char(string="Name", help="Document name")
    attachment = fields.Binary(string='File', help="Document data")
    date = fields.Datetime(string='Date', help="Document create date")
    workspace_id = fields.Many2one('document.workspace',
                                   string='Workspace',
                                   required=True,
                                   help="Workspace associated with this document.")
    security = fields.Selection(
        selection=[
            ('private', 'Private'),
            ('managers_and_owner', 'Managers & Owner'),
            ('specific_users', 'Specific Users')
        ], default='managers_and_owner', string="Security",
        help="Private: only the uploaded user can view Managers & Owner: Document shared with Managers")
    user_id = fields.Many2one('res.users', string='Owner',
                              default=lambda self: self.env.user,
                              help="Owner of the document.")
    brochure_url = fields.Char(string="URL", help="Shareable URL of the document")
    extension = fields.Char(string='Extension',
                            help="""Document extension, helps to determine the file type.""")
    priority = fields.Selection(
        [('0', 'None'), ('1', 'Favorite')],
        string="Priority", help="Priority/Favorite status.")
    attachment_id = fields.Many2one('ir.attachment', ondelete='restrict',
                                    help="Attached item")
    content_url = fields.Char(string='Content Url',
                              help='Content URL')
    content_type = fields.Selection(
        selection=[('file', 'File'), ('url', 'Url')],
        help="Document content type", string="Content type")
    preview = fields.Char(string='Preview', help="Preview URL")
    active = fields.Boolean(string='Active', default=True,
                            help="Indicates whether the document is active.")
    deleted_date = fields.Date(string="Deleted Date",
                               help="Document auto delete date")
    mimetype = fields.Char(string='Mime Type', help="Document mimetype")
    description = fields.Text(string='Description',
                              help="Description of the document.")
    user_ids = fields.Many2many('res.users', string="User",
                                help="Users allowed to access this document.")
    partner_id = fields.Many2one('res.partner', string="Partner",
                                 help="Partner related to this document.")
    is_auto_delete = fields.Boolean(string='Auto Delete', default=False,
                                    help="Enable automatic document deletion.")
    days = fields.Integer(string='Days', help="Automatic deletion after specified number of days.")
    is_trash = fields.Boolean(string='Trash', help="To specify deleted items")
    delete_date = fields.Date(string='Date Delete', readonly=True, store=True)
    file_url = fields.Char(string='File URL',
                           help="URL stored for a document created from a link.")
    size = fields.Char(string='Size', compute='_compute_size',
                       help='Computed size of the document.')
    is_locked = fields.Boolean(string="Lock document",
                               help="Whether the document is locked.",
                               default=False)
    document_file_id = fields.Many2one('document.file', string='Document File',
                                       help="Add document here")

    is_crm_install = fields.Boolean(string="is crm installed",
                                    help="Indicates whether the CRM module is installed.")
    is_project_install = fields.Boolean(string="is project installed",
                                        help="Indicates whether the Project module is installed.")
    document_tag_ids = fields.Many2many('document.tag', string='Tags')

    def _is_module_installed(self, module_name):
        """Return whether a technical module is installed.

        Reading ir.module.module requires elevated rights for regular document
        users, so sudo is intentionally scoped to this system model only.
        """
        return self.env['ir.module.module'].sudo().search_count(
            [('name', '=', module_name), ('state', '=', 'installed')],
            limit=1) > 0

    def cron_auto_delete_doc(self):
        """Function to delete document automatically using schedule action"""
        self.search([
            ('is_auto_delete', '=', True),
            ('delete_date', '<=', fields.Date.today())]).unlink()

    @api.depends('attachment_id')
    def _compute_size(self):
        """Function is used to fetch the file size of an attachment"""
        for rec in self:
            rec.size = str(rec.attachment_id.file_size / 1000) + ' Kb'

    def action_upload_document(self):
        """Function it works while uploading a file, and it adds some basic
        information about the file"""
        self.ensure_one()
        # important to maintain extension and name as different
        attachment_id = self.env['ir.attachment'].sudo().create({
            'name': self.name,
            'datas': self.attachment,
            'res_model': 'document.file',
            'res_id': self.id,
            'public': True,
        })
        self.write({
            'name': self.name,
            'date': fields.Date.today(),
            'user_id': self.env.uid,
            'extension': self.name.split(".")[len(self.name.split(".")) - 1],
            'content_url':
                f"/web/content/{attachment_id.id}/{self.name}",
            'mimetype': attachment_id.mimetype,
            'attachment_id': attachment_id.id,
            'brochure_url': attachment_id.local_url,
            'is_crm_install': self._is_module_installed('crm'),
            'is_project_install': self._is_module_installed('project')
        })
        if self.env.context.get('active_model') == "request.document":
            self.env['request.document'].browse(
                self.env.context.get('active_id')).write({
                    'state': 'accepted'
                })
        return {
            'type': 'ir.actions.client',
            'tag': 'soft_reload'
        }

    @api.model
    def action_document_request_upload_document(self, *args):
        """
        Upload a document and add basic information about the file to the
         database.This function is used to upload a file and create a
         corresponding database record with basic information about the
         uploaded file, such as name, date, extension, and more.
        :param args: A tuple containing a dictionary with information about
        the uploaded file.
        :type args: Tuple,
        :return: None
        """
        file_name = args[0]['file_name']
        file_data = args[0]['file']
        workspace_id = args[0].get('workspace_id') or self.env[
            'document.workspace'].search([], order='id', limit=1).id
        base_url = (self.env['ir.config_parameter'].sudo().
                    get_param('web.base.url'))
        document = self.create({
            'attachment': file_data,
            'workspace_id': workspace_id,
            'name': file_name,
            'date': fields.Datetime.now(),
            'user_id': self.env.uid,
            'is_crm_install': self._is_module_installed('crm'),
            'is_project_install': self._is_module_installed('project')
        })
        attachment_id = self.env['ir.attachment'].sudo().create({
            'name': file_name,
            'datas': file_data,
            'res_model': 'document.file',
            'res_id': document.id,
            'public': True,
        })
        document.write({
            'extension': file_name.split(".")[len(file_name.split(".")) - 1],
            'content_url': (
                f"{base_url}/web/content/{attachment_id.id}/{file_name}"
            ),
            'mimetype': attachment_id.mimetype,
            'attachment_id': attachment_id.id,
        })

    @api.model
    def download_zip_function(self, document_selected):
        """
        Download selected documents as a ZIP archive.
        This function generates a URL to download the selected documents
         as a ZIP archive.
        :param document_selected: A list of document IDs to be included in
        the ZIP archive.
        :type document_selected: list
        :return: Action to open url a  for downloading the ZIP archive.
        """
        url = "/get/document?param=" + str(document_selected)
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

    @api.model
    def document_file_delete(self, doc_ids):
        """
        Delete documents and move them to the document.trash.
        This function is responsible for deleting documents and creating
        corresponding records
        in the 'document.trash' table to keep track of the deleted documents.
        :param doc_ids: A list of document IDs to be deleted and moved
         to the trash.
        :type doc_ids: list
        :return: None
        """
        documents = self.browse(doc_ids)
        trash_values = []
        for document in documents:
            trash_values.append({
                'name': document.name,
                'attachment': document.attachment,
                'document_create_date': document.date,
                'workspace_id': document.workspace_id.id,
                'user_id': document.user_id.id,
                'brochure_url': document.brochure_url,
                'extension': document.extension,
                'priority': document.priority,
                'attachment_id': document.attachment_id.id,
                'content_url': document.content_url,
                'content_type': document.content_type,
                'preview': document.preview,
                'active': document.active,
                'deleted_date': fields.Date.today(),
                'mimetype': document.mimetype,
                'description': document.description,
                'security': document.security,
                'user_ids': [(6, 0, document.user_ids.ids)],
                'partner_id': document.partner_id.id,
                'days': document.days,
                'file_url': document.file_url,
            })
        if trash_values:
            self.env['document.trash'].create(trash_values)
            documents.with_context(force_delete=True).unlink()

    def unlink(self):
        """
        Override unlink to move documents to the trash when standard action -> delete is used.
        """
        if not self.env.context.get('force_delete'):
            self.document_file_delete(self.ids)
            return True
        return super().unlink()

    @api.model
    def document_file_archive(self, documents_selected):
        """
        Archive documents and toggle their active status or delete date.
        This function is used to archive documents. Depending on the current
         state of
        the documents, it either toggles the 'active' status to mark them as
        archived
        or clears the 'delete_date' and sets them as active again.
        :param documents_selected: document ID to be archived.
        :type documents_selected: int
        :return: None
        """
        documents = self.browse(documents_selected)
        active_documents = documents.filtered('active')
        active_documents.write({'active': False})
        inactive_documents = documents - active_documents
        deleted_documents = inactive_documents.filtered('delete_date')
        deleted_documents.write({
            'delete_date': False,
            'active': True,
        })
        (inactive_documents - deleted_documents).write({'active': True})

    @api.model
    def on_mail_document(self, doc_ids):
        """
        Open a new email compose window to send selected documents
         as attachments.This function opens a new email compose window with
            selected documents as attachments.The 'doc_ids' parameter
            contains a list of document IDs to be attached to the email.
        :param doc_ids: A list of document IDs to be attached to the email.
        :type doc_ids: list
        :return: Action to open a new email compose window.
        """
        default_composition_mode = self.env.context.get(
            'default_composition_mode',
            self.env.context.get('composition_mode', 'comment'))
        compose_ctx = dict(
            default_composition_mode=default_composition_mode,
            default_model='document.file',
            default_res_ids=doc_ids,
            mail_tz=self.env.user.tz,
            default_attachment_ids=self.browse(doc_ids).mapped(
                'attachment_id').ids
        )
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sent document',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': compose_ctx,
        }

    @api.model
    def action_btn_create_task(self, doc):
        """
        Create a task based on a document if the 'project' module is installed.
        This function checks if the 'project' module is installed and, if so,
        creates a task with the name of the document. It also associates the
         document's attachment with the task.
        :param doc: The document for which a task should be created.
        :type doc: recordset
        :return: True if the task is created, False if the 'project' module
         is not installed.
        :rtype: bool
        """
        if self._is_module_installed('project'):
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
        """
        Create a CRM lead based on a document if the 'crm' module is installed.
        This function checks if the 'crm' module is installed and, if so,
        creates a lead with the name of the document. It also associates
         the document's attachment with the lead.
        :param doc: The document for which a CRM lead should be created.
        :type doc: recordset
        :return: True if the lead is created, False if the 'crm' module is
         not installed.
        :rtype: bool
        """
        if self._is_module_installed('crm'):
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
        """
        Delete documents from the trash based on the configured
        retention period.This function deletes documents from the
        'document.trash' table based on the configured retention period
        specified in the 'enhanced_document_management.trash' parameter.It checks
        the 'deleted_date' of each document in the trash and deletes those
        that have reached or exceeded the retention
        period.
        :return: None
        """
        limit = self.env['ir.config_parameter'].sudo().get_param(
            'enhanced_document_management.trash')
        if not limit:
            return
        try:
            limit = int(limit)
        except ValueError:
            return
        cutoff_date = fields.Date.subtract(fields.Date.today(), days=limit)
        self.env['document.trash'].search([
            ('deleted_date', '<=', cutoff_date)
        ]).unlink()

    def action_click_share(self):
        """
        Share a single document by generating a shareable URL or requesting a
        password for locked documents.
        This function allows users to share a single document.
        If the document is not locked,it generates a shareable URL using the
        'document.share' model. If the document is locked,
        it opens a window to prompt the user to enter a password for access.
        :return: Shareable URL or action to enter a password.
        """
        document_id = self.env.context.get('document_id') or self.id
        if not self.browse(document_id).is_locked:
            return self.env['document.share'].create_url([document_id])
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Please Enter Password',
                'res_model': 'document.lock',
                'view_mode': 'form',
                'views': [(self.env.ref(
                    'enhanced_document_management.document_lock_share_view_form').id, 'form')],
                'target': 'new',
                'context': {
                    'default_document_file_id': document_id,
                }
            }

    def action_click_create_lead(self):
        """
        Create a CRM lead from the document's dropdown menu.
        This method allows users to create a CRM lead from a document if the
        document is not locked.
        If the document is locked, it prompts the user to enter a password.
        :return: Action to create a lead or a notification to install the CRM
         module.
        """
        document_id = self.env.context.get('document_id') or self.id
        if not self.browse(document_id).is_locked:
            result = self.action_btn_create_lead(document_id)
            if not result:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': "Install CRM Module to use this function",
                        'type': 'info',
                        'sticky': False,
                    }
                }
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Please Enter Password',
                'res_model': 'document.lock',
                'view_mode': 'form',
                'target': 'new',
                'views': [(self.env.ref(
                    'enhanced_document_management.document_lock_lead_view_form').id, 'form')],
                'context': {
                    'default_document_file_id': document_id,
                }
            }

    def action_click_create_task(self):
        """
        Create a task from the document's dropdown menu.
        This method allows users to create a task from a document if
         the document is not locked.
        If the document is locked, it prompts the user to enter a password.
        :return: Action to create a task or a notification to install the
        Project module.
        """
        document_id = self.env.context.get('document_id') or self.id
        if not self.browse(document_id).is_locked:
            result = self.action_btn_create_task(document_id)
            if not result:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': "Install Project Module to use this "
                                   "function",
                        'type': 'info',
                        'sticky': False,
                    }
                }
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Please Enter Password',
                'res_model': 'document.lock',
                'view_mode': 'form',
                'target': 'new',
                'views': [(self.env.ref(
                    'enhanced_document_management.document_lock_task_view_form').id, 'form')],
                'context': {
                    'default_document_file_id': document_id,
                }
            }

    def action_click_create_mail(self):
        """
        Create an email from the document's dropdown menu.
        This method allows users to create an email from a document if the
        document is not locked.
        If the document is locked, it prompts the user to enter a password.
        :return: Action to create an email or a window to enter a password.
        """
        document_id = self.env.context.get('document_id') or self.id
        if not self.browse(document_id).is_locked:
            return self.on_mail_document([document_id])
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Please Enter Password',
                'res_model': 'document.lock',
                'view_mode': 'form',
                'target': 'new',
                'views': [(self.env.ref(
                    'enhanced_document_management.document_lock_mail_view_form').id, 'form')],
                'context': {
                    'default_document_file_id': document_id,
                }
            }

    def action_click_copy_move(self):
        """
        Copy or move a document from one workspace to another using the
        document's dropdown.His method allows users with appropriate
        permissions to copy or move a document from one workspace to another.
        It checks if the document is locked and if the user has the
        'enhanced_document_management.view_all_document' group. If the user has permission
         and the document is not locked, it opens a window for copying the
         document. If the document is locked, it prompts the user to enter a
         password. If the user does not have
        permission, it displays a notification.
        :return: Action to copy or move a document, or a notification for
        permission denied.
        """
        document_id = self.env.context.get('document_id') or self.id
        user_group = self.env.user.has_group(
            'enhanced_document_management.view_all_document')
        if user_group:
            if not self.browse(document_id).is_locked:
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'copy',
                    'res_model': 'work.space',
                    'view_mode': 'form',
                    'target': 'new',
                    'views': [[False, 'form']],
                    'context': {
                        'default_doc_ids': [document_id]
                    }
                }
            else:
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Please Enter Password',
                    'res_model': 'document.lock',
                    'view_mode': 'form',
                    'target': 'new',
                    'views': [(self.env.ref(
                        'enhanced_document_management.document_lock_copy_view_form').id, 'form')],
                    'context': {
                        'default_document_file_id': document_id,
                    }
                }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': "You don't have permission to "
                               "perform this action",
                    'type': 'danger',
                    'sticky': False,
                }
            }

    def action_click_document_archive(self):
        """Archive a document from the document's dropdown menu.
        This method allows users to archive a document if the document is not
        locked.
        If the document is locked, it prompts the user to enter a password.
        :return: None or action to enter a password.
        """
        document_id = self.env.context.get('document_id') or self.id
        if not self.browse(document_id).is_locked:
            self.document_file_archive(document_id)
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Please Enter Password',
                'res_model': 'document.lock',
                'view_mode': 'form',
                'target': 'new',
                'views': [(self.env.ref(
                    'enhanced_document_management.document_lock_archive_view_form').id, 'form')],
                'context': {
                    'default_document_file_id': document_id,
                }
            }

    @api.model
    def action_click_open_locked(self, document_id):
        """Return the lock wizard for opening a document."""
        view_id = self.env.ref(
            'enhanced_document_management.document_lock_open_view_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Please Enter Password',
            'res_model': 'document.lock',
            'views': [(view_id, 'form')],
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_document_file_id': document_id,
            }
        }

    def action_click_document_delete(self):
        """
            Delete a document from the document's dropdown menu.

            This method allows users to delete a document if they have the
            'enhanced_document_management.view_all_document' group. It opens a window for
            users to choose between moving the document to the trash or
            permanently deleting it.
            :return: Action to choose between moving to trash or permanent
            deletion.
            """
        document_id = self.env.context.get('document_id') or self.id
        document = self.browse(document_id)
        user_group = self.env.user.has_group(
            'enhanced_document_management.view_all_document')
        if user_group:
            if document.is_locked:
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Please Enter Password',
                    'res_model': 'document.lock',
                    'view_mode': 'form',
                    'target': 'new',
                    'views': [(self.env.ref(
                        'enhanced_document_management.document_lock_delete_view_form').id, 'form')],
                    'context': {
                        'default_document_file_id': document_id,
                    }
                }
            return {
                'type': 'ir.actions.act_window',
                'name': 'Choose One',
                'res_model': 'document.delete.trash',
                'view_mode': 'form',
                'target': 'new',
                'views': [(self.env.ref(
                    'enhanced_document_management.document_delete_trash_view_form').id, 'form')],
                'context': {
                    'default_document_file_id': document_id,
                }
            }

    def action_click_document_lock(self):
        """
        Lock a document from the document's dropdown menu.
        This method allows users to lock a document by opening a window where
        they can set a password for the document. Once locked,
         the document can only be accessed with the provided password.
        :return: Action to set a password and lock the document.
        """
        document_id = self.env.context.get('document_id') or self.id
        document = self.env.ref('enhanced_document_management.document_lock_view_form')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Lock',
            'res_model': 'document.lock',
            'view_mode': 'form',
            'views': [(document.id, 'form')],
            'target': 'new',
            'context': {
                'default_document_file_id': document_id,
            }
        }

    def action_click_document_unlock(self):
        """
        Unlock a document from the document's dropdown menu.
        This method allows users to unlock a locked document by opening a
         window where they can enter
        the document's password for access.
        :return: Action to enter the document's password and unlock it.
        """
        document_id = self.env.context.get('document_id') or self.id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Unlock',
            'res_model': 'document.lock',
            'view_mode': 'form',
            'target': 'new',
            'views': [(self.env.ref(
                'enhanced_document_management.document_unlock_view_form').id, 'form')],
            'context': {
                'default_document_file_id': document_id,
            }
        }

    @api.model
    def get_documents_list(self, *args):
        """Get a list of documents to open the document viewer.
        This method retrieves information about a specific document and a
        list of other documents that can be viewed in the document viewer.
        It provides details such as the document's name, download URL,
        extension, and more. It also checks if a document is viewable based
        on its extension and whether it's locked.
        :param args: A list of arguments, with the first argument being the
        document ID to retrieve.
        :type args: list
        :return: Information about the specified document and a list of other
        viewable documents.
        :rtype: tuple"""
        document = self.browse(int(args[0]))

        viewable_extensions = ['pdf', 'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'bmp']
        viewable_mimetypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml', 'image/bmp', 'application/pdf']

        def check_viewable(doc):
            ext = (doc.extension or '').lower()
            mime = (doc.mimetype or '').lower()
            return ext in viewable_extensions or mime in viewable_mimetypes or mime.startswith('image/')

        def check_pdf(doc):
            ext = (doc.extension or '').lower()
            mime = (doc.mimetype or '').lower()
            return ext == 'pdf' or mime == 'application/pdf'

        def check_image(doc):
            ext = (doc.extension or '').lower()
            mime = (doc.mimetype or '').lower()
            return mime.startswith('image/') or ext in ['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'bmp']

        attachment = ({
            'defaultSource': document.brochure_url,
            'name': document.name,
            'displayName': document.name,
            'downloadUrl': document.brochure_url,
            'extension': document.extension,
            'filename': document.name,
            'id': document.id,
            'is_locked': document.is_locked,
            'originThreadLocalId': 'document.file,' + str(
                document.id),
            'uid': str(document.create_uid.id),
            'isPdf': check_pdf(document),
            'isImage': check_image(document),
            'isViewable': check_viewable(document),
            'mimetype': document.mimetype,
            'urlRoute': "/web/image/" + str(document.attachment_id.id),
        })

        ext_list = viewable_extensions + [e.upper() for e in viewable_extensions]
        domain = [
            '|', '|',
            ('extension', 'in', ext_list),
            ('mimetype', 'ilike', 'image/%'),
            ('mimetype', '=', 'application/pdf')
        ]
        viewable_documents = self.search(domain)

        if check_viewable(document) and document not in viewable_documents:
            viewable_documents |= document

        attachment_list = [{
            'defaultSource': record.brochure_url,
            'name': record.name,
            'displayName': str(record.name),
            'downloadUrl': record.brochure_url,
            'extension': record.extension,
            'filename': record.name,
            'id': record.id,
            'originThreadLocalId': 'document.file,' + str(
                record.id),
            'uid': str(record.create_uid.id),
            'isPdf': check_pdf(record),
            'isImage': check_image(record),
            'isViewable': check_viewable(record),
            'mimetype': record.mimetype,
            'urlRoute': "/web/image/" + str(record.attachment_id.id),
        } for record in viewable_documents]
        return attachment, attachment_list

    @api.model
    def get_document_count(self, *args):
        """
           Get the count of documents in a workspace and all documents.
           This method counts the number of documents in a specific workspace
            and the total number of documents across all workspaces.
           :param args: A list of arguments, with the first argument being the
           workspace ID.
           :type args: list
           :return: A tuple containing the count of documents in the specified
           workspace and the count of all documents.
           :rtype: tuple
           """
        document_count_in_workspace = self.search_count(
            [('workspace_id', '=', args[0])])
        all_document_count = self.search_count([])
        return document_count_in_workspace, all_document_count
