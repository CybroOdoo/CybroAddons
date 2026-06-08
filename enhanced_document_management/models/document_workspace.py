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

class DocumentWorkspace(models.Model):
    """ Model to store document workspace """
    _name = 'document.workspace'
    _inherit = ['mail.thread']
    _description = "Document Workspace"

    name = fields.Char(string='Name', required=True,
                       help="Name of the workspace.")
    display_name = fields.Char(string='Workspace',
                               compute='_compute_display_name',
                               help="Name of the workspace.")
    company_id = fields.Many2one('res.company', string='Company',
                                 help="Workspace belongs to this company",
                                 default=lambda self: self.env.company)
    description = fields.Text(string='Description',
                              help="Description of the workspace.")
    document_count = fields.Integer(compute='_compute_document_count',
                                    string='Document Count',
                                    help="Number of documents uploaded "
                                         "under this workspace")
    privacy_visibility = fields.Selection([
        ('followers', 'Invited internal users (private)'),
        ('employees', 'All internal users'), ],
        string='Visibility', required=True,
        default='employees',
        help='- Invited internal users: when following a workspace, internal '
             'users will get access to all of its documents without '
             'distinction \n\n'
             'All internal users: all internal users can access the '
             'workspace and all of its documents without distinction.\n\n')


    _sql_constraints = [
        ('name_company_uniq', 'unique (name, company_id)', 'The name of the workspace must be unique per company!'),
    ]

    def action_button_view_document(self):
        """
        Open the Kanban view of associated documents.
        This function opens the Kanban view displaying documents associated
        with the current workspace.
        :return: Action to open the Kanban view
        """
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'document.file',
            'name': self.name,
            'view_mode': 'kanban,form',
            'view_type': 'form',
            'target': 'current',
            'domain': [('workspace_id', '=', self.id)]
        }

    @api.depends('name')
    def _compute_display_name(self):
        """ compute function to get display name """
        for record in self:
            record.display_name = record.name

    def _compute_document_count(self):
        """
        Calculate the number of documents associated with this workspace.
        This function computes the count of documents that belong to the
        current workspace.
        """
        for record in self:
            record.document_count = self.env['document.file'].search_count(
                [('workspace_id', '=', record.id)])
