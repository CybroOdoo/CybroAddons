# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from markupsafe import Markup
from odoo import fields, models


class WebsiteSnippetData(models.Model):
    _name = 'website.snippet.data'
    _description = 'AI Generated Website Snippet'

    name = fields.Char(string="Snippet Name", required=True)
    content = fields.Text(string="Snippet Content", required=True)
    image_url = fields.Char(string="Image URL")
    create_date = fields.Datetime(string="Created Date", readonly=True)
    is_ai_generated = fields.Boolean(string="AI Generated")

    def get_content(self):
        return Markup(self.content)
