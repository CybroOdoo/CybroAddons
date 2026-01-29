# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import models, fields, api, _


class IrUiView(models.Model):
    _inherit = 'ir.ui.view'

    custom_id = fields.Char(string='Custom ID')


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    custom_id = fields.Char(string='Custom ID')


class IrActionsActWindow(models.Model):
    _inherit = 'ir.actions.act_window'

    custom_id = fields.Char(string='Custom ID')


class CustomReport(models.Model):
    _name = 'custom.report'
    _description = 'Custom Report'

    name = fields.Char(string='Name')
    model_id = fields.Many2one('ir.model', string='Model', required=True, domain="[('transient', '=', False),]",
                               ondelete='cascade')
    fields_ids = fields.One2many('custom.report.fields', 'report_id', string='Fields', required=True)
    menu_id = fields.Many2one('ir.ui.menu', string='Menu', required=True, ondelete='cascade',
                              help="The menu where you want to create a new menu item.")
    menu_group_id = fields.Many2many('res.groups', string='Menu Group', required=True, ondelete='cascade')
    view_type = fields.Selection([('pivot', 'Pivot'), ('graph', 'Graph')], string='View Type')

    def unlink(self):
        for rec in self:
            # Searching the view
            view = self.env['ir.ui.view'].search(
                [('custom_id', '=', str(rec.id) + '_' + rec.model_id.model + '_' + rec.menu_id.complete_name)])
            # search the action
            action = self.env['ir.actions.act_window'].search(
                [('custom_id', '=', str(rec.id) + '_' + 'pivot' + '_' + '_' + 'current',)])
            # search the menu
            menu = self.env['ir.ui.menu'].search(
                [('custom_id', '=', str(rec.id) + '_' + rec.menu_id.complete_name + '_' + rec.model_id.model)])
            view.sudo().unlink()
            action.sudo().unlink()
            menu.sudo().unlink()
        return super().unlink()

    @api.constrains('menu_id', 'fields_ids', 'model_id', 'name', 'menu_group_id')
    def _create_menu_id(self):
        view_id = self.env['ir.ui.view'].search(
            [('custom_id', '=', str(self.id) + '_' + self.model_id.model + '_' + self.menu_id.complete_name)])
        arch_base = '''<pivot string="%s" sample="1">\n''' % (self.name)
        for rec in self.fields_ids:
            if rec.row:
                arch_base += '''
                <field name="%s" type="row" string="%s"/>\n''' % (rec.custom_field_id.name, rec.label)
            elif rec.measure:
                arch_base += '''
                <field name="%s" type="measure" string="%s"/>\n''' % (rec.custom_field_id.name, rec.label)
            else:
                arch_base += '''<field name="%s" string="%s" />\n''' % (rec.custom_field_id.name, rec.label)

        arch_base += '''</pivot>\n'''
        view_value = {
            'name': _(self.name),
            'type': 'pivot',
            'custom_id': str(self.id) + '_' + self.model_id.model + '_' + self.menu_id.complete_name,
            'model': self.model_id.model,
            'mode': 'primary',
            'active': True,
            'arch_base': arch_base,
            'groups_id': [(6, 0, [self.menu_group_id.id])],
        }
        if not view_id:
            # Creating the view
            view_obj = self.env['ir.ui.view'].create(view_value)
        else:
            view_id.sudo().write(view_value)
            view_obj = view_id
        value = {
            'type': 'ir.actions.act_window',
            'name': _(self.name),
            'res_model': self.model_id.model,
            'custom_id': str(self.id) + '_' + 'pivot' + '_' + '_' + 'current',
            'view_mode': 'pivot',
            'view_id': view_obj.id,
            'target': 'current',
        }
        action_id = self.env['ir.actions.act_window'].search(
            [('custom_id', '=', str(self.id) + '_' + 'pivot' + '_' + '_' + 'current')])
        if not action_id:
            # Creating the action
            action = self.env['ir.actions.act_window'].create(value)
        else:
            action_id.sudo().write(value)
            action = action_id
        value = {
            'name': self.name,
            'complete_name': self.menu_id.complete_name + '/' + self.name,
            'action': 'ir.actions.act_window,%s' % (action.id),
            'parent_id': self.menu_id.id,
            'custom_id': str(self.id) + '_' + self.menu_id.complete_name + '_' + self.model_id.model,
            'groups_id': [(6, 0, [self.menu_group_id.id])],
        }
        menu_id = self.env['ir.ui.menu'].search(
            [('custom_id', '=', str(self.id) + '_' + self.menu_id.complete_name + '_' + self.model_id.model)])
        if not menu_id:
            # Creating the menu
            menu = self.env['ir.ui.menu'].create(value)
        else:
            menu_id.sudo().write(value)


class CustomReportFields(models.Model):
    _name = 'custom.report.fields'
    _description = 'Custom Report Fields'

    custom_field_id = fields.Many2one('ir.model.fields', string='Custom Report',
                                      required=True, ondelete='cascade')
    report_id = fields.Many2one('custom.report', string='Parent ', ondelete='cascade')
    label = fields.Char(string='Label')
    row = fields.Boolean(string='Row', default=0)
    measure = fields.Boolean(string='Mesure', default=0)
    measurable = fields.Boolean(string='Measurable', default=0)
    rowable = fields.Boolean(string='Row able', default=0)

    @api.onchange('custom_field_id')
    def onchange_custom_field_id(self):
        model_id = self.env.context.get('parent_id')
        self.label = self.custom_field_id.field_description
        self.report_id = model_id
        if self.custom_field_id.ttype in ['float', 'integer', 'many2one', 'monetary']:
            self.measurable = True
        if self.custom_field_id.ttype in ['many2many', 'one2many']:
            self.rowable = True
        return {'domain': {'custom_field_id': [('model_id.id', '=', model_id)]}}
