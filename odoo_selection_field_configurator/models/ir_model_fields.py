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
from collections import defaultdict

from odoo import api, models
from odoo.addons.base.models.ir_model import IrModelFieldsSelection as BaseIrModelFieldsSelection
from odoo.exceptions import UserError
from odoo.fields import Selection
from odoo.tools.misc import OrderedSet


class IrModelFields(models.Model):
    """ Inherited ir.model.fields to allow updating selection_ids on base fields
    while strictly preserving core protection against modifying base field schema. """
    _inherit = 'ir.model.fields'

    def _get_writable_properties(self):
        """ Include selection_ids in writable properties so that adding, editing,
        or reordering selection options on base fields does not trigger core
        schema alteration restrictions, while keeping all structural checks active. """
        properties = super()._get_writable_properties()
        return properties + ['selection_ids']


class IrModelFieldsSelection(models.Model):
    """ Inherited ir.model.fields.selection to dynamically manage selection
    options on base and custom fields, ensuring core option protection and
    seamless registry synchronization without import-time monkey-patching. """
    _inherit = 'ir.model.fields.selection'

    def _is_core_selection(self):
        """ Check whether a selection record was defined by Python code/modules.
        Returns True for core/module options and False for user-configured options. """
        self.ensure_one()
        if self.field_id.state == 'manual':
            return False
        # Module-defined selection records have entries in ir.model.data
        if self.env['ir.model.data'].sudo().search_count([
            ('model', '=', 'ir.model.fields.selection'),
            ('res_id', '=', self.id),
        ]):
            return True
        # Verify against Python class field definition
        model_obj = self.env.get(self.field_id.model)
        if model_obj is not None:
            field = model_obj._fields.get(self.field_id.name)
            if field and hasattr(field, '_selection_modules'):
                modules = field._selection_modules(model_obj)
                if self.value in modules:
                    return True
        return False

    @api.model_create_multi
    def create(self, vals_list):
        """ Allow creating selection options for base fields by bypassing
        the state != 'manual' check through standard model creation, and
        synchronizing the registry. """
        field_ids = {vals['field_id'] for vals in vals_list if 'field_id' in vals}
        fields = self.env['ir.model.fields'].browse(field_ids)
        field_names = {(field.model, field.name) for field in fields}

        recs = super(BaseIrModelFieldsSelection, self).create(vals_list)

        target_models = OrderedSet(
            model
            for model, name in field_names
            if model in self.pool and name in self.pool[model]._fields
        )
        if target_models:
            self.env.flush_all()
            self.pool._setup_models__(self.env.cr, target_models)
            self._sync_selection_fields(target_models)

        return recs

    def write(self, vals):
        """ Update selection options, preventing alteration of core technical values
        and ensuring database columns and registry are properly updated. """
        if 'field_id' in vals:
            raise UserError(self.env._('Changing the field of a selection is forbidden!'))

        if 'value' in vals:
            for selection in self:
                if vals['value'] != selection.value and selection._is_core_selection():
                    raise UserError(self.env._(
                        "The technical value of core/system selection options cannot be modified!"
                    ))

        res = super().write(vals)

        target_models = OrderedSet(self.mapped('field_id.model'))
        self._sync_selection_fields(target_models)
        return res

    @api.ondelete(at_uninstall=False)
    def _unlink_if_manual(self):
        """ Prevent deletion of core/system selection options, while allowing
        custom-added options to be safely deleted. """
        if self.env.context.get('force_delete'):
            return
        if self.pool.ready:
            core_selections = self.filtered(lambda sel: sel._is_core_selection())
            if core_selections:
                raise UserError(self.env._(
                    "Core/default selection options cannot be deleted! "
                    "Only custom options added dynamically can be deleted."
                ))

    def unlink(self):
        """ Unlink custom selection options and refresh model registry. """
        target_models = OrderedSet(self.mapped('field_id.model'))
        res = super().unlink()
        self._sync_selection_fields(target_models)
        return res

    def _register_hook(self):
        """ Re-synchronize custom selection options whenever the registry is built. """
        super()._register_hook()
        self._sync_selection_fields()

    @api.model
    def _sync_selection_fields(self, target_models=None):
        """ Synchronize selection fields in registry with ir.model.fields.selection,
        ensuring all options are present in field.selection and field._selection
        without requiring database queries during value conversions. """
        query = """
            SELECT f.model, f.name, s.value, COALESCE(s.name->>'en_US', s.value) AS label
            FROM ir_model_fields_selection s
            JOIN ir_model_fields f ON s.field_id = f.id
            WHERE f.ttype IN ('selection', 'reference')
        """
        params = []
        if target_models:
            query += " AND f.model IN %s"
            params.append(tuple(target_models))
        query += " ORDER BY s.sequence, s.id"

        self.env.cr.execute(query, params)
        rows = self.env.cr.fetchall()

        grouped = defaultdict(list)
        for model_name, field_name, value, label in rows:
            grouped[(model_name, field_name)].append((value, label))

        models_to_check = set(target_models) if target_models else {m for m, _ in grouped}

        for model_name in models_to_check:
            if model_name not in self.pool:
                continue
            for field_name, field in self.pool[model_name]._fields.items():
                if isinstance(field, Selection):
                    args = getattr(field, '_args__', None) or {}
                    base_selection = args.get('selection')
                    if base_selection is None and isinstance(getattr(field, 'selection', None), (list, tuple)):
                        base_selection = field.selection

                    if isinstance(base_selection, (list, tuple)):
                        db_selections = grouped.get((model_name, field_name))
                        if db_selections is not None:
                            existing_keys = {item[0] for item in db_selections}
                            merged_selections = list(db_selections)
                            for key, val in base_selection:
                                if key not in existing_keys:
                                    merged_selections.append((key, val))
                                    existing_keys.add(key)
                            field.selection = tuple(merged_selections)
                            field._selection = dict(merged_selections)
                        else:
                            field.selection = tuple(base_selection)
                            field._selection = dict(base_selection)
