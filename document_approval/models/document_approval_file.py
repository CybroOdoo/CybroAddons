# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sreeshanth V S(<https://www.cybrosys.com>)
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
from odoo import fields, models, _
from odoo.exceptions import UserError


class DocumentApprovalFiles(models.Model):
    """ Manage the documents for approvals"""
    _name = 'document.approval.file'
    _description = "document files"

    name = fields.Char(string="Name", required=True,
                       help='For adding some noted about the file ')
    file = fields.Binary(string="File", required=True,
                         help='For storing the file')
    file_name = fields.Char(string="File Name",
                            help="Storing name of the file")
    approval_id = fields.Many2one('document.approval',
                                  help='Inverse fields for the document '
                                       'approval')

    def unlink(self):
        """Supering the method unlink of model document.approval.line to
        restrict the deleting of the file"""
        for rec in self:
            if rec.approval_id.state != 'Draft':
                raise UserError(
                    _(f"You cannot delete file from {rec.approval_id.state} state"))
            super(DocumentApprovalFiles, rec).unlink()
