# -*- coding: utf-8 -*-
############################################################################-
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
############################################################################-
from odoo import fields, models, _
from odoo.tools import html_escape, html_translate


class PortfolioProject(models.Model):
    """ Created a new class for portfolio project """
    _name = 'portfolio.project'
    _description = 'Portfolio Projects'
    _inherit = ['website.published.mixin', 'image.mixin']

    def _default_content(self):
        text = html_escape(_("Write your project details here"))
        return """
            <p>%(text)s</p>
        """ % {"text": text}

    name = fields.Char('Project Title', required=True, help="Name of the project")
    content = fields.Html('Content', default=_default_content, translate=html_translate, sanitize=False,
                          help="content")
    description = fields.Text('Description', help="Information regarding the portfolio project")
    tag_ids = fields.Many2many("portfolio.project.tag", string="Tags", help="Tags")

    def _compute_website_url(self):
        """ Inherited the function to generate website url """
        super()._compute_website_url()
        for project in self:
            if project.id:
                project.website_url = "/project/%s/" % self.env['ir.http']._slug(project)

    def action_open_form_view(self):
        """ Open form view of the record """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Portfolio Projects',
            'res_model': 'portfolio.project',
            'view_mode': 'form',
            'target': 'current',
            'res_id': self.id,
        }


class PortfolioProjectTag(models.Model):
    """ Created a new class for portfolio project tag """
    _name = 'portfolio.project.tag'

    name = fields.Char('Name', required=True, help="Name of the Tags")