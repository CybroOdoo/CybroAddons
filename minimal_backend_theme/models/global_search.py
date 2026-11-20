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
from odoo import api, models
from odoo.exceptions import AccessError

SEARCH_MODELS_PARAM = 'minimal_backend_theme.search_models'

# Record types searched from the top bar search when Settings name none;
# models of apps that are not installed are skipped.
DEFAULT_SEARCH_MODELS = [
    'res.partner',
    'crm.lead',
    'sale.order',
    'purchase.order',
    'account.move',
    'product.template',
    'stock.picking',
    'project.project',
    'project.task',
    'hr.employee',
    'mrp.production',
    'calendar.event',
]

MIN_QUERY_LENGTH = 2


class MinimalBackendThemeGlobalSearch(models.AbstractModel):
    _name = 'minimal_backend_theme.global_search'
    _description = 'Backend Theme: record search of the top bar'

    @api.model
    def _get_search_model_names(self):
        """Searchable models, in display order: those chosen in Settings, or
        the defaults; only real, installed models are kept."""
        # None: never saved, use the defaults; "": the admin chose none.
        param = self.env['ir.config_parameter'].sudo().get_str(SEARCH_MODELS_PARAM, None)
        if param is None:
            names = DEFAULT_SEARCH_MODELS
        else:
            names = [name.strip() for name in param.split(',') if name.strip()]
        return [name for name in names if self._is_searchable_model(name)]

    @api.model
    def _app_main_model(self, app):
        """The model of an app's main screen: what clicking the app opens,
        i.e. the action of its first menu, depth first (as the web client
        does)."""
        menu = app
        while menu and not menu.action:
            menu = menu.child_id[:1]
        action = menu.action if menu else False
        if action and action._name == 'ir.actions.act_window':
            return action.sudo().res_model
        return False

    @api.model
    def _pick_menu_by_model(self, menus, model_of_menu):
        """For each model, the menu its records open in, in menu order within
        the chosen app. The app is, in that order of preference:
          1. one whose main screen is that model (Contacts for contacts,
             Sales for quotations), though Invoicing lists customers too;
          2. the one with the most menus on that model (Sales over CRM's
             single "My Quotations" menu, if neither were the main screen).

        :param menus: candidate menus, in menu order
        :param model_of_menu: function giving a menu's model, or False
        :return: ``{model: menu id}``
        """
        Menu = self.env['ir.ui.menu']
        candidates = {}  # model -> app id -> [menu ids]
        for menu in menus:
            model = model_of_menu(menu)
            if not model:
                continue
            app_id = int(menu.parent_path.split('/')[0]) if menu.parent_path else menu.id
            candidates.setdefault(model, {}).setdefault(app_id, []).append(menu.id)
        main_model = {}

        def app_rank(model, item):
            app_id, menu_ids = item
            if app_id not in main_model:
                main_model[app_id] = self._app_main_model(Menu.browse(app_id))
            return (main_model[app_id] == model, len(menu_ids))

        # max() keeps the first app (in menu order) on ties.
        return {
            model: max(by_app.items(), key=lambda item, model=model: app_rank(model, item))[1][0]
            for model, by_app in candidates.items()
        }

    @api.model
    def _get_model_menus(self, model_names):
        """For each model, the menu the current user can see that its records
        open in (see _pick_menu_by_model), for the app's icon and breadcrumbs."""
        actions = self.env['ir.actions.act_window'].sudo().search_fetch(
            [('res_model', 'in', model_names)], ['res_model'],
        )
        if not actions:
            return {}
        model_by_ref = {f'ir.actions.act_window,{action.id}': action.res_model for action in actions}
        # Only menus the user can see (searching menus does not filter them).
        menus = self.env['ir.ui.menu'].search(
            [('action', 'in', list(model_by_ref))],
        )._filter_visible_menus()
        return self._pick_menu_by_model(
            menus, lambda menu: model_by_ref.get(f'{menu.action._name},{menu.action.id}'),
        )

    @api.model
    def search_records(self, query, limit=5):
        """Records whose display name matches ``query``, grouped by model.

        Runs as the current user: models they cannot read are skipped and
        record rules apply. Each model's own name search is used, so e.g.
        contacts also match on email or reference.

        :return: list of ``{model, label, menu_id, records: [{id,
            display_name}], has_more}``, in the order of the searchable
            models; ``menu_id`` is the menu opening the model, if any.
        """
        query = (query or '').strip()
        if len(query) < MIN_QUERY_LENGTH:
            return []
        IrModel = self.env['ir.model'].sudo()
        groups = []
        for name in self._get_search_model_names():
            Model = self.env[name]
            if not Model.has_access('read'):
                continue
            try:
                matches = Model.name_search(query, limit=limit + 1)
            except AccessError:
                continue
            if not matches:
                continue
            groups.append({
                'model': name,
                'menu_id': False,
                'label': IrModel._get(name).name,
                'records': [
                    {'id': record_id, 'display_name': display_name}
                    for record_id, display_name in matches[:limit]
                ],
                'has_more': len(matches) > limit,
            })
        if groups:
            menu_by_model = self._get_model_menus([group['model'] for group in groups])
            for group in groups:
                group['menu_id'] = menu_by_model.get(group['model'], False)
        return groups

    @api.model
    def _is_searchable_model(self, name):
        return (
            name in self.env
            and not self.env[name]._abstract
            and not self.env[name]._transient
        )

    @api.model
    def get_recent_records(self, entries, limit=6):
        """Recently opened records (tracked by the web client), checked again:
        only those that still exist and the current user can read are kept,
        with their current name.

        :param entries: ``[{model, id}]``, most recent first
        :return: ``[{model, id, display_name, label, menu_id}]``
        """
        IrModel = self.env['ir.model'].sudo()
        wanted = []
        for entry in entries or []:
            model, record_id = entry.get('model'), entry.get('id')
            if (
                isinstance(model, str) and isinstance(record_id, int)
                and self._is_searchable_model(model)
                and (model, record_id) not in wanted
            ):
                wanted.append((model, record_id))
        readable = {}
        for model in {model for model, _id in wanted}:
            Model = self.env[model]
            if not Model.has_access('read'):
                continue
            ids = [record_id for name, record_id in wanted if name == model]
            try:
                # search() applies record rules and drops deleted records.
                records = Model.search([('id', 'in', ids)])
                readable[model] = {record.id: record.display_name for record in records}
            except AccessError:
                continue
        results = []
        for model, record_id in wanted:
            if record_id in readable.get(model, {}):
                results.append({
                    'model': model,
                    'id': record_id,
                    'display_name': readable[model][record_id],
                    'label': IrModel._get(model).name,
                    'menu_id': False,
                })
            if len(results) >= limit:
                break
        if results:
            menu_by_model = self._get_model_menus(list({r['model'] for r in results}))
            for result in results:
                result['menu_id'] = menu_by_model.get(result['model'], False)
        return results

    @api.model
    def get_create_targets(self):
        """What "new ..." in the top bar search can create: one entry per
        record type the current user may create, opened through the menu its
        records open in (see _pick_menu_by_model), so the new record gets
        that app's defaults and breadcrumbs.

        :return: ``[{model, label, menu_id}]``
        """
        IrModel = self.env['ir.model'].sudo()
        menus = self.env['ir.ui.menu'].search([('action', '!=', False)])._filter_visible_menus()
        creatable = {}

        def creatable_model(menu):
            action = menu.action
            if action._name != 'ir.actions.act_window':
                return False
            action = action.sudo()
            model = action.res_model
            if model not in creatable:
                creatable[model] = (
                    self._is_searchable_model(model)
                    and self.env[model].has_access('create')
                )
            if not creatable[model] or 'form' not in (action.view_mode or '').split(','):
                return False
            return model

        menu_by_model = self._pick_menu_by_model(menus, creatable_model)
        Menu = self.env['ir.ui.menu']

        def is_main(model, menu_id):
            """Whether the model is its app's main screen (contacts in
            Contacts, quotations in Sales): what users create most."""
            menu = Menu.browse(menu_id)
            app_id = int(menu.parent_path.split('/')[0]) if menu.parent_path else menu_id
            return self._app_main_model(Menu.browse(app_id)) == model

        # Each app's main record type first, then in menu order.
        menu_order = {menu_id: index for index, menu_id in enumerate(menus.ids)}
        ranked = sorted(
            menu_by_model.items(),
            key=lambda item: (not is_main(*item), menu_order[item[1]]),
        )
        targets = {
            model: {'model': model, 'label': IrModel._get(model).name, 'menu_id': menu_id}
            for model, menu_id in ranked
        }
        return list(targets.values())
