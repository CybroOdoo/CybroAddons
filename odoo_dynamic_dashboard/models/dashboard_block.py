# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import models, fields, api
from odoo.osv import expression
from ast import literal_eval


class DashboardBlock(models.Model):
    _name = "dashboard.block"
    _description = "Dashboard Blocks"
    _rec_name = "name"

    def get_default_action(self):
        action_id = self.env.ref('odoo_dynamic_dashboard.action_dynamic_dashboard')
        if action_id:
            return action_id.id
        else:
            return False

    name = fields.Char(string="Name", help='Name of the block')
    field_id = fields.Many2one('ir.model.fields', 'Measured Field',domain="[('store', '=', True), ('model_id', '=', model_id), ('ttype', 'in', ['float','integer','monetary'])]")
    fa_icon = fields.Char(string="Icon")
    graph_size = fields.Selection(
        selection=[("col-lg-4", "Small"), ("col-lg-6", "Medium"), ("col-lg-12", "Large")],
        string="Graph Size",default='col-lg-4')
    operation = fields.Selection(
        selection=[("sum", "Sum"), ("avg", "Average"), ("count", "Count")],
        string="Operation", help='Tile Operation that needs to bring values for tile')

    graph_type = fields.Selection(
        selection=[("bar", "Bar"), ("radar", "Radar"), ("pie", "Pie"), ("line", "Line"), ("doughnut", "Doughnut")],
        string="Chart Type", help='Type of Chart')
    measured_field = fields.Many2one("ir.model.fields", "Measured Field")
    client_action = fields.Many2one('ir.actions.client', default = get_default_action)

    type = fields.Selection(
        selection=[("graph", "Chart"), ("tile", "Tile")], string="Type", help='Type of Block ie, Chart or Tile')
    x_axis = fields.Char(string="X-Axis")
    y_axis = fields.Char(string="Y-Axis")
    group_by = fields.Many2one("ir.model.fields", store=True, string="Group by(Y-Axis)", help='Field value for Y-Axis')
    tile_color = fields.Char(string="Tile Color", help='Primary Color of Tile')
    text_color = fields.Char(string="Text Color", help='Text Color of Tile')
    fa_color = fields.Char(string="Icon Color", help='Icon Color of Tile')
    filter = fields.Char(string="Filter")
    model_id = fields.Many2one('ir.model', 'Model')
    model_name = fields.Char(related='model_id.model', readonly=True)

    filter_by = fields.Many2one("ir.model.fields", string=" Filter By")
    filter_values = fields.Char(string="Filter Values")

    sequence = fields.Integer(string="Sequence")
    edit_mode = fields.Boolean(default=False, invisible=True)

    def get_dashboard_vals(self, action_id):
        """Dashboard block values"""
        block_id = []
        dashboard_block = self.env['dashboard.block'].sudo().search([('client_action', '=', int(action_id))])
        for rec in dashboard_block:
            color = rec.tile_color if rec.tile_color else '#1f6abb;'
            icon_color = rec.tile_color if rec.tile_color else '#1f6abb;'
            text_color = rec.text_color if rec.text_color else '#FFFFFF;'
            vals = {
                'id': rec.id,
                'name': rec.name,
                'type': rec.type,
                'graph_type': rec.graph_type,
                'icon': rec.fa_icon,
                'cols': rec.graph_size,
                'color': 'background-color: %s;' % color,
                'text_color': 'color: %s;' % text_color,
                'icon_color': 'color: %s;' % icon_color,
            }
            domain = []
            if rec.filter:
                domain = expression.AND([literal_eval(rec.filter)])
            if rec.model_name:
                if rec.type == 'graph':
                    query = self.env[rec.model_name].get_query(domain, rec.operation, rec.measured_field,
                                                               group_by=rec.group_by)
                    self._cr.execute(query)
                    records = self._cr.dictfetchall()
                    x_axis = []
                    for record in records:
                        x_axis.append(record.get(rec.group_by.name))
                    y_axis = []
                    for record in records:
                        y_axis.append(record.get('value'))
                    vals.update({'x_axis': x_axis, 'y_axis': y_axis})
                else:
                    query = self.env[rec.model_name].get_query(domain, rec.operation, rec.measured_field)
                    self._cr.execute(query)
                    records = self._cr.dictfetchall()
                    magnitude = 0
                    total = records[0].get('value')
                    while abs(total) >= 1000:
                        magnitude += 1
                        total /= 1000.0
                    # add more suffixes if you need them
                    val = '%.2f%s' % (total, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])
                    records[0]['value'] = val
                    vals.update(records[0])
            block_id.append(vals)
        return block_id


class DashboardBlockLine(models.Model):
    _name = "dashboard.block.line"

    sequence = fields.Integer(string="Sequence")
    block_size = fields.Integer(string="Block size")
