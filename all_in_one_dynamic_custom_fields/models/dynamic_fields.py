# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: MOHAMMED DILSHAD TK (odoo@cybrosys.com)
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
################################################################################
from odoo import api, fields, models, _


class DynamicFields(models.Model):
    """Creates dynamic fields model to create and manage new fields"""
    _name = 'dynamic.fields'
    _rec_name = 'field_description'
    _description = 'Custom Dynamic Fields'
    _inherit = 'ir.model.fields'

    @api.model
    def get_possible_field_types(self):
        """Return all available field types other than 'o2m' and
           'reference' fields."""
        field_list = sorted((key, key) for key in fields.MetaField.by_type)
        field_list.remove(('one2many', 'one2many'))
        field_list.remove(('reference', 'reference'))
        return field_list

    @api.onchange('model_id')
    def _onchange_model_id(self):
        """Pass selected model into model field to filter position fields,
            set values to form_view_ids to filter form view ids and pass
            values to tree_view_ids to filter tree view ids"""
        for rec in self:
            rec.model = rec.model_id.model
            rec.write({'form_view_ids': [(6, 0, rec.model_id.view_ids.filtered(
                lambda view: view.type == 'form' and view.mode == 'primary')
                                          .ids)]})
            rec.write({'tree_view_ids': [(6, 0, self.model_id.view_ids.filtered(
                lambda view: view.type == 'tree' and view.mode == 'primary')
                                          .ids)]})

    model = fields.Char(string='Model', help="To store selected model name")
    position_field_id = fields.Many2one(comodel_name='ir.model.fields',
                                        string='Field Name',
                                        required=True, ondelete='cascade',
                                        help="Position field for new field"
                                        , domain=lambda
            self: "[('model', '=', model)]")
    position = fields.Selection(selection=[('before', 'Before'),
                                           ('after', 'After')],
                                string='Position',
                                required=True, help="Position of new field")
    model_id = fields.Many2one(comodel_name='ir.model', string='Model',
                               required=True,
                               index=True, ondelete='cascade',
                               help="The model this field belongs to")
    ref_model_id = fields.Many2one(comodel_name='ir.model', string='Relational '
                                                                   'Model',
                                   index=True, help="Relational model"
                                                    " for relational fields")
    selection_field = fields.Char(string="Selection Options",
                                  help="The model this field belongs to")
    field_type = fields.Selection(selection='get_possible_field_types',
                                  string='Field Type', required=True,
                                  help="Data type of new field")
    ttype = fields.Selection(string="Field Type", related='field_type',
                             help="Field type of field")
    widget = fields.Many2one(comodel_name='dynamic.field.widgets',
                             string='Widget', help="Widgets for field",
                             domain=lambda self: "[('data_type', '=', "
                                                 "field_type)]")
    groups = fields.Many2many('res.groups',
                              'employee_dynamic_fields_group_rel',
                              'field_id', 'group_id',
                              help="Groups of field")
    extra_features = fields.Boolean(string="Show Extra Properties",
                                    help="Enable to add extra features")
    status = fields.Selection(selection=[('draft', 'Draft'), ('form',
                                                              'Field Created')],
                              string='Status',
                              index=True, readonly=True, tracking=True,
                              copy=False, default='draft',
                              required=True, help='State for record')
    form_view_ids = fields.Many2many(comodel_name='ir.ui.view',
                                     string="Form View IDs",
                                     help="Stores form view ids")
    tree_view_ids = fields.Many2many(comodel_name='ir.ui.view',
                                     relation="rel_tree_view",
                                     string="Tree View IDs",
                                     help="Stores tree view ids")
    form_view_id = fields.Many2one(comodel_name='ir.ui.view',
                                   string="Form View ID",
                                   required=True,
                                   help="Form view id of the model",
                                   domain=lambda self: "[('id', 'in', "
                                                       "form_view_ids)]")
    form_view_inherit_id = fields.Char(string="Form View Inherit Id",
                                       related='form_view_id.xml_id',
                                       help="Form view inherit id(adds"
                                            " by selecting form view id)")
    add_field_in_tree = fields.Boolean(string="Add Field to the Tree View",
                                       default=False,
                                       help="Enable to add field in tree view")
    tree_view_id = fields.Many2one(comodel_name='ir.ui.view',
                                   string="Tree View ID",
                                   help="Tree view id of the model",
                                   domain=lambda self: "[('id', 'in', "
                                                       "tree_view_ids)]")
    tree_view_inherit_id = fields.Char(string="Tree View Inherit Id",
                                       related='tree_view_id.xml_id',
                                       help="Tree view inherit id(adds"
                                            " by selecting tree view id)")

    def action_create_dynamic_field(self):
        """Function to create dynamic field to a particular model, data type,
           properties and etc"""
        self.write({'status': 'form'})
        if self.field_type == 'monetary' and not self.env[
            'ir.model.fields'].sudo().search([
            ('model', '=', self.model_id.id),
            ('name', '=', 'currency_id')]):
            self.env['ir.model.fields'].sudo().create({
                'name': 'x_currency_id',
                'field_description': 'Currency',
                'model_id': self.model_id.id,
                'ttype': 'many2one',
                'relation': 'res.currency',
                'is_dynamic_field': True
            })
        self.env['ir.model.fields'].sudo().create({
            'name': self.name,
            'field_description': self.field_description,
            'model_id': self.model_id.id,
            'ttype': self.field_type,
            'relation': self.ref_model_id.model,
            'required': self.required,
            'index': self.index,
            'store': self.store,
            'help': self.help,
            'readonly': self.readonly,
            'selection': self.selection_field,
            'copied': self.copied,
            'is_dynamic_field': True
        })
        inherit_form_view_name = str(
            self.form_view_id.name) + ".inherit.dynamic.custom." + str(self.
                                                   field_description) + ".field"
        xml_id = self.form_view_id.xml_id
        inherit_id = self.env.ref(xml_id)
        arch_base = _('<?xml version="1.0"?>'
                      '<data>'
                      '<field name="%s" position="%s">'
                      '<field name="%s"/>'
                      '</field>'
                      '</data>') % (self.position_field_id.name,
                                    self.position, self.name)
        if self.widget:
            arch_base = _('<?xml version="1.0"?>'
                          '<data>'
                          '<field name="%s" position="%s">'
                          '<field name="%s" widget="%s"/>'
                          '</field>'
                          '</data>') % (self.position_field_id.name,
                                        self.position, self.name,
                                        self.widget.name)
        self.form_view_id = self.env['ir.ui.view'].sudo().create({
            'name': inherit_form_view_name,
            'type': 'form',
            'model': self.model_id.model,
            'mode': 'extension',
            'inherit_id': inherit_id.id,
            'arch_base': arch_base,
            'active': True
        })
        self.action_create_to_tree_view()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def action_create_to_tree_view(self):
        """Function to add field to tree view"""
        if self.add_field_in_tree:
            inherit_tree_view_name = str(
                self.tree_view_id.name) + ".inherit.dynamic.custom" + \
                                     str(self.field_description) + ".field"
            self.tree_view_id = self.env['ir.ui.view'].sudo().create({
                'name': inherit_tree_view_name,
                'type': 'tree',
                'model': self.model_id.model,
                'mode': 'extension',
                'inherit_id': self.tree_view_id.id,
                'arch_base': _(
                    '<?xml version="1.0"?>'
                    '<data>'
                    '''<xpath expr="//tree" position="inside">'''
                    '''<field name="%s" optional="show"/>'''
                    '''</xpath>'''
                    '''</data>''') % self.name,
                'active': True})
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }

    def unlink(self):
        """Super unlink function"""
        if self.form_view_id:
            self.form_view_id.active = False
        if self.tree_view_id:
            self.tree_view_id.active = False
        res = super(DynamicFields, self).unlink()
        return res
