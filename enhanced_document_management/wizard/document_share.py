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
import uuid
from odoo import api, fields, models, _
from odoo.http import request


class DocumentShare(models.Model):
    """Model to share all shared document dats"""
    _name = 'document.share'
    _description = 'Document Share'

    url = fields.Char(
        string='File Url', readonly=True, help="Document Public URL")
    document_ids = fields.Many2many(
        'document.file', string="Documents",
        help="Shared Document IDs")
    user_ids = fields.Many2many(
        'res.users', string="Users", help="Shared User")
    unique = fields.Char(
        string='Unique Access ID', readonly=True, help="Hash code for privacy")

    @api.model
    def create_url(self, document_ids):
        """Functon to create unique id and sharable
            urls for selected documents"""
        unique_id = uuid.uuid4()
        url = (f"{request.httprequest.host_url[:-1]}/web/content/share/"
               f"?unique={unique_id}")
        self.create({
            'url': url,
            'document_ids': document_ids,
            'unique': unique_id
        })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Share'),
            'res_model': 'document.share',
            'view_mode': 'form',
            'target': 'new',
            'views': [[False, "form"]],
            'context': {
                'default_url': url
            }
        }
