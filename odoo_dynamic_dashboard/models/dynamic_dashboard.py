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
from odoo import Command, api, fields, models
from odoo.exceptions import AccessError

DASHBOARD_ACTION_TAG = 'odoo_dynamic_dashboard.dashboard'
MENU_FIELDS = {
    'name', 'active', 'show_in_menu', 'menu_name', 'menu_parent_id', 'menu_sequence', 'menu_group_ids',
}
MANAGER_GROUP = 'odoo_dynamic_dashboard.odoo_dynamic_dashboard_group_manager'


class DynamicDashboard(models.Model):
    _name = 'dynamic.dashboard'
    _description = "Dynamic Dashboard"
    _order = 'sequence, id'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    user_id = fields.Many2one(
        'res.users', string="Owner", required=True, index=True,
        default=lambda self: self.env.user, ondelete='cascade',
    )
    is_shared = fields.Boolean(
        string="Shared",
        help="Shared dashboards are visible to every dashboard user, but only their owner "
             "and the dashboard managers can modify them.",
    )
    block_ids = fields.One2many('dynamic.dashboard.block', 'dashboard_id', string="Blocks")
    block_count = fields.Integer(compute='_compute_block_count')

    show_in_menu = fields.Boolean(
        string="Show in Menu", groups=MANAGER_GROUP,
        help="Create a menu item opening this dashboard directly.",
    )
    menu_name = fields.Char(
        string="Menu Name", groups=MANAGER_GROUP, translate=True,
        help="Name of the menu item. Leave empty to use the dashboard name.",
    )
    menu_parent_id = fields.Many2one(
        'ir.ui.menu', string="Parent Menu", groups=MANAGER_GROUP, ondelete='set null',
        help="Menu under which the dashboard is added. Leave empty to add it as a new app on the home screen.",
    )
    menu_sequence = fields.Integer(string="Menu Sequence", default=50, groups=MANAGER_GROUP)
    menu_group_ids = fields.Many2many(
        'res.groups', string="Menu Visible To", groups=MANAGER_GROUP,
        help="Users of these groups see the menu item and can open the dashboard, even if it is not shared. "
             "Leave empty for the dashboard users.",
    )
    menu_id = fields.Many2one('ir.ui.menu', string="Menu", readonly=True, copy=False, ondelete='set null')
    action_id = fields.Many2one(
        'ir.actions.client', string="Menu Action", readonly=True, copy=False, ondelete='set null',
    )

    @api.depends('block_ids')
    def _compute_block_count(self):
        counts = dict(self.env['dynamic.dashboard.block']._read_group(
            [('dashboard_id', 'in', self.ids)], ['dashboard_id'], ['__count'],
        ))
        for dashboard in self:
            dashboard.block_count = counts.get(dashboard, 0)

    def _check_owner_change(self, vals_list):
        """ Only dashboard administrators give dashboards to other users: the access rules
        let users manage their own dashboards, they must not make someone else the owner. """
        if self.env.su or self.env.user.has_group(MANAGER_GROUP):
            return
        if any(vals.get('user_id', self.env.uid) != self.env.uid for vals in vals_list):
            raise AccessError(self.env._("Only dashboard administrators can change the owner of a dashboard."))

    @api.model_create_multi
    def create(self, vals_list):
        self._check_owner_change(vals_list)
        dashboards = super().create(vals_list)
        dashboards._sync_menu()
        return dashboards

    def write(self, vals):
        if 'user_id' in vals:
            self._check_owner_change([vals])
        res = super().write(vals)
        if MENU_FIELDS & vals.keys():
            self._sync_menu()
        return res

    def unlink(self):
        menus = self.sudo().menu_id
        actions = self.sudo().action_id
        res = super().unlink()
        menus.unlink()
        actions.unlink()
        return res

    def copy_data(self, default=None):
        vals_list = super().copy_data(default=default)
        if 'name' not in (default or {}):
            for dashboard, vals in zip(self, vals_list):
                vals['name'] = self.env._("%s (copy)", dashboard.name)
        return vals_list

    def _sync_menu(self):
        """ Create, update or remove the menu item (and its client action) of the dashboards.
        Menus are technical records only administrators can write, hence the sudo: who may
        configure them is enforced by the ``groups`` of the menu fields. """
        default_groups = self.env.ref('odoo_dynamic_dashboard.odoo_dynamic_dashboard_group_user')
        for dashboard in self.sudo().with_context(active_test=False):
            if not (dashboard.show_in_menu and dashboard.active):
                dashboard.menu_id.unlink()
                dashboard.action_id.unlink()
                continue
            menu_name = dashboard.menu_name or dashboard.name
            action_vals = {
                'name': menu_name,
                'tag': DASHBOARD_ACTION_TAG,
                'params': {'dashboard_id': dashboard.id},
            }
            if dashboard.action_id:
                dashboard.action_id.write(action_vals)
            else:
                dashboard.action_id = dashboard.env['ir.actions.client'].create(action_vals)
            menu_vals = {
                'name': menu_name,
                'parent_id': dashboard.menu_parent_id.id,
                'sequence': dashboard.menu_sequence,
                'action': f'ir.actions.client,{dashboard.action_id.id}',
                'group_ids': [Command.set((dashboard.menu_group_ids or default_groups).ids)],
                'web_icon': (
                    False if dashboard.menu_parent_id
                    else 'odoo_dynamic_dashboard,static/description/icon.png'
                ),
            }
            if dashboard.menu_id:
                dashboard.menu_id.write(menu_vals)
            else:
                dashboard.menu_id = dashboard.env['ir.ui.menu'].create(menu_vals)

    def action_open_dashboard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': DASHBOARD_ACTION_TAG,
            'name': self.name,
            'params': {'dashboard_id': self.id},
        }

    @api.model
    def action_create_dashboard(self):
        """ Open the dashboard builder on a new dashboard. """
        return self.env['ir.actions.actions']._for_xml_id('odoo_dynamic_dashboard.dynamic_dashboard_action_builder')

    def get_dashboard_data(self):
        """ Return the dashboard description and the computed data of its blocks,
        as consumed by the dashboard client action. """
        self.ensure_one()
        dashboard = self.sudo()
        return {
            'id': self.id,
            'name': self.name,
            'can_edit': self.has_access('write'),
            'menu_id': dashboard.menu_id.id,
            'menu_name': dashboard.menu_name or self.name,
            'menu_parent_id': dashboard.menu_parent_id.id,
            'blocks': [block._get_block_data() for block in self.block_ids.sorted()],
        }

    @api.model
    def save_from_builder(self, values):
        """ Create or update a dashboard and its blocks from the dashboard builder.

        :param dict values: ``{'id': int|False, 'name': str, 'blocks': [config]}``, the
            blocks being in display order, see ``dynamic.dashboard.block._get_block_config``
        :return: the saved dashboard, as returned by ``get_dashboard_data``
        """
        Block = self.env['dynamic.dashboard.block']
        if values.get('id'):
            dashboard = self.browse(values['id'])
            dashboard.name = values['name']
        else:
            dashboard = self.create({'name': values['name']})
        configs = values.get('blocks', [])
        kept_ids = {config['id'] for config in configs if config.get('id')}
        (dashboard.block_ids - Block.browse(kept_ids)).unlink()
        to_create = []
        for sequence, config in enumerate(configs):
            vals = {**Block._config_to_vals(config), 'sequence': sequence}
            if config.get('id') in dashboard.block_ids.ids:
                Block.browse(config['id']).write(vals)
            else:
                to_create.append({**vals, 'dashboard_id': dashboard.id})
        Block.create(to_create)
        return dashboard.get_dashboard_data()

    @api.model
    def generate_with_ai(self, description, block_count=None):
        """ Design a dashboard from a description with Odoo's AI service, for the builder.

        :param int block_count: number of blocks to design, decided by the AI when not given
        :return: ``{'name': str, 'blocks': [config]}``, the blocks are not saved: the user
            reviews them in the builder first
        """
        self.check_access('create')
        return self.env['dynamic.dashboard.ai.generator']._generate_dashboard(description, block_count=block_count)

    def set_dashboard_menu(self, menu_name, parent_menu_id=False, group_ids=None):
        """ Add the dashboard to the menus, as asked after saving it in the builder.

        :return: the id of the dashboard menu item
        """
        self.ensure_one()
        vals = {'show_in_menu': True, 'menu_name': menu_name, 'menu_parent_id': parent_menu_id}
        if group_ids is not None:
            vals['menu_group_ids'] = [Command.set(group_ids)]
        self.write(vals)
        return self.sudo().menu_id.id

    def set_block_sequence(self, block_ids):
        """ Reorder the blocks of the dashboard following ``block_ids``. """
        self.ensure_one()
        blocks = self.env['dynamic.dashboard.block'].browse(block_ids).filtered(
            lambda block: block.dashboard_id == self,
        )
        for sequence, block in enumerate(blocks):
            block.sequence = sequence

    @api.model
    def get_dashboard_list(self):
        """ Return the dashboards the current user can open, for the dashboard switcher. """
        return self.search_read([], ['name', 'is_shared', 'user_id'])
