# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Paid App Development Team (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class DocumentWorkspace(models.Model):
    """ Module to store document workspace """
    _name = 'document.workspace'
    _description = 'Document Workspace'

    name = fields.Char(
        string='Name', required=True, help="Name of the WorkSpace.")
    display_name = fields.Char(
        string='Workspace', help="Name of the workSpace.",
        compute='_compute_display_name')
    parent_id = fields.Many2one(
        'document.workspace', string='Parent Workspace',
        help="Current workSpace will be under this workSpace")
    company_id = fields.Many2one(
        'res.company', string='Company',
        help="WorkSpace belongs to this company",
        default=lambda self: self.env.company)
    description = fields.Text(
        string='Description', help="Description about the workSpace")
    document_count = fields.Integer(
        compute='_compute_document_count', string='Document count',
        help="Number of documents uploaded under this workSpace")

    def action_view_document(self):
        """Function to open document kanban view """
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
        """Function compute display name to view in searchpanel """
        for rec in self:
            rec.display_name = rec.name

    def _compute_document_count(self):
        """Compute function to calculate document count under a workspace """
        for record in self:
            record.document_count = self.env['document.file'].search_count(
                [('workspace_id', '=', self.id)])

    @api.constrains('parent_id')
    def _onchange_parent_id(self):
        """Onchange function to restrict setting
            current workspace as parent workspace"""
        if self.parent_id.id == self.id:
            raise ValidationError(
                _("Cannot set current workspace as parent workspace !"))
        return {
            'domain': {
                'parent_id': [('id', '!=', self.id)]
            }
        }

    @api.model
    def work_spaces(self):
        """Function to send workspace data to friend-end """
        workspace_ids = self.env['document.workspace'].search([])
        workspace_list = [{'id': i.id, 'name': i.name} for i in workspace_ids]
        return workspace_list
