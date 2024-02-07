# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import ast
from odoo import fields, models
from odoo.exceptions import UserError


class AlertMessage(models.Model):
    """ Model for creating smart alert"""
    _name = 'alert.message'
    _description = 'Alert Message'

    name = fields.Char('name', required=True, help='Name')
    document_type_id = fields.Many2one('ir.model',
                                       string='Document Type',
                                       help='Select the type of the Document',
                                       required=False)
    group_id = fields.Many2one('res.groups', string='Group',
                               help='Select the group which alert wanted to visible')
    alert_messages = fields.Char('Alert Message', required=True,
                                 help='Alert message that will show in the view.')
    type = fields.Selection([('alert-primary', 'Alert Primary'),
                             ('alert-secondary', 'Alert Secondary'),
                             ('alert-success', 'Alert Success'),
                             ('alert-danger', 'Alert Danger'),
                             ('alert-warning', 'Alert Warning'),
                             ('alert-info', 'Alert Info')],
                            string='Type',
                            required=True, help='Type of alert message')
    model_name = fields.Char(related="document_type_id.model",
                             string='Model Name', help='Model Name')
    field_filter = fields.Char(string='Filter',
                               help='Set conditions for smart alerts',
                               default="[]")
    view_id = fields.Many2one('ir.ui.view', string='View',
                              help='Select the view for smart alerts',
                              required=True,
                              domain='[("model", "=", model_name), '
                                     '("type", "=", "form")]')
    new_view_id = fields.Many2one('ir.ui.view',
                                  string="Created New view Id",
                                  help='It will automatically create a view'
                                       ' record while saving the form',
                                  readonly=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('done', 'Done'), ('cancelled', 'Cancelled')],
        string='State', help='Different Stages', default="draft")

    def action_apply(self):
        """creating a view according to the record"""
        model = self.document_type_id
        model_view = self.view_id
        class_name = 'alert ' + self.type
        xml_id = ''
        if self.group_id.id:
            xml_ids = self.group_id.get_external_id()
            xml_id = xml_ids.get(self.group_id.id)
        filter = ast.literal_eval(self.field_filter)
        for i in range(len(filter)):
            if filter[i] == '&':
                filter[i] = '|'
            elif filter[i] == '|':
                filter[i] = '&amp;'
            else:
                if filter[i][1] == '=':
                    filter_list = list(filter[i])
                    filter_list[1] = '!='
                    filter = f" {filter_list[0]} {filter_list[1]} '{filter_list[2]}'"
                elif filter[i][1] == '!=':
                    filter_list = list(filter[i])
                    filter_list[1] = '=='
                    filter = f" {filter_list[0]} {filter_list[1]} '{filter_list[2]}'"
                elif filter[i][1] == '>':
                    filter_list = list(filter[i])
                    filter_list[1] = '&lt;'
                    filter = f" {filter_list[0]} {filter_list[1]} {filter_list[2]}"
                elif filter[i][1] == '<':
                    filter_list = list(filter[i])
                    filter_list[1] = '&gt;'
                    filter = f" {filter_list[0]} {filter_list[1]} {filter_list[2]}"
                elif filter[i][1] == '>=':
                    filter_list = list(filter[i])
                    filter_list[1] = '&lt;='
                    filter = f" {filter_list[0]} {filter_list[1]} {filter_list[2]}"
                elif filter[i][1] == '<=':
                    filter_list = list(filter[i])
                    filter_list[1] = '&gt;='
                    filter = f" {filter_list[0]} {filter_list[1]} {filter_list[2]}"
                elif filter[i][1] == 'ilike':
                    filter_list = list(filter[i])
                    filter_list[1] = 'not in'
                    filter = f" {filter_list[0]} {filter_list[1]} ['{filter_list[2]}']"
                elif filter[i][1] == 'not ilike':
                    filter_list = list(filter[i])
                    filter_list[1] = 'in'
                    filter = f" {filter_list[0]} {filter_list[1]} ['{filter_list[2]}']"
                elif filter[i][1] == 'in':
                    filter_list = list(filter[i])
                    filter_list[1] = 'not in'
                    filter = f" {filter_list[0]} {filter_list[1]} {filter_list[2]}"
                elif filter[i][1] == 'not in':
                    filter_list = list(filter[i])
                    filter_list[1] = 'in'
                    filter = f" {filter_list[0]} {filter_list[1]} {filter_list[2]}"

        invisible_filter = str(filter).replace("'", '"')
        if xml_id:
            if invisible_filter != '[]':
                arch = '<xpath expr="//sheet" position="before">' + '<div role="alert" class="' + class_name + '" ' + ' groups="' + xml_id + '"' + """ invisible=' """ + invisible_filter + "'" + '>' + self.alert_messages + '</div></xpath>'
            else:
                arch = '<xpath expr="//sheet" position="before">' + '<div role="alert" class="' + class_name + '" ' + ' groups="' + xml_id + '"' + '>' + self.alert_messages + '</div></xpath>'
        else:
            if invisible_filter != '[]':
                arch = '<xpath expr="//sheet" position="before">' + '<div role="alert" class="' + class_name + '" ' + """ invisible='""" + invisible_filter + "'" + '>' + self.alert_messages + '</div></xpath>'
            else:
                arch = '<xpath expr="//sheet" position="before">' + '<div role="alert" class="' + class_name + '" ' + '>' + self.alert_messages + '</div></xpath>'

        if model_view:
            view_data = {
                'name': self.type + '.alert.' + model_view.name + '.' + str(
                    self.id),
                'type': 'form',
                'model': model.model,
                'priority': 1,
                'inherit_id': model_view.id,
                'mode': 'extension',
                'arch_base': arch.encode('utf-8')
            }
            try:
                view = self.env["ir.ui.view"].create(view_data)
            except:
                raise UserError("Can't create a view based on this domain")
            self.new_view_id = view
            self.state = 'done'

    def action_cancel(self):
        """cancel the alert message"""
        self.state = 'cancelled'
        self.new_view_id.unlink()

    def reset_draft(self):
        """reset the record into the draft state"""
        self.state = 'draft'
