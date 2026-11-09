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
"""Project dynamic fields wizard model."""
import re
import xml.etree.ElementTree as xee

from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError


class ProjectDynamicFields(models.TransientModel):
    """Creating new transient model for the dynamic fields wizard."""
    # pylint: disable=protected-access
    _name = 'project.dynamic.fields'
    _description = 'Project Dynamic Fields'

    name = fields.Char(
        string="Field Name",
        required=True,
        help="Technical name of the field (e.g. x_field_name).",
    )
    field_description = fields.Char(
        string="Field Label",
        required=True,
        help="Label shown in the user interface.",
    )
    state = fields.Selection(
        [('manual', 'Custom Field'), ('base', 'Base Field')],
        string="Type",
        default='manual',
    )
    required = fields.Boolean()
    readonly = fields.Boolean()
    index = fields.Boolean(string="Indexed")
    store = fields.Boolean(string="Stored", default=True)
    copied = fields.Boolean(default=True)
    help = fields.Text()

    fields_types = [
        'char', 'text', 'integer', 'float', 'boolean', 'selection',
        'many2one', 'one2many', 'many2many', 'date', 'datetime', 'binary',
        'html', 'monetary',
    ]

    form_view_id = fields.Many2one(
        'ir.ui.view',
        string="Form View ID",
        help="Select the view to be used as the form view for this field.",
    )
    position_field_id = fields.Many2one(
        'ir.model.fields',
        string='Existing Field Name',
        domain=lambda self: self.set_domain(),
        required=True,
        help="Select the field that determines position of custom field.",
    )
    position = fields.Selection(
        [('before', 'Before'), ('after', 'After')],
        required=True,
        help="Position of field",
    )
    model_id = fields.Many2one(
        'ir.model',
        required=True,
        index=True,
        ondelete='cascade',
        help="The model this field belongs to",
        domain=lambda self: self._set_default(),
    )
    ref_model_id = fields.Many2one(
        'ir.model',
        string='Reference Model',
        index=True,
        help="Model that the dynamic field will be associated with.",
    )
    selection_field = fields.Char(
        string="Selection",
        help='Enter selection value',
    )
    rel_field_id = fields.Many2one(
        'ir.model.fields',
        string='linked Related Field',
        help='Related field.',
    )
    field_type = fields.Selection(
        selection='get_possible_field_types',
        required=True,
        help='The type of field that will be created for dynamic field.',
    )
    ttype = fields.Char(
        string='Technical Field Type',
        compute='_compute_ttype',
        store=False,
        help="Technical field type used when creating dynamic field.",
    )
    widget_id_domain = fields.Json(
        string='Widget Domain',
        compute='_compute_widget_id_domain',
        help="Technical domain for filtering widgets based on field type.",
    )
    widget_id = fields.Many2one(
        'project.field.widgets',
        domain="widget_id_domain",
        help='Select widget',
    )
    groups = fields.Many2many(
        'res.groups',
        'project_dynamic_fields_m2m_group_rel',
        'field_ids',
        'group_ids',
        help='The security groups that have access to dynamic field.',
    )
    extra_features = fields.Boolean(
        string="Show Extra Properties",
        help="Whether to display extra properties for dynamic field.",
    )

    @api.depends('field_type')
    def _compute_ttype(self):
        for rec in self:
            rec.ttype = rec.field_type

    @api.depends('field_type')
    def _compute_widget_id_domain(self):
        """Compute widget domain based on selected field type."""
        for rec in self:
            domain = [('id', '=', False)]
            if rec.field_type:
                if rec.field_type == 'binary':
                    domain = [('name', '=', 'image')]
                elif rec.field_type == 'many2many':
                    domain = [('name', 'in', ['many2many_tags', 'binary'])]
                elif rec.field_type == 'selection':
                    domain = [('name', 'in', ['radio', 'priority'])]
                elif rec.field_type == 'float':
                    domain = [('name', '=', 'monetary')]
                elif rec.field_type == 'many2one':
                    domain = [('name', '=', 'selection')]
            rec.widget_id_domain = domain

    @api.model
    def get_possible_field_types(self):
        """Return all available field types other than excluded fields."""
        field_list = sorted((f, f) for f in self.fields_types)
        excluded_types = {
            'one2many', 'reference', 'properties', 'properties_definition',
        }
        return [f for f in field_list if f[0] not in excluded_types]

    def set_domain(self):
        """Return the fields currently present in the project form."""
        view_id = self.env.ref('project.edit_project')
        view_arch = str(view_id.arch_base)
        doc = xee.fromstring(view_arch)
        field_list = [
            tag.attrib['name']
            for tag in doc.findall('.//field')
            if 'name' in tag.attrib
        ]
        model_id = self.env['ir.model'].sudo().search(
            [('model', '=', 'project.project')], limit=1
        )
        return [
            ('model_id', '=', model_id.id),
            ('state', '=', 'base'),
            ('name', 'in', field_list),
        ]

    def _set_default(self):
        """Return the default project.project model domain."""
        model_id = self.env['ir.model'].sudo().search(
            [('model', '=', 'project.project')], limit=1
        )
        return [('id', '=', model_id.id)]

    @api.onchange('field_type')
    def _onchange_field_type(self):
        """Reset widget_id when field type changes."""
        self.widget_id = False

    def action_create_fields(self):
        """Creates a new custom field for project.project and extends form."""
        if not self.env.user.has_group(
            'project_dynamic_fields.group_add_project_custom_fields'
        ):
            raise AccessError(
                self.env._(
                    "You do not have permission to create custom dynamic "
                    "fields."
                )
            )
        wizard = self.sudo()
        if not self.name.startswith('x_'):
            self.name = f'x_{self.name}'
        if not re.match(r'^[a-zA-Z0-9_]+$', self.name):
            raise ValidationError(
                self.env._("The field name contains invalid characters.")
            )
        if not re.match(r'^[a-zA-Z0-9_]+$', wizard.position_field_id.name):
            raise ValidationError(
                self.env._(
                    "The position field name contains invalid characters."
                )
            )
        if self.position not in ('before', 'after'):
            raise ValidationError(
                self.env._("Invalid field position.")
            )
        if self.widget_id:
            if not re.match(r'^[a-zA-Z0-9_]+$', wizard.widget_id.name):
                raise ValidationError(
                    self.env._("The widget name contains invalid characters.")
                )
            widget_attr = f' widget="{wizard.widget_id.name}"'
        else:
            widget_attr = ''

        field_vals = {
            'name': self.name,
            'field_description': self.field_description,
            'model_id': wizard.model_id.id,
            'ttype': self.field_type,
            'relation': wizard.ref_model_id.model if wizard.ref_model_id else False,
            'required': self.required,
            'index': self.index,
            'store': self.store,
            'help': self.help,
            'readonly': self.readonly,
            'selection': self.selection_field,
            'copied': self.copied,
            'is_project_dynamic': True,
        }
        if self.groups:
            field_vals['groups'] = [fields.Command.set(self.groups.ids)]

        field = self.env['ir.model.fields'].sudo().create(field_vals)
        inherit_id = self.env.ref('project.edit_project').sudo()
        arch_base = (
            '<?xml version="1.0"?>\n'
            '<data>\n'
            f'    <field name="{wizard.position_field_id.name}" '
            f'position="{self.position}">\n'
            f'        <field name="{self.name}"{widget_attr}/>\n'
            '    </field>\n'
            '</data>'
        )
        view = self.env['ir.ui.view'].sudo().create({
            'name': f'project.dynamic.field.{self.name}',
            'type': 'form',
            'model': 'project.project',
            'mode': 'extension',
            'inherit_id': inherit_id.id,
            'arch_base': arch_base,
            'active': True,
        })
        field.dynamic_form_view_id = view.id
        self.form_view_id = view.id
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
