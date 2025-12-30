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


class DocumentRequestAccept(models.TransientModel):
    """model help to Accept and upload document request"""
    _name = 'document.request.accept'
    _description = 'Document Request Accept Wizard'

    document_file = fields.Binary(string='File', help="Choose file")
    workspace_id = fields.Many2one('document.workspace',
                                   string='Workspace', readonly=True)
    description = fields.Char(string='Description', help='Add description')
    document_request_id = fields.Many2one('request.document')
    filename = fields.Char(string='File Name')

    def action_accept_request(self):
        """Method used to Accept the document request and upload a file"""
        self.document_request_id.state = 'accepted'
        args = {
            'file': self.document_file,
            'file_name': self.filename,
            'workspace_id': self.workspace_id.id,
        }
        self.env['document.file'].action_document_request_upload_document(args)
