# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Henna Mehjabin (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC
#    LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import re

from lxml import etree

from odoo import api, fields, models

# Field names must be valid PostgreSQL identifiers of at most 63 characters.
_MAX_FIELD_NAME_LENGTH = 63


class ProductPriceList(models.Model):
    """ Inherit product pricelist to add field for showing the pricelist in
    product tree view. """
    _inherit = 'product.pricelist'

    is_show_product_pricelist = fields.Boolean(
        string='Show the pricelist in product view', default=False,
        groups='product.group_product_pricelist',
        help='If set then product pricelist could be seen as a field in product and product variant')

    # ── Naming helpers ─────────────────────────────────────────────────────

    def _get_dynamic_label(self):
        """Return the pricelist name used for the generated field label and
        view name. The source (en_US) value is used so that users working in
        another language resolve the same field and view."""
        self.ensure_one()
        return self.with_context(lang='en_US').name.replace(" ", "_")

    def _build_pricelist_field_name(self, prefix_type):
        """Return a valid technical name for the dynamic field.

        Characters not allowed in a column name are replaced with '_', a name
        starting with a digit gets a leading '_' (so it can't be confused
        with a longer pricelist id), and the result is limited to 63
        characters."""
        self.ensure_one()
        label = re.sub(r'\W', '_', self._get_dynamic_label(), flags=re.ASCII)
        if label[:1].isdigit():
            label = f'_{label}'
        return f'x_{prefix_type}{self.id}{label}'[:_MAX_FIELD_NAME_LENGTH]

    def _get_pricelist_field(self, prefix_type, model_id):
        """Find the dynamic field created for this pricelist."""
        self.ensure_one()
        field_model = self.env['ir.model.fields'].sudo()
        field = field_model.search([
            ('model_id', '=', model_id),
            ('name', '=', self._build_pricelist_field_name(prefix_type)),
        ], limit=1)
        if not field:
            # The pricelist may have been renamed since the field was
            # created: look for a field of this pricelist id. A suffix
            # starting with a digit belongs to another pricelist (e.g. id 1
            # vs id 12).
            target_prefix = f'x_{prefix_type}{self.id}'
            candidate_fields = field_model.search([
                ('model_id', '=', model_id),
                ('name', '=like', f'{target_prefix}%'),
            ])
            for candidate in candidate_fields:
                if not candidate.name.startswith(target_prefix):
                    continue
                suffix = candidate.name[len(target_prefix):]
                if not suffix or not suffix[0].isdigit():
                    field = candidate
                    break
        return field

    @api.model
    def _view_shows_field(self, view, field_name):
        """Return True if the view arch contains the given field."""
        try:
            arch = etree.fromstring((view.arch_db or '').encode())
        except etree.XMLSyntaxError:
            return False
        return bool(arch.xpath('//field[@name=$name]', name=field_name))

    def _get_pricelist_views(self, field):
        """Return every generated view (active or archived) displaying the
        given dynamic field. Views are identified by the field they show
        rather than by their name, so renamed pricelists and pricelists
        sharing a name are handled correctly."""
        views = self.env['ir.ui.view'].sudo().with_context(active_test=False)
        if not field:
            return views.browse()
        return views.search([
            ('model', '=', field.model),
            ('mode', '=', 'extension'),
            ('arch_db', 'like', field.name),
        ]).filtered(lambda view: self._view_shows_field(view, field.name))

    def _ensure_pricelist_view(self, field, inherit_xmlid):
        """Make sure exactly one active list view displays the field."""
        self.ensure_one()
        view_name = f'product.dynamic.fields.{self._get_dynamic_label()}'
        views = self._get_pricelist_views(field).sorted(
            lambda view: not view.active)
        if views:
            view, duplicates = views[0], views[1:]
            if duplicates:
                # Left over by earlier versions of the module.
                duplicates.unlink()
            vals = {}
            if not view.active:
                vals['active'] = True
            if view.name != view_name:
                vals['name'] = view_name
            if vals:
                view.write(vals)
            return view
        arch_base = (
            '<?xml version="1.0"?>'
            '<data>'
            '<field name="standard_price" position="after" '
            'groups="dynamic_product_pricelist.group_show_sale_pricelist">'
            '<field name="%s" />'
            '</field>'
            '</data>') % field.name
        return self.env['ir.ui.view'].sudo().create({
            'name': view_name,
            'type': 'list',
            'model': field.model,
            'mode': 'extension',
            'inherit_id': self.env.ref(inherit_xmlid).id,
            'arch_base': arch_base,
            'active': True,
        })

    def _create_pricelist_field(self, prefix_type, model_id):
        """Create the dynamic float field of this pricelist."""
        self.ensure_one()
        return self.env['ir.model.fields'].sudo().create({
            'name': self._build_pricelist_field_name(prefix_type),
            'field_description': self._get_dynamic_label(),
            'model_id': model_id,
            'ttype': 'float',
        })

    def _get_pricelist_fields(self):
        """Return the (template, variant) dynamic fields of this pricelist."""
        self.ensure_one()
        field_tmpl = self._get_pricelist_field(
            'temp_', self.env.ref('product.model_product_template').id)
        field_var = self._get_pricelist_field(
            'variant_', self.env.ref('product.model_product_product').id)
        return field_tmpl, field_var

    # ── Price values ───────────────────────────────────────────────────────

    def _get_dynamic_price_models(self):
        """Return template/variant models that ignore record rules and
        include archived records, so that stale prices are always found
        and reset (archived products, other companies, etc.)."""
        tmpl_model = self.env['product.template'].sudo().with_context(
            active_test=False)
        var_model = self.env['product.product'].sudo().with_context(
            active_test=False)
        return tmpl_model, var_model

    def _reset_dynamic_pricelist_values(self, field_tmpl, field_var):
        """Set the pricelist column back to 0.0 on every product that
        currently holds a non-zero value."""
        tmpl_model, var_model = self._get_dynamic_price_models()
        if field_tmpl:
            stale_templates = tmpl_model.search([(field_tmpl.name, '!=', 0.0)])
            if stale_templates:
                stale_templates.write({field_tmpl.name: 0.0})
        if field_var:
            stale_variants = var_model.search([(field_var.name, '!=', 0.0)])
            if stale_variants:
                stale_variants.write({field_var.name: 0.0})

    def check_pricelist_condition(self):
        """ Displays the pricelist in product view and product variant view. """
        for pricelist in self:
            pricelist._compute_dynamic_pricelist_fields()

    def _compute_dynamic_pricelist_fields(self):
        self.ensure_one()

        # ── 1. Product template field & view ───────────────────────────
        model_tmpl_id = self.env.ref('product.model_product_template').id
        field_tmpl = self._get_pricelist_field('temp_', model_tmpl_id)
        if not field_tmpl:
            field_tmpl = self._create_pricelist_field('temp_', model_tmpl_id)
        self._ensure_pricelist_view(
            field_tmpl, 'product.product_template_tree_view')

        # ── 2. Product variant field & view (if variant rules exist or present) ─
        model_var_id = self.env.ref('product.model_product_product').id
        field_var = self._get_pricelist_field('variant_', model_var_id)
        has_variant_rules = any(r.applied_on == '0_product_variant' for r in self.item_ids)
        if has_variant_rules and not field_var:
            field_var = self._create_pricelist_field('variant_', model_var_id)
        if field_var:
            self._ensure_pricelist_view(
                field_var, 'product.product_product_tree_view')

        # ── 3. Reset ALL stale prices in product.template & product.product ────
        # Uses sudo + active_test=False so archived products and products of
        # other companies (blocked by record rules) are reset as well.
        # This guarantees that switching rule type (category -> product, or
        # between categories/products, or deleting rules) clears products that
        # no longer match.
        self._reset_dynamic_pricelist_values(field_tmpl, field_var)

        if not self.item_ids:
            return

        # ── 4. Apply active rules in order of precedence ──────────────────────
        # Global (1) -> Category (2) -> Product (3) -> Variant (4)
        tmpl_model, var_model = self._get_dynamic_price_models()

        def rule_priority(item):
            if item.applied_on == '3_global':
                return 1
            elif item.applied_on == '2_product_category':
                return 2
            elif item.applied_on == '1_product':
                return 3
            elif item.applied_on == '0_product_variant':
                return 4
            return 0

        for rec in self.item_ids.sorted(key=rule_priority):
            if rec.applied_on == '3_global':
                templates = tmpl_model.search([])
                if templates:
                    self._apply_rule_to_templates(
                        rec, templates, field_tmpl, field_var)
            elif rec.applied_on == '2_product_category':
                if rec.categ_id:
                    templates = tmpl_model.search([
                        ('categ_id', 'child_of', rec.categ_id.id)
                    ])
                    if templates:
                        self._apply_rule_to_templates(
                            rec, templates, field_tmpl, field_var)
            elif rec.applied_on == '1_product':
                if rec.product_tmpl_id:
                    tmpl = rec.product_tmpl_id.sudo()
                    price = (rec.fixed_price if rec.compute_price == 'fixed'
                             else self._get_product_price(tmpl, 1.0))
                    tmpl.write({field_tmpl.name: price})
                    if field_var and tmpl.product_variant_ids:
                        tmpl.product_variant_ids.write({field_var.name: price})
            elif rec.applied_on == '0_product_variant':
                if rec.product_id:
                    variant = rec.product_id.sudo()
                    price = (rec.fixed_price if rec.compute_price == 'fixed'
                             else self._get_product_price(variant, 1.0))
                    if field_var:
                        variant.write({field_var.name: price})
                    if variant.product_tmpl_id:
                        variant.product_tmpl_id.write({field_tmpl.name: price})

    def _apply_rule_to_templates(self, rec, templates, field_tmpl, field_var):
        """Write the price of a global/category rule on the given templates,
        and on their variants when the variant column exists."""
        if rec.compute_price == 'fixed':
            templates.write({field_tmpl.name: rec.fixed_price})
            if field_var:
                templates.product_variant_ids.write(
                    {field_var.name: rec.fixed_price})
        else:
            for tmpl in templates:
                price = self._get_product_price(tmpl, 1.0)
                tmpl.write({field_tmpl.name: price})
                if field_var and tmpl.product_variant_ids:
                    tmpl.product_variant_ids.write({field_var.name: price})

    # ── Hide / remove ──────────────────────────────────────────────────────

    def _hide_pricelist_in_product_view(self):
        """Deactivate views and reset field values when pricelist view is disabled."""
        for rec in self:
            field_tmpl, field_var = rec._get_pricelist_fields()
            views = (rec._get_pricelist_views(field_tmpl)
                     | rec._get_pricelist_views(field_var))
            active_views = views.filtered('active')
            if active_views:
                active_views.write({'active': False})
            rec._reset_dynamic_pricelist_values(field_tmpl, field_var)

    def _remove_dynamic_pricelist_columns(self):
        """Delete the generated views and fields of these pricelists only.
        Views (active or archived) are removed first so that the fields are
        no longer referenced when they are deleted."""
        views = self.env['ir.ui.view'].sudo()
        dynamic_fields = self.env['ir.model.fields'].sudo()
        for rec in self:
            for field in rec._get_pricelist_fields():
                if field:
                    dynamic_fields |= field
                    views |= rec._get_pricelist_views(field)
        if views:
            views.unlink()
        if dynamic_fields:
            dynamic_fields.unlink()

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for rec in res.filtered(lambda pl: pl.is_show_product_pricelist):
            rec.check_pricelist_condition()
        return res

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            if 'is_show_product_pricelist' in vals and not rec.is_show_product_pricelist:
                rec._hide_pricelist_in_product_view()
            elif rec.is_show_product_pricelist:
                rec.check_pricelist_condition()
        return res

    def unlink(self):
        """Override to remove generated fields and views when a pricelist is deleted."""
        self._remove_dynamic_pricelist_columns()
        return super().unlink()


class ProductPricelistItem(models.Model):
    """Override pricelist item to refresh the product column whenever a rule
    is saved, created, or deleted."""
    _inherit = 'product.pricelist.item'

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        pricelists = res.mapped('pricelist_id').filtered(
            lambda pl: pl.is_show_product_pricelist)
        for pricelist in pricelists:
            pricelist.check_pricelist_condition()
        return res

    def write(self, vals):
        old_pricelists = self.mapped('pricelist_id').filtered(
            lambda pl: pl.is_show_product_pricelist)
        res = super().write(vals)
        new_pricelists = self.mapped('pricelist_id').filtered(
            lambda pl: pl.is_show_product_pricelist)
        for pricelist in (old_pricelists | new_pricelists):
            pricelist.check_pricelist_condition()
        return res

    def unlink(self):
        pricelists = self.mapped('pricelist_id').filtered(
            lambda pl: pl.is_show_product_pricelist)
        res = super().unlink()
        for pricelist in pricelists:
            pricelist.check_pricelist_condition()
        return res