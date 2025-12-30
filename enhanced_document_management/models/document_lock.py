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
import hashlib
from odoo import fields, models


class DocumentLock(models.Model):
    """Model used to lock documents and do other functions
     for locked documents"""
    _name = 'document.lock'
    _description = 'Document Lock'
    _rec_name = 'document_file_id'

    document_file_id = fields.Many2one('document.file', string='document file',
                                       help="id of document file")
    password = fields.Char(string='password', required=True,
                           help="Password to lock document")
    is_lock = fields.Boolean(string="Lock",
                             help='field for document is lock or not')

    def lock_doc(self):
        """
        Lock a document.
        This method allows authorized users to lock a document by setting a
        password for it.It checks if the user has the
        'enhanced_document_management.view_all_document' group. If the user has permission,
        it hashes the provided password and sets the 'is_lock' flag to True for
        both the document and its associated file.
        :return: None or a notification if the user does not have permission.
        """
        if self.env.user.has_group('enhanced_document_management.view_all_document'):
            self.write({
                'password': hashlib.sha256(self.password.encode()).hexdigest(),
                'is_lock': True

            })
            self.document_file_id.is_locked = True
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': "You dont have permission to"
                               " lock the documents",
                    'type': 'info',
                    'sticky': False,
                }
            }

    def unlock_doc(self):
        """
        Unlock a document.
        This method allows users to unlock a locked document by verifying the
        provided password.It hashes the provided password and checks if it
        matches the stored password for the document. If the passwords match,
        the document is unlocked, and the associated lock records are removed.
        If the passwords do not match, an incorrect password
         notification is displayed.
        :return: None or a notification if the password is incorrect.
        :rtype: None or dict
        """
        password = hashlib.sha256(self.password.encode()).hexdigest()
        self.write({
            'password': hashlib.sha256(self.password.encode()).hexdigest()
        })
        if password == self.env['document.lock'].search(
                [('document_file_id', '=', self.document_file_id.id),
                 ('is_lock', '=', True)],
                order="id desc").password:
            self.document_file_id.is_locked = False
            self.env['document.lock'].search(
                [('document_file_id', '=', self.document_file_id.id),
                 ('is_lock', '=', True)],
                order="id desc").unlink()
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': "Incorrect Password",
                    'type': 'danger',
                    'sticky': False,
                }
            }

    def document_share(self):
        """
        Share a locked document.
        This method allows users to share a locked document by verifying the
        provided password.It hashes the provided password and checks if it
        matches the stored password for the document. If the passwords match,
        the document is shared using the 'document.share' model.
        If the passwords do not match, an incorrect password notification is
         displayed.
        :return: URL for sharing the document or a notification
         if the password is incorrect.
        """
        password = hashlib.sha256(self.password.encode()).hexdigest()
        self.write({
            'password': hashlib.sha256(self.password.encode()).hexdigest()
        })
        if password == self.env['document.lock'].search(
                [('document_file_id', '=', self.document_file_id.id),
                 ('is_lock', '=', True)],
                order="id desc").password:
            return self.env['document.share'].create_url(
                [self.document_file_id.id])
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': "Incorrect Password",
                    'type': 'danger',
                    'sticky': False,
                }
            }

    def document_download(self):
        """
        Download a locked document.
        This method allows users to download a locked document by verifying
        the provided password.It hashes the provided password and checks
        if it matches the stored password for the document. If the passwords
        match, the document is downloaded using 'ir.actions.act_url'.
        If the passwords do not match, an incorrect password notification is
        displayed.
        :return: Action to download the document or a notification
        if the password is incorrect.
        """
        password = hashlib.sha256(self.password.encode()).hexdigest()
        self.write({
            'password': hashlib.sha256(self.password.encode()).hexdigest()
        })
        if password == self.env['document.lock'].search(
                [('document_file_id', '=', self.document_file_id.id),
                 ('is_lock', '=', True)],
                order="id desc").password:
            document_url = self.env.context.get('document_url', False)
            return {
                'type': 'ir.actions.act_url',
                'url': document_url + '?download=true',
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': "Incorrect Password",
                    'type': 'danger',
                    'sticky': False,
                }
            }

    def document_create_lead(self):
        """
        Create a lead for a locked document.
        This method allows users to create a lead for a locked document by
        verifying the provided password.
        It hashes the provided password and checks if it matches the stored
        password for the document. If the passwords match, it calls the
        'action_btn_create_lead' method of the associated document file
        to create a lead. If the passwords do not match, an incorrect
        password notification is displayed.
        :return: Action to create a lead, a notification for CRM module
         installation,or a notification for an incorrect password.
        """
        password = hashlib.sha256(self.password.encode()).hexdigest()
        self.write({
            'password': hashlib.sha256(self.password.encode()).hexdigest()
        })
        if password == self.env['document.lock'].search(
                [('document_file_id', '=', self.document_file_id.id),
                 ('is_lock', '=', True)],
                order="id desc").password:
            result = self.document_file_id.action_btn_create_lead(
                self.document_file_id.id)
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
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': "Incorrect Password",
                    'type': 'danger',
                    'sticky': False,
                }
            }

    def document_create_task(self):
        """
        Create a task for a locked document.
        This method allows users to create a task for a locked document by
        verifying the provided password.It hashes the provided password and
        checks if it matches the stored password for the document. If the
        passwords match, it calls the 'action_btn_create_task' method of the
        associated document file to create a task. If the passwords do not
        match, an incorrect password notification is displayed.
        :return: Action to create a task, a notification for Project module
        installation,or a notification for an incorrect password.
        """
        password = hashlib.sha256(self.password.encode()).hexdigest()
        self.write({
            'password': hashlib.sha256(self.password.encode()).hexdigest()
        })
        if password == self.env['document.lock'].search(
                [('document_file_id', '=', self.document_file_id.id),
                 ('is_lock', '=', True)],
                order="id desc").password:
            result = self.document_file_id.action_btn_create_task(
                self.document_file_id.id)
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
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': "Incorrect Password",
                    'type': 'danger',
                    'sticky': False,
                }
            }

    def document_lock_mail(self):
        """
        Create mail for locked documents.This method allows users to create a
        mail for a locked document by verifying the provided password.It
        hashes the provided password and checks if it matches the stored
        password for the document. If the passwords match, it calls the
        'on_mail_document' method of the associated document file to create a
        mail. If the passwords do not match, an incorrect password notification
        is displayed.
        :return: Action to create a mail or a notification for an incorrect
        password.
        """
        password = hashlib.sha256(self.password.encode()).hexdigest()
        self.write({
            'password': hashlib.sha256(self.password.encode()).hexdigest()
        })
        if password == self.env['document.lock'].search(
                [('document_file_id', '=', self.document_file_id.id),
                 ('is_lock', '=', True)],
                order="id desc").password:
            return self.document_file_id.on_mail_document(
                [self.document_file_id.id])
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': "Incorrect Password",
                    'type': 'danger',
                    'sticky': False,
                }
            }

    def document_copy_mail(self):
        """
        Copy or move locked documents.
        This method allows users to copy or move locked documents from one
        workspace to another by verifying the provided password. It hashes the
        provided password and checks if it matches the stored password
        for the document. If the passwords match, it opens a window to copy or
        move the document. If the passwords do not match, an incorrect
        password notification is displayed.
        :return: Action to copy or move documents or a notification for an
        incorrect password.
        """
        password = hashlib.sha256(self.password.encode()).hexdigest()
        self.write({
            'password': hashlib.sha256(self.password.encode()).hexdigest()
        })
        if password == self.env['document.lock'].search(
                [('document_file_id', '=', self.document_file_id.id),
                 ('is_lock', '=', True)],
                order="id desc").password:
            return {
                'type': 'ir.actions.act_window',
                'name': 'copy',
                'res_model': 'work.space',
                'view_mode': 'form',
                'target': 'new',
                'views': [[False, 'form']],
                'context': {
                    'default_doc_ids': [self.document_file_id.id]
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': "Incorrect Password",
                    'type': 'danger',
                    'sticky': False,
                }
            }

    def document_lock_archive(self):
        """
        Archive locked documents after verifying the password.
        This method archives locked documents by checking the provided password
        against the stored password.If the passwords match, it archives the
        document using the 'document_file_archive' method of the associated
        document file. If not, it displays an incorrect password notification.
        :return: Archive action or incorrect password notification.
        """
        password = hashlib.sha256(self.password.encode()).hexdigest()
        self.write({
            'password': hashlib.sha256(self.password.encode()).hexdigest()
        })
        if password == self.env['document.lock'].search(
                [('document_file_id', '=', self.document_file_id.id),
                 ('is_lock', '=', True)],
                order="id desc").password:
            self.document_file_id.document_file_archive(
                self.document_file_id.id)
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': "Incorrect Password",
                    'type': 'danger',
                    'sticky': False,
                }
            }

    def document_move_to_trash(self):
        """
        Move locked documents to the trash folder after password verification.
        This method moves locked documents to the trash folder by verifying the
        provided password against the stored password. If the passwords match,
        it performs the document deletion using the 'document_file_delete'
        method of the associated document file. If not, it displays an
        incorrect password notification.
        :return: Trash action or incorrect password notification.
        """
        password = hashlib.sha256(self.password.encode()).hexdigest()
        self.write({
            'password': hashlib.sha256(self.password.encode()).hexdigest()
        })
        if password == self.env['document.lock'].search(
                [('document_file_id', '=', self.document_file_id.id),
                 ('is_lock', '=', True)],
                order="id desc").password:
            self.document_file_id.document_file_delete(
                self.document_file_id.id)
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': "Incorrect Password",
                    'type': 'danger',
                    'sticky': False,
                }
            }

    def document_delete_permanent(self):
        """
        Permanently delete locked documents after password verification.
        This method permanently deletes locked documents by verifying the
        provided password against the stored password. If the passwords match,
        it deletes the document using the 'unlink' method of the associated
        document file. If not, it displays an incorrect password notification.
        :return: Deletion action or incorrect password notification.
        """
        password = hashlib.sha256(self.password.encode()).hexdigest()
        self.write({
            'password': hashlib.sha256(self.password.encode()).hexdigest()
        })
        if password == self.search(
                [('document_file_id', '=', self.document_file_id.id),
                 ('is_lock', '=', True)], order="id desc").password:
            self.document_file_id.unlink()
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': "Incorrect Password",
                    'type': 'danger',
                    'sticky': False,
                }
            }
