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
from odoo import fields, models

class DocumentDeleteTrash(models.Model):
    """Document Deletion and Trash Management"""
    _name = "document.delete.trash"
    _description = "Document Delete Trash"

    document_file_id = fields.Many2one("document.file",
                                       string='document file id',
                                       help='ID of the document file to delete')

    def action_document_move_trash(self):
        """
        Move a document to the trash.
        :return: Action to move to the trash.
        :rtype: dict or None
        """
        self.document_file_id.document_file_delete(
            self.document_file_id.id)

    def action_document_permanent_delete(self):
        """
        Permanently delete a document.
        :return: Action to permanently delete.
        :rtype: dict or None
        """
        self.document_file_id.with_context(force_delete=True).unlink()
