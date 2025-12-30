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
from odoo import api, fields, models


class DocumentRequestTemplate(models.Model):
    """Model representing document request templates."""
    _name = "document.request.template"
    _description = "Document request template"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Template name",
                       required=True,
                       help="name of template")
    user_ids = fields.Many2many('res.users', string="User", help="Choose User",
                                compute='_get_managers')
    company_id = fields.Many2one('res.company', string='Company',
                                 help='choose company',default=lambda self: self.env.company)
    manager_id = fields.Many2one("res.users", string="Managers",
                                 help="Choose Manager", required=True)
    stamp = fields.Image(string="Stamp", max_width=170, max_height=170,
                         help="Add your stamp")
    template = fields.Html(string="Template", help="Add the template here")

    @api.depends('name')
    def _get_managers(self):
        """function to get user's with document request template
        manager group"""
        self.user_ids = self.manager_id.search([]).filtered(
            lambda managers: managers.has_group(
                'enhanced_document_management.view_all_document'))
