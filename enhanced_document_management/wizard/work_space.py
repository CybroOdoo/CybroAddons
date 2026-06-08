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
from odoo.http import request


class WorkSpace(models.TransientModel):
    """model help to move, copy documents"""
    _name = 'work.space'
    _description = "Workspace"

    workspace_id = fields.Many2many('document.workspace',
                                    string='Workspace', required=True)
    doc_ids = fields.Many2many('document.file',
                               help="Documents to copy or move.",
                               string='Document')
    is_move = fields.Boolean(compute="_compute_is_move", default=True, string="Move",
                          help="Indicates whether to perform a move operation")

    @api.depends('workspace_id')
    def _compute_is_move(self):
        """Compute whether a move operation is permitted (exactly one workspace)."""
        for record in self:
            record.is_move = len(record.workspace_id) == 1

    def action_copy_docs(self):
        """function to copy documents """
        values_list = []
        for workspace in self.workspace_id.ids:
            for document in self.doc_ids:
                values_list.append({
                    'name': document.name,
                    'attachment': document.attachment,
                    'brochure_url': document.brochure_url,
                    'attachment_id': document.attachment_id.id,
                    'mimetype': document.mimetype,
                    'content_url': (
                        f"{request.httprequest.host_url[:-1]}/web/content/"
                        f"{document.attachment_id.id}/{document.name}"
                    ),
                    'date': fields.Datetime.now(),
                    'workspace_id': workspace,
                    'user_id': document.user_id.id,
                    'extension': document.name.split(".")[
                        len(document.name.split(".")) - 1]
                })
        if values_list:
            self.env['document.file'].create(values_list)
        return {
            'type': 'ir.actions.client',
            'tag': 'edm_soft_reload',
        }

    def action_move_docs(self):
        """function to move documents"""
        self.ensure_one()
        self.doc_ids.write({
            'workspace_id': self.workspace_id.id
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'edm_soft_reload',
        }
