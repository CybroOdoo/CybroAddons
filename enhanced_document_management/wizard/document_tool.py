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
