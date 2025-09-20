# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
                                        "create action button.",
                                   default=True,
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
        """
        Computes and updates the `created_action_names` field with the names
        of the actions that have been created for the current follower.

        This method depends on the `action_name` field and is triggered when
        the `action_name` is modified. It retrieves the window actions associated
        with the current follower and stores their names as a comma-separated
        string in the `created_action_names` field.

        Key Steps:
        1. For each follower record, it searches for window actions (`ir.actions.act_window`)
           that match the action IDs in `follower.window_action_ids`.
        2. The names of the found actions are extracted using `mapped('name')`
           and joined into a single string, separated by commas.
        3. The resulting string is stored in the `created_action_names` field
           for display purposes.

        Returns:
        None
        """
        for follower in self:
            actions = self.env['ir.actions.act_window'].search(
                [('id', 'in', follower.window_action_ids.ids)])
            follower.created_action_names = ', '.join(actions.mapped('name'))

    def action_create(self):
        """
        Creates a new action in the selected model when the 'Add Action' button
        is clicked.

        This method performs the following tasks:
        1. Disables the `enabled_value` field and sets the `states` field to 'running'.
        2. Loops through the `applied_to_ids` (the models to which the action will
           be applied) and creates a new window action (`ir.actions.act_window`)
           for each model.
        3. The newly created window action is associated with the
           'follower.adding.removing' model and its corresponding form view.
        4. The created window action is linked to the current record by adding it
           to the `window_action_ids` field.
        5. Once the actions are created, it reloads the client interface to reflect
           the changes.

        Returns:
        dict: A dictionary to trigger a client action that reloads the current view
        to reflect the newly created actions.

        Key Fields:
        - `enabled_value`: Set to `False` to indicate the action creation process is
          ongoing.
        - `states`: Updated to 'running' to show the action is in progress.
        - `action_name`: The name used for the new actions.
        - `applied_to_ids`: The models to which the new actions are applied.
        - `window_action_ids`: Updated to include the newly created window actions.

        Returns:
        A reload action to refresh the view.
        """
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
        """
        Removes the contextual actions created for server actions.

        This method performs the following tasks:
        1. Sets the `states` field to 'cancel', indicating that the action removal
           process is in progress or has been completed.
        2. Deletes all window actions associated with the current record by unlinking
           them through the `window_action_ids` field.
        3. Clears the `window_action_ids` field by setting it to `False`.
        4. Resets the `enabled_value` field to `True`, enabling the functionality for
           future use.
        5. Returns an action to reload the client interface to reflect the removal of
           the actions.

        Returns:
        dict: A dictionary to trigger a client action that reloads the current view
        to reflect the removal of the actions.

        Key Fields:
        - `states`: Updated to 'cancel' to indicate that the action removal is
          completed or in progress.
        - `window_action_ids`: Unlinked (deleted) to remove the associated actions.
        - `enabled_value`: Set to `True` to re-enable the functionality for adding
          actions in the future.

        Returns:
        A reload action to refresh the view.
        """
        self.states = 'cancel'
        self.window_action_ids.unlink()
        self.window_action_ids = False
        self.enabled_value = True
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def unlink(self):
        """
        Overrides the unlink method to remove associated active actions before
        deleting the record.

        This method performs the following tasks:
        1. Iterates over each record in the current recordset (`self`).
        2. For each record, it calls the `action_unlink` method to remove any
           active actions associated with that record.
        3. After removing the active actions, it proceeds to call the original
           `unlink` method from the parent class to delete the record itself.

        Key Steps:
        - Ensures that all associated active actions are properly cleaned up
          before the record is deleted.
        - Maintains the integrity of related actions by explicitly handling their
          removal.

        Returns:
        None

        Note:
        - This method should be used when you want to ensure that any associated
          actions are removed before the record is deleted from the database.
        """
        for rec in self:
            rec.action_unlink()
        super().unlink()
