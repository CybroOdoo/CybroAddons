# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.info)
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
###############################################################################
from ast import literal_eval
from odoo import api, fields, models
from odoo.exceptions import AccessError
from odoo.fields import Domain
from odoo.addons.web.icons import ICONS

# Odoo 20 dropped the FontAwesome stylesheet, so tiles saved with a
# "fa fa-*" class are mapped to the Material Symbols name rendered by
# <i class="oi" data-icon="..."/>. Names that only differ by "-" vs "_"
# (bar-chart, shopping-cart ...) need no entry here.
FA_TO_MATERIAL = {
    'area-chart': 'area_chart',
    'line-chart': 'show_chart',
    'pie-chart': 'pie_chart',
    'money': 'payments',
    'usd': 'attach_money',
    'dollar': 'attach_money',
    'eur': 'euro',
    'euro': 'euro',
    'user': 'person',
    'users': 'group',
    'truck': 'local_shipping',
    'cart-plus': 'add_shopping_cart',
    'file': 'description',
    'file-text': 'description',
    'file-text-o': 'description',
    'envelope': 'mail',
    'envelope-o': 'mail',
    'phone': 'phone',
    'calendar': 'calendar_today',
    'clock-o': 'schedule',
    'building': 'business',
    'cubes': 'inventory_2',
    'cube': 'inventory_2',
    'tasks': 'checklist',
    'check': 'check_circle',
    'star': 'star',
    'heart': 'favorite',
    'cog': 'settings',
    'gear': 'settings',
    'bank': 'account_balance',
    'university': 'account_balance',
    'credit-card': 'credit_card',
    'tag': 'sell',
    'tags': 'sell',
    'shopping-bag': 'shopping_bag',
    'handshake-o': 'handshake',
}
DEFAULT_ICON = 'bar_chart'


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
    fa_icon = fields.Char(
        string="Icon", default=DEFAULT_ICON,
        help="Material Symbols icon name for the tile, e.g. bar_chart, "
             "shopping_cart, payments (see fonts.google.com/icons)")
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

    def _group_labels(self, group_by, raw_values):
        """Turn the raw grouped column values into chart labels.

        A many2one group-by aggregates on the foreign key, so the ids are
        resolved to display names here; a translated column comes back as its
        jsonb value and is read in the user's language.
        """
        if group_by.ttype == 'many2one' and group_by.relation:
            comodel = self.env[group_by.relation]
            names = {
                record.id: record.display_name
                for record in comodel.browse(
                    [value for value in raw_values if value]).exists()
            }
            return [names.get(value, '') for value in raw_values]
        lang = self.env.context.get('lang') or 'en_US'
        return [
            value.get(lang, '') if isinstance(value, dict) else value
            for value in raw_values
        ]

    def _has_dashboard_access(self, action_id):
        """Whether the current user is allowed to see the dashboard of
        ``action_id``.

        ``get_dashboard_vals`` is reachable over RPC with any action id, so the
        group restrictions of the dashboard's menu are checked here instead of
        assuming the user reached it by clicking that menu.
        """
        menus = self.env['ir.ui.menu'].sudo().search(
            [('action', '=', f'ir.actions.client,{int(action_id)}')])
        return bool(menus._filter_visible_menus())

    def _get_icon_name(self):
        """Return the Material Symbols name to render for the tile icon,
        converting legacy FontAwesome classes ("fa fa-bar-chart")"""
        self.ensure_one()
        icon = (self.fa_icon or '').strip()
        if icon.startswith('fa') or ' ' in icon:
            icon = next((cls[3:] for cls in icon.split()
                         if cls.startswith('fa-')), '')
            icon = FA_TO_MATERIAL.get(icon, icon.replace('-', '_'))
        return icon if icon in ICONS else DEFAULT_ICON

    def get_dashboard_vals(self, action_id, start_date=None, end_date=None):
        """Fetch dashboard block values efficiently for chart rendering"""
        if not self._has_dashboard_access(action_id):
            return []
        blocks = self.env['dashboard.block'].search(
            [('client_action_id', '=', int(action_id))])
        block_data = []
        for rec in blocks:
            # The date range is passed separately, so a create_date leaf left
            # over in a saved filter would fight with it. Leaves come back as
            # lists from the domain widget and as tuples from literal_eval.
            filters = [
                leaf for leaf in literal_eval(rec.filter or "[]")
                if not (isinstance(leaf, (list, tuple)) and leaf
                        and leaf[0] == 'create_date')
            ]
            color = rec.tile_color or '#1f6abb'
            vals = {
                'id': rec.id,
                'name': rec.name,
                'type': rec.type,
                'graph_type': rec.graph_type,
                'icon': rec._get_icon_name(),
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
                # Seeded here rather than only on the success path: a block
                # whose model is gone, unreadable, or simply matches no record
                # is still sent to the client, and the chart component reads
                # these unconditionally.
                'x_axis': [],
                'y_axis': [],
                'domain': filters,
            }
            domain = Domain(filters)
            model = self.env.get(rec.model_name) if rec.model_name else None
            if model is None:
                # No model set, or the model's module has been uninstalled.
                block_data.append(vals)
                continue
            try:
                query = model.get_query(domain, rec.operation,
                                        rec.measured_field_id,
                                        start_date, end_date,
                                        group_by=rec.group_by_id if rec.type == 'graph' else False)
            except AccessError:
                # The user cannot read this block's model: render the block
                # without a value rather than breaking the whole dashboard.
                block_data.append(vals)
                continue
            self.env.cr.execute(query)
            records = self.env.cr.dictfetchall()
            if not records:
                block_data.append(vals)
                continue
            if rec.type == 'graph':
                x_field = rec.group_by_id.name if rec.group_by_id else None
                raw_values = [record.get(x_field) for record in records]
                vals.update({
                    'x_axis': self._group_labels(rec.group_by_id, raw_values),
                    'y_axis': [record.get('value', 0) for record in records],
                })
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
