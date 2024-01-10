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
from odoo import api, fields, models


class WorkSpace(models.TransientModel):
    """Model help to move, copy documents"""
    _name = 'document.tool'

    workspace_ids = fields.Many2many(
        'document.workspace', string='Workspace', required=True,
        help="Workspace to move")
    doc_ids = fields.Many2many(
        'document.file', string='Documents', help='Documents to move')
    move = fields.Boolean(
        compute="_compute_move", default=True, string='Is Move',
        help="Whether it is a move or copy")

    @api.depends('workspace_ids')
    def _compute_move(self):
        """Compute function to enable move function"""
        if len(self.workspace_ids) > 1:
            self.move = False
        else:
            self.move = True

    def action_copy_docs(self):
        """Function to copy documents """
        for workspace in self.workspace_ids.ids:
            for rec in self.doc_ids:
                self.env['document.file'].create({
                    'name': rec.name,
                    'attachment': rec.attachment,
                    'attachment_id': rec.attachment_id.id,
                    'date': fields.Date.today(),
                    'workspace_id': workspace,
                    'user_id': rec.user_id.id,
                    'extension': rec.name.split(".")[
                        len(rec.name.split(".")) - 1]
                })
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def action_move_docs(self):
        """Function to move documents"""
        for rec in self.doc_ids:
            rec.write({
                'workspace_id': self.workspace_ids.id
            })
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
