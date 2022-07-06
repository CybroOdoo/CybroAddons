# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Abhishek E T (odoo@cybrosys.com)
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

from odoo import fields, models, _
from odoo.exceptions import UserError


class ViewAnyModel(models.TransientModel):
    _name = 'view.any.model'
    _description = 'View Any Model'

    view_type = fields.Selection(
        selection=[('tree', 'Tree'), ('form', 'Form')], string='View Type',
        default='tree', required=True)
    record_id = fields.Integer(string="ID", default="1")
    model_id = fields.Many2one('ir.model', string='Model', ondelete='set null')
    model_name = fields.Char(related='model_id.model', string='Model Name',
                             readonly=True, store=True)
    filter_domain = fields.Char(string='Apply on')

    def action_view_model(self):
        """
        View the records of selected model in tree or form view
        :return: tree/ form view of selected model
        """
        if self.view_type == 'form':
            if self.record_id < 1:
                raise UserError(_("ID should be a positive integer"))
            if not self.env[self.model_name].sudo().search(
                    [('id', '=', self.record_id)]):
                raise UserError(_("Enter ID of existing record"))
        domain = self.filter_domain
        if not domain:
            domain = []
        action = {
            'name': self.model_id.name,
            'type': 'ir.actions.act_window',
            'res_model': self.model_name,
            'view_id': False,
            'target': 'main',
            'domain': domain,
            'context': {
                'create': False,
                'edit': False,
                'delete': False,
                'copy': False
            }
        }
        if self.view_type == 'form':
            action.update({
                'res_id': self.record_id,
                'view_mode': 'form',
                'views': [(False, 'form')],
            })
        else:
            action.update({
                'view_mode': 'tree,form',
                'views': [(False, 'tree'), (False, 'form')],
            })
        return action
