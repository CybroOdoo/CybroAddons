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
import requests
from bs4 import BeautifulSoup

from odoo import api, fields, models


class UrlUploadWizard(models.TransientModel):
    """Model help to add URL type documents"""
    _name = 'document.url'
    _description = 'Url Upload Wizard'

    url = fields.Char(string='Url', help='URL to upload')
    workspace_id = fields.Many2one(
        'document.workspace', required=True, string="Workspace",
        help='Workspace to upload')
    name = fields.Char(help='Name of the document', string='Document Name')

    @api.onchange('url')
    def _onchange_url(self):
        """Function to fetch data from url"""
        if self.url:
            response = requests.get(self.url, stream=True)
            response.raise_for_status()
            # Read only enough content to find the title tag
            content = b""
            for chunk in response.iter_content(chunk_size=1024):
                content += chunk
                if b"</title>" in content:
                    break
            soup = BeautifulSoup(content, 'html.parser')
            self.name = soup.find('title').string

    def action_add_url(self):
        """Function to create documents based for URL"""
        self.env['document.file'].create({
            'name': self.name,
            'date': fields.Date.today(),
            'workspace_id': self.workspace_id.id,
            'user_id': self.env.uid,
            'extension': 'url',
            'content_url': self.url,
            'content_type': 'url',
            'brochure_url': self.url
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
