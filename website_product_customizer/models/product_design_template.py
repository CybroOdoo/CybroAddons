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
from odoo import fields, models


class ProductDesignTemplate(models.Model):
    """Model representing a pre-designed template that customers can start from."""
    _name = 'product.design.template'
    _description = 'Product Design Template'
    _order = 'usage_count desc, name'

    name = fields.Char(
        string="Template Name",
        required=True,
        translate=True,
        help="Display name for this pre-designed template. Shown to customers in template picker. "
             "Example: 'Modern Blue Business Card', 'Bold Event Banner', 'Minimalist Logo Tee'."
    )
    preview_image = fields.Binary(
        string="Preview Image (Front)",
        attachment=True,
        help="Thumbnail preview of the front side template design. Shown in the template gallery. "
             "Recommended: 600x400px, high quality PNG or JPEG."
    )
    preview_image_back = fields.Binary(
        string="Preview Image (Back)",
        attachment=True,
        help="Thumbnail preview of the back side template design. "
             "Only used for two-sided (front/back) product templates."
    )
    product_tmpl_id = fields.Many2one(
        'product.template',
        string="Specific Product",
        help="If set, this template is only available for this specific product. "
             "Leave empty to make the template available for all products in the same category."
    )
    design_category_id = fields.Many2one(
        'product.public.category',
        string="Design Category",
        help="The design category this template belongs to. "
             "If no specific product is set, the template is available for all products in this category."
    )
    design_data = fields.Text(
        string="Design Data (JSON)",
        help="Full template layout stored as JSON. Contains canvas object positions, text content, "
             "font settings, colors, and image data. See the example in the source code comments."
    )

    # Template metadata
    template_style = fields.Selection([
        ('modern', 'Modern'),
        ('classic', 'Classic'),
        ('minimalist', 'Minimalist'),
        ('bold', 'Bold'),
        ('elegant', 'Elegant'),
        ('playful', 'Playful'),
        ('corporate', 'Corporate'),
        ('creative', 'Creative'),
    ], string="Design Style", default='modern',
        help="Visual style classification for filtering templates:\n"
             "- Modern: Clean lines, flat design, contemporary fonts\n"
             "- Classic: Traditional layouts, serif fonts, timeless feel\n"
             "- Minimalist: Lots of whitespace, simple typography\n"
             "- Bold: Strong colors, large text, high contrast\n"
             "- Elegant: Script fonts, subtle colors, luxury feel\n"
             "- Corporate: Professional, structured, brand-focused"
    )
    color_primary = fields.Char(
        string="Primary Color",
        default='#1E40AF',
        help="Main color used in this template (hex format). "
             "Used for filtering templates by color scheme. Example: '#1E40AF' (blue)."
    )
    color_secondary = fields.Char(
        string="Secondary Color",
        default='#F59E0B',
        help="Accent color used in this template (hex format). "
             "Example: '#F59E0B' (amber), '#10B981' (green)."
    )
    tag_ids = fields.Many2many(
        'product.design.template.tag',
        string="Tags",
        help="Tags for categorizing and filtering templates. "
             "Example: 'Professional', 'Colorful', 'Photo-based', 'Text-focused'."
    )
    usage_count = fields.Integer(
        string="Times Used",
        default=0,
        readonly=True,
        help="Number of times customers have selected this template. "
             "Automatically incremented. Used for sorting popular templates first."
    )
    is_premium = fields.Boolean(
        string="Premium Template",
        default=False,
        help="If checked, this template may require a subscription or extra payment. "
             "Premium templates appear with a special badge in the gallery."
    )
    active = fields.Boolean(
        string="Active",
        default=True,
        help="If unchecked, this template is hidden from the template gallery."
    )
