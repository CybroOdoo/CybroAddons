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


class ProductTemplate(models.Model):
    """Extends product.template to enable product customization with a
    Fabric.js canvas designer, supporting text, images, fonts and colors."""
    _inherit = 'product.template'

    # Designer fields
    is_designable = fields.Boolean(
        string="Designable Product",
        default=False,
        help="If checked, customers can customize this product using the online designer. "
             "A 'Customize & Design' button will appear on the product page."
    )
    design_category_id = fields.Many2one(
        'product.public.category',
        string="Design Category",
        ondelete='set null',
        index=True,
        help="Assign this product to a design category for browsing and organization. "
             "Example: 'Business Cards', 'Banners', 'Apparel'. "
             "Categories appear on the /shop/designer page for customers to browse."
    )

    # Fonts & Colors
    design_font_ids = fields.Many2many(
        'product.design.font',
        string="Allowed Fonts",
        help="Specific fonts customers are allowed to use when customizing this product. "
             "Leave this blank if you want ALL activated system fonts to be available."
    )
    design_bg_color_ids = fields.Many2many(
        'product.design.color',
        'product_template_bg_color_rel',
        'product_tmpl_id',
        'color_id',
        string="Background Colors",
        help="Colors available to the customer for filling the design area background. "
             "Leave blank to disable background color selection."
    )
    design_text_color_ids = fields.Many2many(
        'product.design.color',
        'product_template_text_color_rel',
        'product_tmpl_id',
        'color_id',
        string="Text Colors",
        help="Colors available to the customer for text. "
             "Leave blank to show a free color picker instead."
    )

    # Design templates
    design_template_ids = fields.One2many(
        'product.design.template',
        'product_tmpl_id',
        string="Design Templates",
        help="Pre-designed starting templates customers can choose and customize. "
             "Templates pre-fill the canvas with sample text, images, and styling. "
             "Good templates increase conversion rates."
    )

    # Design Area Configuration (boundaries on the base image)
    design_area_left = fields.Float(
        string="Design Area Left (%)",
        default=0.0,
        help="The left offset of the customizable area relative to the base image width, "
             "expressed as a percentage (0 to 100). Default is 0."
    )
    design_area_top = fields.Float(
        string="Design Area Top (%)",
        default=0.0,
        help="The top offset of the customizable area relative to the base image height, "
             "expressed as a percentage (0 to 100). Default is 0."
    )
    design_area_width = fields.Float(
        string="Design Area Width (%)",
        default=100.0,
        help="The width of the customizable area relative to the base image width, "
             "expressed as a percentage (0 to 100). Default is 100."
    )
    design_area_height = fields.Float(
        string="Design Area Height (%)",
        default=100.0,
        help="The height of the customizable area relative to the base image height, "
             "expressed as a percentage (0 to 100). Default is 100."
    )

    # Back-side Design Area Configuration
    design_area_back_left = fields.Float(
        string="Back Design Area Left (%)",
        default=0.0,
        help="The left offset of the back-side customizable area relative to the base image width, "
             "expressed as a percentage (0 to 100). Only used when Two-Sided Design is enabled."
    )
    design_area_back_top = fields.Float(
        string="Back Design Area Top (%)",
        default=0.0,
        help="The top offset of the back-side customizable area relative to the base image height, "
             "expressed as a percentage (0 to 100). Only used when Two-Sided Design is enabled."
    )
    design_area_back_width = fields.Float(
        string="Back Design Area Width (%)",
        default=100.0,
        help="The width of the back-side customizable area relative to the base image width, "
             "expressed as a percentage (0 to 100). Only used when Two-Sided Design is enabled."
    )
    design_area_back_height = fields.Float(
        string="Back Design Area Height (%)",
        default=100.0,
        help="The height of the back-side customizable area relative to the base image height, "
             "expressed as a percentage (0 to 100). Only used when Two-Sided Design is enabled."
    )

    # Design product image (the base image for the designer canvas)
    design_base_image = fields.Image(
        string="Design Base Image (Front)",
        help="The product image used as the background canvas in the designer (front side). "
             "Should clearly show the product with defined printable areas. "
             "If not set, the main product image (image_1920) will be used instead."
    )
    design_base_image_back = fields.Image(
        string="Design Base Image (Back)",
        help="Back side product image for two-sided designs. "
             "Only used when 'Two-Sided Design' is enabled. Shows the reverse of the product."
    )

    # Design settings
    has_front_back = fields.Boolean(
        string="Two-Sided Design",
        default=False,
        help="Enable designing on both front and back of the product. "
             "When enabled, a Front/Back toggle appears in the designer. "
             "Make sure to upload a 'Design Base Image (Back)' as well."
    )
    design_instruction = fields.Html(
        string="Design Instructions",
        translate=True,
        help="Instructions displayed to the customer in the designer sidebar. "
             "Use this to inform about file requirements, safe areas, color modes, etc. "
             "Example: 'Ensure text is at least 5mm from edges. Use high-res images (300 DPI).'",
    )
    design_max_texts = fields.Integer(
        string="Max Text Objects",
        default=0,
        help="Maximum number of text objects a customer can add. Set to 0 for unlimited."
    )
    design_max_images = fields.Integer(
        string="Max Image Objects",
        default=0,
        help="Maximum number of images a customer can upload/add. Set to 0 for unlimited."
    )
    design_max_characters = fields.Integer(
        string="Max Characters per Text",
        default=25,
        help="Maximum number of characters allowed in a single text object. Set to 0 for unlimited."
    )
    min_order_quantity = fields.Integer(
        string="Minimum Order Quantity",
        default=1,
        help="Minimum number of units the customer must order. "
             "Example: 100 for business cards, 1 for banners. "
             "Set to 1 if there's no minimum."
    )
    max_order_quantity = fields.Integer(
        string="Maximum Order Quantity",
        default=10000,
        help="Maximum units allowed per order. Set a reasonable limit to prevent abuse. "
             "Example: 10000 for business cards, 50 for large banners."
    )
    production_time_days = fields.Integer(
        string="Production Time (Days)",
        default=3,
        help="Estimated production time in business days (excluding shipping). "
             "Displayed to customers to set expectations. "
             "Example: 2-3 days for business cards, 5-7 for large format."
    )
    shipping_weight_per_unit = fields.Float(
        string="Shipping Weight per Unit (kg)",
        default=0.1,
        help="Weight per unit in kilograms, used for shipping calculation. "
             "Example: 0.05 for 100 business cards, 0.5 for a banner, 0.2 for a t-shirt."
    )
    design_customization_ids = fields.One2many(
        'product.design.customization',
        'product_tmpl_id',
        string="Customer Designs",
        help="All customer-created designs for this product. "
             "Each record represents one customer's customization with their specific text, images, and choices."
    )

    # Computed
    design_template_count = fields.Integer(
        string="Template Count",
        compute='_compute_design_template_count',
        help="Total number of pre-designed templates available for this product."
    )

    @api.depends('design_template_ids')
    def _compute_design_template_count(self):
        """Count the design templates available for each product."""
        for product in self:
            product.design_template_count = len(product.design_template_ids)

    def action_open_designer_templates(self):
        """Open the design templates configured for this product."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Design Templates',
            'res_model': 'product.design.template',
            'view_mode': 'list,form',
            'domain': [('product_tmpl_id', '=', self.id)],
            'context': {'default_product_tmpl_id': self.id},
        }
