# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mohammed Irfan T (<https://www.cybrosys.com>)
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
from odoo import api, fields, models, _
from odoo.exceptions import UserError

OBJECT_VALS = {
    '=': '!=',
    '!=': '=',
    '>': '&lt;',
    '<': '&gt;',
    '>=': '&lt=;',
    '<=': '&gt=;',
    'ilike': 'not in',
    'not ilike': 'in',
    'in': 'not in',
    'not in': 'in'
}


class AlertMessage(models.Model):
    """
        This class used to create the smart alert warnings
    """
    _name = 'alert.message'
    _description = 'Alert Message'

    name = fields.Char(string='Name', required=True,
                       help="Name for the smart alert warning")
    document_type_id = fields.Many2one('ir.model', required=True,
                                       help="Choose the model in which where "
                                            "you need to show the warning",
                                       string="Document Type",
                                       ondelete='cascade')
    group_id = fields.Many2one('res.groups',
                               help="Choose which user groups need to see "
                                    "the warnings", string="Group")
    alert_messages = fields.Char(string='Alert Message', required=True,
                                 help='Alert message that will show '
                                      'in the view.')
    type = fields.Selection([('alert-primary', 'Alert Primary'),
                             ('alert-secondary', 'Alert Secondary'),
                             ('alert-success', 'Alert Success'),
                             ('alert-danger', 'Alert Danger'),
                             ('alert-warning', 'Alert Warning'),
                             ('alert-info', 'Alert Info')],
                            required=True, help='Type of alert message',
                            string="Type")
    model_name = fields.Char(string="Model Name", help="name of selected "
                                                       "model",
                             related="document_type_id.model")
    field_filter = fields.Char(default="[]",
                               help="Add any filtration if you need to show"
                                    " the warning messages",
                               string="Field Filter")
    view_id = fields.Many2one('ir.ui.view', required=True,
                              domain='[("model", "=", model_name), '
                                     '("type", "=", "form"), '
                                     '("is_alert_boolean", "=", False)]',
                              help="Choose the view in which the alert need "
                                   "to show", string='View')
    new_view_id = fields.Many2one('ir.ui.view',
                                  string="Created New view Id",
                                  readonly=True,
                                  help="To generate the view id of newly "
                                       "created record")
    state = fields.Selection(
        [('draft', 'Draft'), ('done', 'Done')],
        default="draft", help="Stages of the record", string="State")
    is_edit_mode = fields.Boolean(string="Is Edit",
                                  help="To check is it is in edit mode")

    def action_confirm(self):
        """
            This method is responsible for creating a new record and related
            view based on provided parameters and conditions.

            It performs the following actions:
            - Deletes the existing new_view_id if it exists.
            - Retrieves model and model_view based on document_type_id and
            view_id.
            - Constructs an XML snippet (arch) for the view with dynamic
            attributes.
            - Attempts to create the new view and updates related fields.

            :return: The ID of the newly created view.
        """
        if self.new_view_id:
            self.new_view_id.unlink()
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
                filter_list = list(filter[i])
                filter_list[1] = OBJECT_VALS[filter[i][1]]
                filter[i] = tuple(filter_list)
        invisible_filter = str(filter).replace("'", '"')
        arch = '<xpath expr="//sheet" position="before">'
        arch += '<div role="alert" class="' + class_name + '" '
        if xml_id:
            arch += ' groups="' + xml_id + '"'
        if invisible_filter != '[]':
            arch += """ attrs='{"invisible": """ + invisible_filter + "}'"
        arch += '>' + self.alert_messages + '</div></xpath>'
        if model_view:
            print('dd')
            view_data = {
                'name': self.type + '.alert.' + model_view.name + '.' + str(
                    self.id),
                'type': 'form',
                'model': self.document_type_id.model,
                'priority': 1,
                'inherit_id': model_view.id,
                'mode': 'extension',
                'arch_base': arch.encode('utf-8')
            }
            try:
                view = self.env["ir.ui.view"].create(view_data)
                self.new_view_id = view.id
                view.is_alert_boolean = True
                self.state = 'done'
            except:
                raise UserError(_("Can't create a view based on this domain"))
            return view.id

    def action_reset_draft(self):
        """Reset the record into the draft state"""
        self.state = 'draft'
        self.new_view_id.unlink()

    def unlink(self):
        """To unlink the alert record on deleting the record"""
        self.new_view_id.unlink()
        res = super().unlink()
        return res
