# -- coding: utf-8 --
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class ProductProduct(models.Model):
    """Extends product.product (variant) with variant-specific design fields.

    Follows Odoo's image_variant pattern: variant-specific stored fields with
    computed fallback fields that return variant value when set, otherwise
    falling back to the product template value.
    """
    _inherit = 'product.product'

    # -------------------------------------------------------------------------
    # Variant-specific design images (stored on variant)
    # Same pattern as Odoo core's image_variant_1920 / image_1920
    # -------------------------------------------------------------------------
    design_base_image_variant = fields.Image(
        "Variant Design Base Image (Front)",
        max_width=1920, max_height=1920,
        help="Variant-specific front design image. When set, this overrides "
             "the template's design base image for this variant.",
    )
    design_base_image_back_variant = fields.Image(
        "Variant Design Base Image (Back)",
        max_width=1920, max_height=1920,
        help="Variant-specific back design image. When set, this overrides "
             "the template's back design base image for this variant.",
    )

    design_base_image = fields.Image(
        "Design Base Image (Front)",
        compute='_compute_design_base_image',
    )
    design_base_image_back = fields.Image(
        "Design Base Image (Back)",
        compute='_compute_design_base_image_back',
    )

    # -------------------------------------------------------------------------
    # Variant design settings override
    # -------------------------------------------------------------------------
    has_design_variant_override = fields.Boolean(
        "Override Template Design Settings",
        default=False,
        help="When enabled, this variant uses its own design area, limits, "
             "colors, fonts, and instructions instead of the template defaults.",
    )

    # Variant-specific design area (front)
    variant_design_area_left = fields.Float("Design Area Left (%)", default=0.0)
    variant_design_area_top = fields.Float("Design Area Top (%)", default=0.0)
    variant_design_area_width = fields.Float("Design Area Width (%)", default=100.0)
    variant_design_area_height = fields.Float("Design Area Height (%)", default=100.0)

    # Variant-specific design area (back)
    variant_design_area_back_left = fields.Float("Back Design Area Left (%)", default=0.0)
    variant_design_area_back_top = fields.Float("Back Design Area Top (%)", default=0.0)
    variant_design_area_back_width = fields.Float("Back Design Area Width (%)", default=100.0)
    variant_design_area_back_height = fields.Float("Back Design Area Height (%)", default=100.0)

    # Variant-specific settings
    has_variant_front_back = fields.Boolean("Two-Sided Design")
    variant_design_instruction = fields.Html("Design Instructions", translate=True)
    variant_design_max_texts = fields.Integer("Max Text Objects", default=0)
    variant_design_max_images = fields.Integer("Max Image Objects", default=0)
    variant_design_max_characters = fields.Integer("Max Characters per Text", default=25)
    variant_min_order_quantity = fields.Integer("Minimum Order Quantity", default=1)
    variant_max_order_quantity = fields.Integer("Maximum Order Quantity", default=10000)
    variant_production_time_days = fields.Integer("Production Time (Days)", default=3)
    variant_shipping_weight_per_unit = fields.Float("Shipping Weight per Unit (kg)", default=0.1)

    # Variant-specific fonts & colors
    variant_design_font_ids = fields.Many2many(
        'product.design.font',
        'product_variant_design_font_rel',
        'product_id', 'font_id',
        string="Allowed Fonts",
    )
    variant_design_bg_color_ids = fields.Many2many(
        'product.design.color',
        'product_variant_bg_color_rel',
        'product_id', 'color_id',
        string="Background Colors",
    )
    variant_design_text_color_ids = fields.Many2many(
        'product.design.color',
        'product_variant_text_color_rel',
        'product_id', 'color_id',
        string="Text Colors",
    )

    # -------------------------------------------------------------------------
    # Computed image fields
    # -------------------------------------------------------------------------
    @api.depends('design_base_image_variant', 'product_tmpl_id.design_base_image')
    def _compute_design_base_image(self):
        """Use variant image when set, otherwise fall back to template."""
        for record in self:
            record.design_base_image = (
                record.design_base_image_variant
                or record.product_tmpl_id.design_base_image
            )

    @api.depends('design_base_image_back_variant', 'product_tmpl_id.design_base_image_back')
    def _compute_design_base_image_back(self):
        """Use variant back image when set, otherwise fall back to template."""
        for record in self:
            record.design_base_image_back = (
                record.design_base_image_back_variant
                or record.product_tmpl_id.design_base_image_back
            )

    # -------------------------------------------------------------------------
    # Helper: effective design configuration
    # -------------------------------------------------------------------------
    def _get_design_config(self):
        """Return the effective design configuration for this variant.

        When ``has_design_variant_override`` is True, variant-specific values are
        returned.  Otherwise, the product template's values are used as the
        fallback — which is the normal case for products with no variants or
        when no per-variant customisation is needed.
        """
        self.ensure_one()
        tmpl = self.product_tmpl_id

        if self.has_design_variant_override:
            fonts = self.variant_design_font_ids
            bg_colors = self.variant_design_bg_color_ids
            text_colors = self.variant_design_text_color_ids
            return {
                'has_front_back': self.has_variant_front_back,
                'design_area_left': self.variant_design_area_left,
                'design_area_top': self.variant_design_area_top,
                'design_area_width': self.variant_design_area_width,
                'design_area_height': self.variant_design_area_height,
                'design_area_back_left': self.variant_design_area_back_left,
                'design_area_back_top': self.variant_design_area_back_top,
                'design_area_back_width': self.variant_design_area_back_width,
                'design_area_back_height': self.variant_design_area_back_height,
                'design_instruction': self.variant_design_instruction,
                'design_max_texts': self.variant_design_max_texts,
                'design_max_images': self.variant_design_max_images,
                'design_max_characters': self.variant_design_max_characters,
                'min_order_quantity': self.variant_min_order_quantity,
                'max_order_quantity': self.variant_max_order_quantity,
                'production_time_days': self.variant_production_time_days,
                'shipping_weight_per_unit': self.variant_shipping_weight_per_unit,
                'design_font_ids': fonts,
                'design_bg_color_ids': bg_colors,
                'design_text_color_ids': text_colors,
            }

        # Default: inherit from template
        return {
            'has_front_back': tmpl.has_front_back,
            'design_area_left': tmpl.design_area_left,
            'design_area_top': tmpl.design_area_top,
            'design_area_width': tmpl.design_area_width,
            'design_area_height': tmpl.design_area_height,
            'design_area_back_left': tmpl.design_area_back_left,
            'design_area_back_top': tmpl.design_area_back_top,
            'design_area_back_width': tmpl.design_area_back_width,
            'design_area_back_height': tmpl.design_area_back_height,
            'design_instruction': tmpl.design_instruction,
            'design_max_texts': tmpl.design_max_texts,
            'design_max_images': tmpl.design_max_images,
            'design_max_characters': tmpl.design_max_characters,
            'min_order_quantity': tmpl.min_order_quantity,
            'max_order_quantity': tmpl.max_order_quantity,
            'production_time_days': tmpl.production_time_days,
            'shipping_weight_per_unit': tmpl.shipping_weight_per_unit,
            'design_font_ids': tmpl.design_font_ids,
            'design_bg_color_ids': tmpl.design_bg_color_ids,
            'design_text_color_ids': tmpl.design_text_color_ids,
        }