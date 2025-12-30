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
from odoo import fields, models


class DocumentDeleteTrash(models.Model):
    _name = "document.delete.trash"
    _description = "document permanent delete or move to trash"

    document_file_id = fields.Many2one("document.file",
                                       string='document file id',
                                       help='file if of document to delete')

    def document_move_trash(self):
        """
        Move a document to the trash if it is not locked, otherwise return an
         action to unlock the document.
        This method checks if a document is locked. If it is not locked, it
         moves the document to the trash.
        If the document is locked, it returns an action to unlock the document.
        :return: Action to move to the trash or unlock the document.
        :rtype: dict or None
        """
        if not self.document_file_id.is_locked:
            self.document_file_id.document_file_delete(
                self.document_file_id.id)
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Lock',
                'res_model': 'document.lock',
                'view_mode': 'form',
                'view_id': self.env.ref(
                    'enhanced_document_management.document_lock_move_trash_view_form').id,
                'target': 'new',
                'context': {
                    'default_document_file_id': self.document_file_id.id,
                }
            }

    def document_permanent_delete(self):
        """
        Permanently delete a document if it is not locked, or return an action
         to unlock the document.
        This method checks if a document is locked. If it is not locked, it
        permanently deletes the document.
        If the document is locked, it returns an action to unlock the document.
        :return: Action to permanently delete or unlock the document.
        :rtype: dict or None
        """
        if not self.document_file_id.is_locked:
            self.document_file_id.unlink()
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Lock',
                'res_model': 'document.lock',
                'view_mode': 'form',
                'view_id': self.env.ref(
                    'enhanced_document_management.document_lock_delete_view_form').id,
                'target': 'new',
                'context': {
                    'default_document_file_id': self.document_file_id.id,
                }
            }
