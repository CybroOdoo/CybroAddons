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
from odoo import api, fields, models


class MultiFollower(models.Model):
    """Model for managing dynamic multi-follower actions."""
    _name = 'multi.follower'
    _description = 'Multi Follower'
    _rec_name = 'action_name'

    action_name = fields.Char(help="Name of the action visible under the "
                                   "appropriate model's action menu.",
                              required=True)
    applied_to_ids = fields.Many2many('ir.model',
                                      domain="[('is_mail_thread', '=', True)]",
                                      help='Select the model to which you '
                                           'want to apply this action.',
                                      required=True)
    enabled_value = fields.Boolean(string="Create Action",
                                   help="Enabling and hiding the "
                                        "create action button.",
                                   default=True,
                                   copy=False)
    created_action_names = fields.Char(compute="_compute_created_action_names",
                                       help="Displays names of created actions. "
                                            "Cleared when actions are removed.")
    states = fields.Selection([('draft', 'Draft'),
                               ('running', 'Running'), ('cancel', 'Cancelled')],
                              string='State', help='State of the action',
                              default="draft", copy=False)
    window_action_ids = fields.Many2many('ir.actions.act_window',
                                         string="Window Actions",
                                         help="Related Window Actions")

    @api.depends('action_name', 'window_action_ids', 'window_action_ids.name')
    def _compute_created_action_names(self):
        """
        Computes and updates the `created_action_names` field with the names
        of the actions that have been created for the current follower.
        """
        for follower in self:
            follower.created_action_names = ', '.join(follower.window_action_ids.mapped('name'))

    def action_create(self):
        """
        Creates contextual window actions for the selected models across
        all records in self.
        """
        view_id = self.env.ref(
            'all_in_one_multi_followers.follower_adding_removing_view_form',
        ).id
        for record in self:
            record.enabled_value = False
            record.states = 'running'
            for model_id in record.applied_to_ids:
                res = self.env['ir.actions.act_window'].create({
                    'name': record.action_name,
                    'res_model': 'follower.adding.removing',
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'binding_model_id': model_id.id,
                    'target': 'new',
                    'view_id': view_id,
                    'binding_view_types': 'list',
                })
                record.window_action_ids += res
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def action_unlink(self):
        """
        Removes the contextual actions created for records in self.
        """
        for record in self:
            record.states = 'cancel'
            record.window_action_ids.unlink()
            record.window_action_ids = False
            record.enabled_value = True
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def unlink(self):
        """
        Overrides the unlink method to remove associated active actions before
        deleting the record.
        """
        for rec in self:
            rec.action_unlink()
        return super().unlink()
