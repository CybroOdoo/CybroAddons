# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import urllib.parse
from odoo import api, fields, models
from odoo.exceptions import UserError


class ProjectShortcut(models.TransientModel):
    """Custom Project Shortcut Wizard"""
    _name = 'project.shortcut'
    _description = 'Custom Project Shortcut Wizard'

    name = fields.Char(string='Name', required=True, help='Name of the'
                                                          ' shortcut')
    link = fields.Char(string='Link', required=True, help='URL link of the '
                                                          'shortcut')
    project_id = fields.Many2one('project.project', string='Project',
                                 help='Associated Project')
    is_shortcuts = fields.Boolean(string="Has Shortcuts", readonly=True,
                                  help='Check if there are shortcuts')

    @api.model
    def default_get(self, fields):
        """Get default values for the wizard."""
        defaults = super(ProjectShortcut, self).default_get(fields)
        active_project_id = self.env.context.get('active_id')
        if active_project_id:
            defaults['project_id'] = active_project_id
        return defaults

    @staticmethod
    def is_valid_url(url):
        """Check if the URL is valid."""
        try:
            result = urllib.parse.urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    def action_project_shortcut(self):
        """Create or update project shortcuts."""
        project = self.project_id
        if project:
            if not self.is_valid_url(self.link):
                raise UserError("Invalid URL. Please enter a valid URL.")
            project.write({'url_link': self.link,
                           'url_name': self.name,
                           'is_active': True})
