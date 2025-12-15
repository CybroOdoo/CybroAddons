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
from collections import defaultdict
from lxml import etree
from lxml.builder import E
from odoo import api, models
from odoo.addons.base.models.ir_model import MODULE_UNINSTALL_FLAG


class ResGroups(models.Model):
    """Extends res.groups to dynamically generate role-based group views."""
    _inherit = 'res.groups'

    def name_boolean_group(self, id):
        """Generate boolean group field name."""
        return 'in_group_' + str(id)

    def name_selection_groups(self, ids):
        """Generate selection group field name."""
        return 'sel_groups_' + '_'.join(str(it) for it in sorted(ids))

    def is_boolean_group(name):
        """Check if the field name belongs to a boolean group."""
        return name.startswith('in_group_')

    def is_selection_groups(name):
        """Check if the field name belongs to a selection group."""
        return name.startswith('sel_groups_')

    def get_boolean_group(name):
        """Extract group ID from a boolean group field name."""
        return int(name[9:])

    def get_selection_groups(name):
        """Extract group IDs from a selection group field name."""
        return [int(v) for v in name[11:].split('_')]

    @api.model
    def _register_hook(self):
        """Hook to update role-based group view after module installation."""
        super()._register_hook()
        self._update_role_groups_view()
        return True

    @api.model
    def get_groups_by_application(self):
        """ Return all groups classified by application (module category), as a list::
                [(app, kind, groups), ...],
            where ``app`` and ``groups`` are recordsets, and ``kind`` is either
            ``'boolean'`` or ``'selection'``. Applications are given in sequence
            order.  If ``kind`` is ``'selection'``, ``groups`` are given in
            reverse implication order.
        """
        def linearize(app, gs, category_name):
            if app.xml_id == 'base.module_category_user_type':
                return (app, 'selection', gs.sorted('id'), category_name)
            order = {g: len(g.trans_implied_ids & gs) for g in gs}
            if app.xml_id == 'base.module_category_accounting_accounting':
                return (app, 'selection', gs.sorted(key=order.get), category_name)
            if len(set(order.values())) == len(gs):
                return (app, 'selection', gs.sorted(key=order.get), category_name)
            else:
                return (app, 'boolean', gs, (100, 'Other'))

        by_app, others = defaultdict(self.browse), self.browse()
        for g in self.get_application_groups([]):
            if g.category_id:
                by_app[g.category_id] += g
            else:
                others += g
        res = []
        for app, gs in sorted(by_app.items(), key=lambda it: it[0].sequence or 0):
            if app.parent_id:
                res.append(
                    linearize(app, gs, (app.parent_id.sequence, app.parent_id.name)))
            else:
                res.append(linearize(app, gs, (100, 'Other')))
        if others:
            res.append(
                (self.env['ir.module.category'], 'boolean', others, (100, 'Other')))
        return res

    @api.model
    def customize_role_group_fields(self, field_name, attrs, model_name):
        """
        Customize group field attributes for specific models.
        """
        if model_name == 'access.role' and field_name == 'sel_groups_1_10_11':
            # Hide the field but keep it in the form data
            attrs['invisible'] = '1'
            attrs['class'] = 'd-none'
        return attrs

    @api.model
    def _update_role_groups_view(self):
        """
        Modify the view with xmlid ``base.user_groups_view`` or custom view,
        introducing reified group fields with customizations.
        """
        self = self.with_context(lang=None)
        view = self.env.ref('access_roles.access_role_view_form_groups',
                            raise_if_not_found=False)

        if not (view and view._name == 'ir.ui.view'):
            return

        model_name = self._context.get('model', 'access.role') 
        if self._context.get('install_filename') or self._context.get(
                MODULE_UNINSTALL_FLAG):
            xml = E.field(name="groups_ids", position="after")
        else:
            group_no_one = self.env.ref('base.group_no_one')
            xml0, xml2, xml3, xml4 = [], [], [], []
            xml_by_category = {}
            sorted_tuples = sorted(self.get_groups_by_application(),
                                   key=lambda t: t[0].xml_id != 'base.module_category_user_type')

            invisible_information = (
                "All fields linked to groups must be present in the view "
                "due to the overwrite of create and write. "
                "The implied groups are calculated using this values.")
            for app, kind, gs, category_name in sorted_tuples:
                attrs = {}
                if kind == 'selection':
                    field_name = self.name_selection_groups(gs.ids)
                    attrs['on_change'] = '1'
                    attrs = self.customize_role_group_fields(field_name, attrs,
                                                             model_name)
                    if category_name not in xml_by_category:
                        xml_by_category[category_name] = []
                        xml_by_category[category_name].append(E.newline())
                    xml_by_category[category_name].append(
                        E.field(name=field_name, **attrs))
                    xml_by_category[category_name].append(E.newline())
                    if attrs.get('groups') == 'base.group_no_one':
                        xml0.append(E.field(name=field_name,
                                            **dict(attrs, groups='!base.group_no_one')))
                        xml0.append(etree.Comment(invisible_information))
                else:
                    app_name = app.name or 'Other'
                    xml4.append(E.separator(string=app_name, **attrs))
                    left_group, right_group = [], []
                    group_count = 0
                    for g in gs:
                        field_name = self.name_boolean_group(g.id)
                        dest_group = left_group if group_count % 2 == 0 else right_group
                        attrs = self.customize_role_group_fields(field_name, attrs,
                                                                 model_name)
                        if g == group_no_one:
                            dest_group.append(
                                E.field(name=field_name, invisible="True", **attrs))
                            dest_group.append(etree.Comment(invisible_information))
                        else:
                            dest_group.append(E.field(name=field_name, **attrs))
                        xml0.append(E.field(name=field_name,
                                            **dict(attrs, invisible="True",
                                                   groups='!base.group_no_one')))
                        xml0.append(etree.Comment(invisible_information))
                        group_count += 1
                    xml4.append(E.group(*left_group))
                    xml4.append(E.group(*right_group))
            xml4.append({'class': "o_label_nowrap"})
            for xml_cat in sorted(xml_by_category.keys(), key=lambda it: it[0]):
                master_category_name = xml_cat[1]
                xml3.append(
                    E.group(*(xml_by_category[xml_cat]), string=master_category_name))
            xml = E.field(
                *(xml0),
                E.group(*(xml2)),
                E.group(*(xml3)),
                E.group(*(xml4), groups='base.group_no_one'),
                name="groups_ids", position="replace")
            xml.addprevious(etree.Comment("GENERATED AUTOMATICALLY BY GROUPS"))
        xml_content = etree.tostring(xml, pretty_print=True, encoding="unicode")
        if xml_content != view.arch:
            new_context = dict(view._context)
            new_context.pop('install_filename', None)
            new_context['lang'] = None
            view.with_context(new_context).write({'arch': xml_content})

    def get_application_groups(self, domain):
        """Return the non-share groups that satisfy ``domain``."""
        return self.search(domain + [('share', '=', False)])
