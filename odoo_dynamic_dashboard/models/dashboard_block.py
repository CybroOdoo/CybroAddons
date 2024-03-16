# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import models, fields, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
from ast import literal_eval


class DashboardBlock(models.Model):
    """Creates the model Dashboard Blocks"""
    _name = "dashboard.block"
    _description = "Dashboard Blocks"

    def get_default_action(self):
        """This is the method get_default_action which will return the default
        action id."""
        action_id = self.env.ref(
            'odoo_dynamic_dashboard.dynamic_dashboard_action')
        if action_id:
            return action_id.id
        return False

    name = fields.Char(string="Name", help='Name of the block')
    field_id = fields.Many2one('ir.model.fields', string='Measured Field',
                               domain="[('store', '=', True), ('model_id', '=', model_id), ('ttype', 'in', ['float','integer','monetary'])]",
                               help='Measured field for the block')
    fa_icon = fields.Char(string="Icon", help='Icon for the block')
    graph_size = fields.Selection(
        selection=[("col-lg-4", "Small"), ("col-lg-6", "Medium"),
                   ("col-lg-12", "Large")],
        string="Graph Size", default='col-lg-4', help="Size of the graph")
    operation = fields.Selection(
        selection=[("sum", "Sum"), ("avg", "Average"), ("count", "Count")],
        string="Operation",
        help='Tile Operation that needs to bring values for tile')
    graph_type = fields.Selection(
        selection=[("bar", "Bar"), ("radar", "Radar"), ("pie", "Pie"),
                   ("line", "Line"), ("doughnut", "Doughnut")],
        string="Chart Type", help='Type of Chart')
    measured_field = fields.Many2one("ir.model.fields", string="Measured Field",
                                     help='Measure field for the chart')
    client_action = fields.Many2one('ir.actions.client',
                                    default=get_default_action,
                                    string="Client Action",
                                    help='Client Action for the dashboard '
                                         'block')
    type = fields.Selection(
        selection=[("graph", "Chart"), ("tile", "Tile")], string="Type",
        help='Type of Block ie, Chart or Tile')
    x_axis = fields.Char(string="X-Axis", help="X-axis for the chart")
    y_axis = fields.Char(string="Y-Axis", help="Y-axis for the chart")
    group_by = fields.Many2one("ir.model.fields", store=True,
                               string="Group by(Y-Axis)",
                               help='Field value for Y-Axis',
                               domain="[('store', '=', True)]")
    tile_color = fields.Char(string="Tile Color", help='Primary Color of Tile')
    text_color = fields.Char(string="Text Color", help='Text Color of Tile')
    fa_color = fields.Char(string="Icon Color", help='Icon Color of Tile')
    filter = fields.Char(string="Filter", help='Filter for Tile')
    model_id = fields.Many2one('ir.model', string='Model',
                               help='Model for Tile')
    model_name = fields.Char(related='model_id.model', readonly=True,
                             string="Model Name", help='Model Name of Tile')
    filter_by = fields.Many2one("ir.model.fields", string=" Filter By",
                                help="Filter By for Tile")
    filter_values = fields.Char(string="Filter Values",
                                help="Filter Values for tiles accordingly")
    sequence = fields.Integer(string="Sequence",
                              help="sequence of the dashboard")
    edit_mode = fields.Boolean(default=False, invisible=True,
                               string="Edit Mode", help="Edit mode of the tile")

    def get_dashboard_vals(self, action_id):
        """Dashboard block values"""
        block_id = []
        for rec in self.env['dashboard.block'].sudo().search(
                [('client_action', '=', int(action_id))]):
            vals = {
                'id': rec.id,
                'name': rec.name,
                'type': rec.type,
                'graph_type': rec.graph_type,
                'icon': rec.fa_icon,
                'cols': rec.graph_size,
                'color': rec.tile_color if rec.tile_color else '#1f6abb;',
                'text_color': rec.text_color if rec.text_color else '#FFFFFF;',
                'icon_color': rec.fa_color if rec.fa_color else '#1f6abb;',
                'tile_color': rec.tile_color if rec.tile_color else '#FFFFFF;',
                'model_name': rec.model_name,
                'measured_field': rec.measured_field.field_description if rec.measured_field else None,
                'y_field': rec.measured_field.name,
                'x_field': rec.group_by.name,
                'operation': rec.operation
            }
            domain = []
            if rec.filter:
                domain = expression.AND([literal_eval(rec.filter)])
            if rec.model_name:
                if rec.type == 'graph':
                    query = self.env[rec.model_name].get_query(domain,
                                                               rec.operation,
                                                               rec.measured_field,
                                                               group_by=rec.group_by)
                    try:
                        self._cr.execute(query)
                    except Exception as exc:
                        raise ValidationError(
                            _(f"Could'nt fetch data try another group by field for {rec.name} block")) from exc
                    records = self._cr.dictfetchall()
                    x_axis = []
                    for record in records:
                        x_axis.append(record.get(rec.group_by.name))
                    y_axis = []
                    for record in records:
                        y_axis.append(record.get('value'))
                    vals.update({'x_axis': x_axis, 'y_axis': y_axis})
                else:
                    query = self.env[rec.model_name].get_query(domain,
                                                               rec.operation,
                                                               rec.measured_field)
                    self._cr.execute(query)
                    records = self._cr.dictfetchall()
                    magnitude = 0
                    total = records[0].get('value')
                    while abs(total) >= 1000:
                        magnitude += 1
                        total /= 1000.0
                    val = f'{total:.2f}{" KMGTP"[magnitude]}' if magnitude else f'{total:.2f}'
                    records[0]['value'] = val
                    vals.update(records[0])
            block_id.append(vals)
        return block_id
