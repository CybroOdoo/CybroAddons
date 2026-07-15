# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Arjun S (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU AFFERO GENERAL PUBLIC LICENSE (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from ast import literal_eval
from odoo import api, fields, models
from odoo.osv import expression


class DashboardBlock(models.Model):
    """Class is used to create charts and tiles in dashboard"""
    _name = "dashboard.block"
    _description = "Dashboard Block"

    def get_default_action(self):
        """Return the ID of the dashboard action if available, else False."""
        action = self.env.ref(
            'odoo_dynamic_dashboard.dashboard_view_action',
            raise_if_not_found=False
        )
        return action.id if action else False

    name = fields.Char(string="Name", help='Name of the block')
    fa_icon = fields.Char(string="Icon", help="Add icon for tile")
    operation = fields.Selection(
        selection=[("sum", "Sum"), ("avg", "Average"), ("count", "Count")],
        string="Operation",
        help='Tile Operation that needs to bring values for tile',
        required=True)
    graph_type = fields.Selection(
        selection=[("bar", "Bar"), ("radar", "Radar"), ("pie", "Pie"),
                   ("polarArea", "polarArea"), ("line", "Line"),
                   ("doughnut", "Doughnut")],
        string="Chart Type", help='Type of Chart')
    measured_field_id = fields.Many2one("ir.model.fields",
                                        string="Measured Field",
                                        help="Select the Measured")
    client_action_id = fields.Many2one('ir.actions.client',
                                       string="Client action",
                                       default=get_default_action,
                                       help="Client action")
    type = fields.Selection(
        selection=[("graph", "Chart"), ("tile", "Tile")],
        string="Type", help='Type of Block ie, Chart or Tile')
    x_axis = fields.Char(string="X-Axis", help="Chart X-axis")
    y_axis = fields.Char(string="Y-Axis", help="Chart Y-axis")
    height = fields.Char(string="Height ", help="Height of the block")
    width = fields.Char(string="Width", help="Width of the block")
    translate_x = fields.Char(string="Translate_X",
                              help="x value for the style transform translate")
    translate_y = fields.Char(string="Translate_Y",
                              help="y value for the style transform translate")
    data_x = fields.Char(string="Data_X", help="Data x value for resize")
    data_y = fields.Char(string="Data_Y", help="Data y value for resize")
    group_by_id = fields.Many2one("ir.model.fields",
                                  string="Group by(Y-Axis)",
                                  help='Field value for Y-Axis')
    tile_color = fields.Char(string="Tile Color", help='Primary Color of Tile')
    text_color = fields.Char(string="Text Color", help='Text Color of Tile')
    val_color = fields.Char(string="Value Color", help='Value Color of Tile')
    fa_color = fields.Char(string="Icon Color", help='Icon Color of Tile')
    filter = fields.Char(string="Filter", help="Add filter")
    model_id = fields.Many2one('ir.model', string='Model',
                               help="Select the module name")
    model_name = fields.Char(related='model_id.model', string="Model Name",
                             help="Added model_id model")
    edit_mode = fields.Boolean(string="Edit Mode",
                               help="Enable to edit chart and tile", )

    @api.onchange('model_id')
    def _onchange_model_id(self):
        if self.operation or self.measured_field_id:
            self.update({
                'operation': False,
                'measured_field_id': False,
                'group_by_id': False,
            })

    def get_dashboard_vals(self, action_id, start_date=None, end_date=None):
        """Fetch dashboard block values efficiently for chart rendering"""
        block = self.env['dashboard.block'].sudo()
        blocks = block.search([('client_action_id', '=', int(action_id))])
        block_data = []
        for rec in blocks:
            filters = literal_eval(rec.filter or "[]")
            filters = [f for f in filters if
                       not (isinstance(f, tuple) and f[0] == 'create_date')]
            rec.filter = repr(filters)
            color = rec.tile_color or '#1f6abb'
            vals = {
                'id': rec.id,
                'name': rec.name,
                'type': rec.type,
                'graph_type': rec.graph_type,
                'icon': rec.fa_icon,
                'model_name': rec.model_name,
                'color': f'background-color: {color};',
                'text_color': f'color: {rec.text_color or "#FFFFFF"};',
                'val_color': f'color: {rec.val_color or "#FFFFFF"};',
                'icon_color': f'color: {color};',
                'height': rec.height,
                'width': rec.width,
                'translate_x': rec.translate_x,
                'translate_y': rec.translate_y,
                'data_x': rec.data_x,
                'data_y': rec.data_y,
                'x_label': rec.measured_field_id.field_description,
                'y_label': rec.group_by_id.field_description,
                'domain': filters,
            }
            domain = expression.AND([filters]) if filters else []
            if not rec.model_name:
                block_data.append(vals)
                continue
            model = self.env[rec.model_name]
            query = model.get_query(domain, rec.operation,
                                    rec.measured_field_id,
                                    start_date, end_date,
                                    group_by=rec.group_by_id if rec.type == 'graph' else False)
            self._cr.execute(query)
            records = self._cr.dictfetchall()
            if not records:
                block_data.append(vals)
                continue
            if rec.type == 'graph':
                x_field = rec.group_by_id.name if rec.group_by_id else None
                x_axis = []
                y_axis = []
                for record in records:
                    name = record.get(x_field)
                    if isinstance(name, dict):
                        name = name.get(self._context.get('lang') or 'en_US',
                                        '')
                    x_axis.append(name)
                    y_axis.append(record.get('value', 0))
                vals.update({'x_axis': x_axis, 'y_axis': y_axis})
            else:
                total = records[0].get('value', 0) or 0
                magnitude = 0
                while abs(total) >= 1000:
                    magnitude += 1
                    total /= 1000.0
                formatted_val = f"{total:.2f}{['', 'K', 'M', 'G', 'T', 'P'][magnitude]}"
                vals['value'] = formatted_val
            block_data.append(vals)
        return block_data

    def get_save_layout(self, grid_data_list):
        """Persist updated layout values for dashboard blocks efficiently."""
        for data in grid_data_list:
            block = self.browse(int(data['id']))
            vals = {}
            if 'data-x' in data and 'data-y' in data:
                vals.update({
                    'translate_x': f"{data['data-x']}px",
                    'translate_y': f"{data['data-y']}px",
                    'data_x': data['data-x'],
                    'data_y': data['data-y'],
                })
            if 'height' in data and 'width' in data:
                vals.update({
                    'height': f"{data['height']}px",
                    'width': f"{data['width']}px",
                })
            if vals:
                block.write(vals)
        return True
