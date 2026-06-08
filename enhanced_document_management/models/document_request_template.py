# -*- coding: utf-8 -*-
#############################################################################
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
#############################################################################
from odoo import api, fields, models


class DocumentRequestTemplate(models.Model):
    """Model representing document request templates."""
    _name = "document.request.template"
    _description = "Document Request Template"

    name = fields.Char(string="Template name",
                       required=True,
                       help="Name of the template.")
    user_ids = fields.Many2many('res.users', string="User",
                                help="Users who can use this template.",
                                compute="_compute_user_ids")
    company_id = fields.Many2one('res.company', string='Company',
                                 help='The company this template belongs to.', default=lambda self: self.env.company)
    manager_id = fields.Many2one("res.users", string="Managers",
                                 help="Manager responsible for this template.", required=True)
    stamp = fields.Image(string="Stamp", max_width=170, max_height=170,
                         help="Stamp displayed in the generated document.")
    template = fields.Html(string="Template", help="Template content for the document.")


    @api.depends('manager_id')
    def _compute_user_ids(self):
        """Compute users who belong to the view_all_document group."""
        group = self.env.ref('enhanced_document_management.view_all_document', raise_if_not_found=False)
        users = group.user_ids if group else self.env['res.users']
        for rec in self:
            rec.user_ids = users

    def action_preview_document(self):
        """Open the client-side document preview for the template.

        Returns:
            dict: Client action descriptor for the 'preview_document' OWL component.
        """
        self.ensure_one()
        stamp_value = self.stamp
        if isinstance(stamp_value, bytes):
            stamp_value = stamp_value.decode("utf-8")

        return {
            "type": "ir.actions.client",
            "tag": "preview_document",
            "params": {
                "body_html": self.template or "",
                "stamp": stamp_value or False,
            },
        }
