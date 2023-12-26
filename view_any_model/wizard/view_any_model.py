# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Abhin K(odoo@cybrosys.com)
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
##############################################################################
from odoo import fields, models, _
from odoo.exceptions import UserError


class ViewAnyModel(models.TransientModel):
    """Model is viewed as a wizard to access any views of
    any model and should have necessary access rights"""
    _name = 'view.any.model'
    _description = 'View Any Model'

    def _get_domain(self):
        """Returns the domain that filter out all the Transient
        and Abstract models or the models with no views"""
        model_ids = self.env['ir.model'].search(
            [('transient', '=', False)]).filtered(
            lambda rec: rec.view_ids).ids
        return [('id', 'in', model_ids)]

    view_type = fields.Selection(
        selection=[('tree', 'Tree'), ('form', 'Form')], string='View Type',
        default='tree', required=True, help='Select the Type of view')
    record_id = fields.Integer(string="Record ID", default="1",
                               help='Enter the id of the record')
    model_id = fields.Many2one('ir.model', string='Model',
                               ondelete='set null',
                               help='Select the Model',
                               domain=_get_domain)
    model_name = fields.Char(related='model_id.model', string='Model Name',
                             help='Model name is saved', readonly=True,
                             store=True)
    filter_domain = fields.Char(string='Apply on', help='Enter your Domain')

    def action_view_model(self):
        """
        View the records of selected model in tree or form view
        :return: tree/form view of selected model
        """
        try:
            if self.view_type == 'form':
                if self.record_id < 1:
                    raise UserError(_("ID should be a positive integer"))
                if not self.env[self.model_name].sudo().search(
                        [('id', '=', self.record_id)]):
                    # Browse function is replaced with search as it doesn't
                    # actually give a consistent output
                    raise UserError(_("Enter ID of existing record"))
            action = {
                'name': self.model_id.name,
                'type': 'ir.actions.act_window',
                'res_model': self.model_name,
                'view_id': False,
                'target': 'main',
                'domain': self.filter_domain or [],
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
        except ValueError:
            raise UserError(
                _(f'You are not allowed to access {self.model_name} records.'))
