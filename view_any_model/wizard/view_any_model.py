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
#############################################################################
from odoo import fields, models
from odoo.exceptions import UserError


class ViewAnyModel(models.TransientModel):
    """Wizard to access records and views of any model
    with appropriate access rights."""
    _name = 'view.any.model'
    _description = 'View Any Model'

    def _get_domain(self):
        """Return a domain that filters out all transient
        and abstract models, or models without views."""
        model_ids = self.env['ir.model'].search(
            [('transient', '=', False)]).filtered(
            lambda rec: rec.view_ids).ids
        return [('id', 'in', model_ids)]

    view_type = fields.Selection(
        selection=[('list', 'List'), ('form', 'Form')],
        default='list', required=True, help='Select the type of view')
    record_id = fields.Integer(string="Record ID", default=1,
                               help='Enter the ID of the record')
    model_id = fields.Many2one('ir.model',
                               ondelete='set null',
                               help='Select the model',
                               domain=lambda self: self._get_domain())
    model_name = fields.Char(related='model_id.model', string='Model Name',
                             help='Technical name of the selected model',
                             readonly=True, store=True)
    filter_domain = fields.Char(string='Apply on', help='Enter domain filter')

    def action_view_model(self):
        """View records of the selected model in list or form view.

        :return: Action dictionary for the list/form view of the selected model
        """
        self.ensure_one()
        self.env[self.model_name].check_access('read')
        if self.view_type == 'form':
            if self.record_id < 1:
                raise UserError(
                    self.env._("The record ID must be a positive integer."))
            if not self.env[self.model_name].search(
                    [('id', '=', self.record_id)]):
                # Search is used instead of browse to verify record existence consistently
                raise UserError(
                    self.env._("Enter the ID of an existing record."))
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
                'view_mode': 'list,form',
                'views': [(False, 'list'), (False, 'form')],
            })
        return action
