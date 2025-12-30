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
from linkpreview import Link, LinkGrabber, LinkPreview
from odoo import api, fields, models
from odoo.exceptions import UserError


class DocumentUrl(models.TransientModel):
    """model help to add URL type documents"""
    _name = 'document.url'
    _description = 'Url Upload Wizard'

    url = fields.Char(string='Url', help='URL to upload')
    workspace_id = fields.Many2one('document.workspace', required=True,
                                   string='Workspace', help="Related workspace")
    name = fields.Char(string='Name', help="Document name")
    preview = fields.Char(string='Url Preview',
                          help="store generated url preview")

    @api.onchange('url')
    def _onchange_url(self):
        """Function to fetch data from url"""
        self.preview = None
        try:
            if self.url:
                url = self.url
                grabber = LinkGrabber(
                    initial_timeout=20, maxsize=1048576, receive_timeout=10,
                    chunk_size=1024,
                )
                content, url = grabber.get_content(url)
                link = Link(url, content)
                preview = LinkPreview(link, parser="lxml")
                self.name = preview.title
                self.preview = preview.image
        except Exception as e:
            raise UserError(e)

    def action_add_url(self):
        """function to create documents based for URL"""
        self.env['document.file'].create({
            'name': self.name,
            'date': fields.Date.today(),
            'workspace_id': self.workspace_id.id,
            'user_id': self.env.uid,
            'extension': 'url',
            'content_url': self.url,
            'content_type': 'url',
            'preview': self.preview,
            'brochure_url': self.url
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
