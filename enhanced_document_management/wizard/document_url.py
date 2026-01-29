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
