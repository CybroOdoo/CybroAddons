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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
import xml.sax.saxutils
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class CustomReport(models.Model):
    """Custom report model for creating pivot view and adding required
        fields for the model"""
    _name = 'custom.report'
    _description = 'Custom Report'

    name = fields.Char(string='Name', required=True, help="Name of the pivot report")
    model_id = fields.Many2one('ir.model', string='Model',
                               required=True,
                               domain="[('transient', '=', False),]",
                               ondelete='cascade',
                               help="Select the model for the report")
    fields_ids = fields.One2many('custom.report.fields',
                                 'report_id', string='Fields',
                                 help="Select the fields added to the custom report.")
    menu_id = fields.Many2one('ir.ui.menu', string='Menu',
                              required=True, ondelete='cascade',
                              help="The parent menu where the report menu item will be created.")
    menu_group_ids = fields.Many2many('res.groups',
                                      string='Menu Groups', required=True,
                                      help="Select the user groups who have access to the report menu")

    @api.constrains('fields_ids')
    def _check_fields_ids(self):
        """Ensure that at least one field is configured for the report."""
        for rec in self:
            if not rec.fields_ids:
                raise ValidationError("Please configure at least one field for the custom report.")

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            rec._sync_ui_components()
        return records

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            rec._sync_ui_components()
        return res

    def unlink(self):
        """Customized unlink method to clean up related records."""
        for rec in self:
            # Search associated views, actions, and menus by stable custom_report key
            tag = f"custom_report_{rec.id}"
            views = self.env['ir.ui.view'].search([('custom_report', '=', tag)])
            actions = self.env['ir.actions.act_window'].search([('custom_report', '=', tag)])
            menus = self.env['ir.ui.menu'].search([('custom_report', '=', tag)])
            views.sudo().unlink()
            actions.sudo().unlink()
            menus.sudo().unlink()
        return super().unlink()

    def _sync_ui_components(self):
        """Create or update the ir.ui.view, ir.actions.act_window, and ir.ui.menu."""
        for rec in self:
            if not rec.name or not rec.model_id or not rec.menu_id:
                continue

            tag = f"custom_report_{rec.id}"
            escaped_report_name = xml.sax.saxutils.quoteattr(rec.name or '')
            arch_base = f'<pivot string={escaped_report_name} sample="1">\n'

            for field in rec.fields_ids:
                if not field.custom_field_id:
                    continue
                field_name = xml.sax.saxutils.quoteattr(field.custom_field_id.name or '')
                label_val = xml.sax.saxutils.quoteattr(field.label or field.custom_field_id.field_description or '')
                if field.row:
                    arch_base += f'    <field name={field_name} type="row" string={label_val}/>\n'
                elif field.measure:
                    arch_base += f'    <field name={field_name} type="measure" string={label_val}/>\n'
                else:
                    arch_base += f'    <field name={field_name} string={label_val}/>\n'

            arch_base += '</pivot>\n'

            # 1. ir.ui.view
            view_vals = {
                'name': rec.name,
                'type': 'pivot',
                'custom_report': tag,
                'model': rec.model_id.model,
                'mode': 'primary',
                'active': True,
                'arch_base': arch_base,
                'group_ids': [(6, 0, rec.menu_group_ids.ids)],
            }
            view = self.env['ir.ui.view'].search([('custom_report', '=', tag)], limit=1)
            if not view:
                view = self.env['ir.ui.view'].create(view_vals)
            else:
                view.sudo().write(view_vals)

            # 2. ir.actions.act_window
            action_vals = {
                'type': 'ir.actions.act_window',
                'name': rec.name,
                'res_model': rec.model_id.model,
                'custom_report': tag,
                'view_mode': 'pivot',
                'view_id': view.id,
                'target': 'current',
            }
            action = self.env['ir.actions.act_window'].search([('custom_report', '=', tag)], limit=1)
            if not action:
                action = self.env['ir.actions.act_window'].create(action_vals)
            else:
                action.sudo().write(action_vals)

            # 3. ir.ui.menu
            complete_name = f"{rec.menu_id.complete_name}/{rec.name}" if rec.menu_id.complete_name else rec.name
            menu_vals = {
                'name': rec.name,
                'complete_name': complete_name,
                'action': f'ir.actions.act_window,{action.id}',
                'parent_id': rec.menu_id.id,
                'custom_report': tag,
                'group_ids': [(6, 0, rec.menu_group_ids.ids)],
            }
            menu = self.env['ir.ui.menu'].search([('custom_report', '=', tag)], limit=1)
            if not menu:
                self.env['ir.ui.menu'].create(menu_vals)
            else:
                menu.sudo().write(menu_vals)

    def _create_menu_id(self):
        """Deprecated alias maintained for backward compatibility."""
        self._sync_ui_components()
