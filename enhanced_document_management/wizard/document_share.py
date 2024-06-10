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
