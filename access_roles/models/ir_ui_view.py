# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
#############################################################################
from odoo import models


class IrUiView(models.Model):
    """Extend ir.ui.view to apply role-based UI restrictions."""
    _inherit = 'ir.ui.view'

    def _postprocess_access_rights(self, tree):
        """Modify the view tree, list, kanban based on role-based access rules."""
        current_model = tree.get('model_access_rights')
        tree = super()._postprocess_access_rights(tree)
        current_user_access_role = self.env.user.access_role_id
        if not current_user_access_role:
            return tree
        role_management = current_user_access_role.role_management_id
        if not role_management:
            return tree
        button_access_records = role_management.button_access_ids
        filter_access_records = role_management.filter_access_ids
        field_access_records = role_management.field_access_ids
        model_access_records = role_management.model_access_ids
        tree = self._process_button_access(tree, button_access_records, current_model)
        tree = self._process_tab_access(tree, button_access_records, current_model)
        tree = self._process_filter_access(tree, filter_access_records, current_model)
        tree = self._process_field_access(tree, field_access_records, current_model)
        tree = self._process_model_access(tree, model_access_records, role_management,
                                          current_model)
        return tree

    def _process_button_access(self, tree, button_access_records, current_model):
        """Process button access restrictions."""
        for button in button_access_records:
            for button_node in tree.xpath('//button'):
                button_name = button_node.get('name')
                for record in button.button_ids:
                    if current_model == record.model_id.model and button_name == record.action_name:
                        button_node.set('invisible', 'True')
        return tree

    def _process_tab_access(self, tree, button_access_records, current_model):
        """Process tab access restrictions."""
        for tab in button_access_records:
            for tab_node in tree.xpath('//page'):
                tab_name = tab_node.get('string')
                for record in tab.tab_ids:
                    if current_model == record.model_id.model and tab_name == record.name:
                        tab_node.set('invisible', 'True')
        return tree

    def _process_filter_access(self, tree, filter_access_records, current_model):
        """Process filter and groupBy access restrictions."""
        for groupby in filter_access_records:
            for filter_node in tree.xpath('//filter'):
                filter_name = filter_node.get('string')
                for record in groupby.filter_ids:
                    if current_model == record.model_id.model and filter_name == record.name:
                        filter_node.set('invisible', 'True')
                for record in groupby.group_ids:
                    if current_model == record.model_id.model and filter_name == record.name:
                        filter_node.set('invisible', 'True')
        return tree

    def _process_field_access(self, tree, field_access_records, current_model):
        """Process field access restrictions."""
        for field_model in field_access_records.fields_ids:
            for field_node in tree.xpath('//field'):
                field_name = field_node.get('name')
                if field_model.model_id.model == current_model and field_name == field_model.name:
                    field_access = field_access_records.filtered(
                        lambda f: field_name in f.fields_ids.mapped("name"))
                    if field_access:
                        self._apply_field_attributes(field_node, field_access)
        return tree

    def _apply_field_attributes(self, field_node, field_access):
        """Apply attributes to field nodes based on access rights."""
        if any(field_access.mapped("is_field_required")):
            field_node.set("required", "1")
        if any(field_access.mapped("is_field_invisible")):
            field_node.set("invisible", "1")
        if any(field_access.mapped("is_field_readonly")):
            field_node.set("readonly", "1")
        if any(field_access.mapped("is_remove_link")):
            field_node.set("options", '{"no_open": true}')

    def _process_model_access(self, tree, model_access_records, role_management,
                              current_model):
        """Process model access restrictions for form, list, and kanban views."""
        tree = self._process_form_access(tree, model_access_records, role_management,
                                         current_model)
        tree = self._process_list_access(tree, model_access_records, role_management,
                                         current_model)
        tree = self._process_kanban_access(tree, model_access_records,
                                           role_management, current_model)
        return tree

    def _process_form_access(self, tree, model_access_records, role_management,
                             current_model):
        """Process form view access restrictions."""
        for model_node in tree.xpath('//form'):
            if role_management.is_readonly:
                model_node.set("edit", "false")
                model_node.set("create", "false")
            for model in model_access_records:
                if current_model == model.model_id.model:
                    if model.is_model_readonly:
                        model_node.set("edit", "false")
                        model_node.set("create", "false")
                        for button_node in model_node.xpath('//button'):
                            button_node.set('invisible', 'True')
                    if model.is_hide_create:
                        model_node.set("create", "false")
                    if model.is_hide_delete:
                        model_node.set("delete", "false")
                    if model.is_hide_duplicate:
                        model_node.set("duplicate", "false")
        return tree

    def _process_list_access(self, tree, model_access_records, role_management,
                             current_model):
        """Process list view access restrictions."""
        for list_node in tree.xpath('//list'):
            if role_management.is_readonly:
                list_node.set("edit", "false")
                list_node.set("create", "false")
            for model in model_access_records:
                if current_model == model.model_id.model:
                    if model.is_model_readonly:
                        list_node.set("create", "false")
                    if model.is_hide_create:
                        list_node.set("create", "false")
                    if model.is_hide_delete:
                        list_node.set("delete", "false")
                    if model.is_hide_duplicate:
                        list_node.set("duplicate", "false")
        return tree

    def _process_kanban_access(self, tree, model_access_records, role_management,
                               current_model):
        """Process kanban view access restrictions."""
        for kanban_node in tree.xpath('//kanban'):
            if role_management.is_readonly:
                kanban_node.set("edit", "false")
                kanban_node.set("create", "false")
            for model in model_access_records:
                if current_model == model.model_id.model:
                    if model.is_model_readonly:
                        kanban_node.set("edit", "false")
                        kanban_node.set("create", "false")
                    if model.is_hide_create:
                        kanban_node.set("create", "false")
        return tree
