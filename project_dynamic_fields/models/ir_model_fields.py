# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
"""Inherit ir.model.fields to track dynamic project fields."""
from odoo import fields, models


class IrModelFields(models.Model):
    """Adding a new field to understand the dynamically created fields."""
    # pylint: disable=too-few-public-methods
    _inherit = 'ir.model.fields'

    is_project_dynamic = fields.Boolean(
        string="Dynamic Field",
        help="Flag to indicate whether this field is dynamically created or "
             "not.",
    )
    dynamic_form_view_id = fields.Many2one(
        'ir.ui.view',
        ondelete='set null',
        help="Extension view associated with this dynamic field.",
    )

    def unlink(self):
        """Deactivate extension views when project dynamic fields are deleted."""
        if not self:
            return True
        self.check_access('unlink')
        for field in self.filtered('is_project_dynamic'):
            if field.dynamic_form_view_id and field.dynamic_form_view_id.exists():
                field.dynamic_form_view_id.sudo().write({'active': False})
            else:
                inherit_view = self.env.ref(
                    'project.edit_project', raise_if_not_found=False
                )
                domain = [
                    ('model', '=', 'project.project'),
                    ('mode', '=', 'extension'),
                    ('name', 'in', [
                        f'project.dynamic.field.{field.name}',
                        'project.dynamic.fields',
                    ]),
                ]
                if inherit_view:
                    domain.append(('inherit_id', '=', inherit_view.id))
                views = self.env['ir.ui.view'].sudo().search(domain)
                views_with_field = views.filtered(
                    lambda v, fname=field.name: fname in (v.arch_db or '')
                )
                if views_with_field:
                    views_with_field.sudo().write({'active': False})
        return super(IrModelFields, self.sudo()).unlink()
