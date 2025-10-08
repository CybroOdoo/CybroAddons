# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Junaidul Ansar M (odoo@cybrosys.com)
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
###############################################################################
from odoo import api, fields, models


class MultiFollower(models.Model):
    """Creating multi follower creation model"""
    _name = 'multi.follower'
    _description = 'Multi Follower'
    _rec_name = 'action_name'

    action_name = fields.Char(string="Action Name",
                              help='This is the  action name. So this name is '
                                   'visible under the the appropriate'
                                   ' model action.',
                              required=True)
    applied_to_ids = fields.Many2many('ir.model',
                                      string='Applied To',
                                      help='Select the model in which you '
                                           'want to apply this action.',
                                      required=True)
    enabled_value = fields.Boolean(string="Create Action",
                                   help="Enabling and hiding the "
                                        "create action button.", default=True,
                                   copy=False)
    created_action_names = fields.Char(string="Created Action Names",
                                       compute="_compute_created_action_names",
                                       help='If the name is visible to the line'
                                            ' its created the action. If its '
                                            'not its deleted the action.')
    states = fields.Selection([('draft', 'Draft'),
                               ('running', 'Running'), ('cancel', 'Cancelled')],
                              string='State', help='State of the action',
                              default="draft", copy=False)
    window_action_ids = fields.Many2many('ir.actions.act_window',
                                         string="Window Actions",
                                         helps="Related Window Actions")

    @api.depends('action_name')
    def _compute_created_action_names(self):
        """Computation of adding the action names"""
        for follower in self:
            actions = self.env['ir.actions.act_window'].search(
                [('id', 'in', follower.window_action_ids.ids)])
            follower.created_action_names = ', '.join(actions.mapped('name'))

    def action_create(self):
        """When clicking the Add Action button to crete the action in
        appropriate model"""
        self.enabled_value = False
        self.states = 'running'
        # Check if action_name has changed and update existing actions
        for model_id in self.applied_to_ids:
            res = self.env['ir.actions.act_window'].create({
                'name': self.action_name,
                'res_model': 'follower.adding.removing',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'binding_model_id': model_id.id,
                'target': 'new',
                'view_id': self.env.ref(
                    'all_in_one_multi_followers.'
                    'follower_adding_removing_view_form').id,
                'binding_view_types': 'list'
            })
            self.window_action_ids += res
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def action_unlink(self):
        """ Remove the contextual actions created for the server actions. """
        self.states = 'cancel'
        self.window_action_ids.unlink()
        self.window_action_ids = False
        self.enabled_value = True
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def unlink(self):
        """Super the unlink method to remove the active action"""
        for rec in self:
            rec.action_unlink()
        super().unlink()
