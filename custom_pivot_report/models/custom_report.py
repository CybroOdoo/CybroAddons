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
from odoo import api, fields, models, _


class CustomReport(models.Model):
    """Custom report model for creating pivot view and adding required
        fields for the model"""
    _name = 'custom.report'
    _description = 'Custom Report'

    name = fields.Char(string='Name', help="Name of the pivot report")
    model_id = fields.Many2one('ir.model', string='Model',
                               required=True,
                               domain="[('transient', '=', False),]",
                               ondelete='cascade',
                               help="Select the model for the report")
    fields_ids = fields.One2many('custom.report.fields',
                                 'report_id', string='Fields',
                                 required=True,
                                 help="Select the field that is added to the custom report.")
    menu_id = fields.Many2one('ir.ui.menu', string='Menu',
                              required=True, ondelete='cascade',
                              help="The menu where you want to create a new menu item.")
    menu_group_id = fields.Many2many('res.groups',
                                     string='Menu Group', required=True,
                                     ondelete='cascade',
                                     help="Set the user group who hav access to the report menu")
    view_type = fields.Selection([('pivot', 'Pivot'),
                                  ('graph', 'Graph')], string='View Type',
                                 help="Select the type of report")

    def unlink(self):
        """Customized unlink method to clean up related records."""
        for rec in self:
            # Searching the view
            view = self.env['ir.ui.view'].search(
                [('custom_report', '=', str(rec.id) + '_' + rec.model_id.model + '_' + rec.menu_id.complete_name)])
            # search the action
            action = self.env['ir.actions.act_window'].search(
                [('custom_report', '=', str(rec.id) + '_' + 'pivot' + '_' + '_' + 'current',)])
            # search the menu
            menu = self.env['ir.ui.menu'].search(
                [('custom_report', '=', str(rec.id) + '_' + rec.menu_id.complete_name + '_' + rec.model_id.model)])
            view.sudo().unlink()
            action.sudo().unlink()
            menu.sudo().unlink()
        return super().unlink()

    @api.constrains('menu_id', 'fields_ids', 'model_id', 'name', 'menu_group_id')
    def _create_menu_id(self):
        for rec in self:

            view_id = self.env['ir.ui.view'].search([
                ('custom_report', '=', f"{rec.id}_{rec.model_id.model}_{rec.menu_id.complete_name}")
            ])

            arch_base = f'<pivot string="{rec.name}" sample="1">\n'

            for field in rec.fields_ids:
                if field.row:
                    arch_base += f'<field name="{field.custom_field_id.name}" type="row" string="{field.label}"/>\n'
                elif field.measure:
                    arch_base += f'<field name="{field.custom_field_id.name}" type="measure" string="{field.label}"/>\n'
                else:
                    arch_base += f'<field name="{field.custom_field_id.name}" string="{field.label}" />\n'

            arch_base += '</pivot>\n'

            view_value = {
                'name': _(rec.name),
                'type': 'pivot',
                'custom_report': f"{rec.id}_{rec.model_id.model}_{rec.menu_id.complete_name}",
                'model': rec.model_id.model,
                'mode': 'primary',
                'active': True,
                'arch_base': arch_base,
                'group_ids': [(6, 0, rec.menu_group_id.ids)],
            }

            if not view_id:
                view_obj = self.env['ir.ui.view'].create(view_value)
            else:
                view_id.sudo().write(view_value)
                view_obj = view_id

            action_vals = {
                'type': 'ir.actions.act_window',
                'name': _(rec.name),
                'res_model': rec.model_id.model,
                'custom_report': f"{rec.id}_pivot__current",
                'view_mode': 'pivot',
                'view_id': view_obj.id,
                'target': 'current',
            }

            action_id = self.env['ir.actions.act_window'].search([
                ('custom_report', '=', f"{rec.id}_pivot__current")
            ])

            if not action_id:
                action = self.env['ir.actions.act_window'].create(action_vals)
            else:
                action_id.sudo().write(action_vals)
                action = action_id

            menu_vals = {
                'name': rec.name,
                'complete_name': rec.menu_id.complete_name + '/' + rec.name,
                'action': f'ir.actions.act_window,{action.id}',
                'parent_id': rec.menu_id.id,
                'custom_report': f"{rec.id}_{rec.menu_id.complete_name}_{rec.model_id.model}",
                'group_ids': [(6, 0, rec.menu_group_id.ids)],
            }

            menu_id = self.env['ir.ui.menu'].search([
                ('custom_report', '=', f"{rec.id}_{rec.menu_id.complete_name}_{rec.model_id.model}")
            ])

            if not menu_id:
                self.env['ir.ui.menu'].create(menu_vals)
            else:
                menu_id.sudo().write(menu_vals)
