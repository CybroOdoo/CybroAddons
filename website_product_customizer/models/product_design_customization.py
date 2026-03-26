# -- coding: utf-8 --
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys(<https://www.cybrosys.com>)
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

import json

from odoo import api, fields, models


class ProductDesignCustomization(models.Model):
    """Model that stores the customer's final design data and order state."""
    _name = 'product.design.customization'
    _description = 'Product Design Customization'
    _order = 'create_date desc'

    name = fields.Char(
        string="Design Reference",
        required=True,
        copy=False,
        default='New',
        help="Unique auto-generated reference number for this design (e.g., 'DSN/2026/0001'). "
             "Used to track and identify customer designs across orders and production."
    )
    partner_id = fields.Many2one(
        'res.partner',
        string="Customer",
        help="The customer who created this design. Automatically set to the logged-in user. "
             "For guest/public users, this may be empty until checkout."
    )
    session_id = fields.Char(
        string="Session ID",
        help="Browser session ID for anonymous/guest users. Used to retrieve designs before login."
    )
    product_tmpl_id = fields.Many2one(
        'product.template',
        string="Product",
        required=True,
        help="The product template being customized. "
             "Example: 'Premium Business Cards', 'Custom Outdoor Banner'."
    )
    product_id = fields.Many2one(
        'product.product',
        string="Product Variant",
        help="Specific product variant if the product has variants (e.g., color/size combinations). "
             "May be empty if the product has no variants."
    )
    design_template_id = fields.Many2one(
        'product.design.template',
        string="Starting Template",
        help="The pre-designed template the customer started from (if any). "
             "Helps track template popularity and customer preferences."
    )

    quantity = fields.Integer(
        string="Quantity",
        default=1,
        help="Number of units the customer wants to order with this design."
    )

    # Design data — stores the complete customer design as JSON
    # -------------------------------------------------------------------------
    # PURPOSE: This field stores the customer's final design exactly as they
    # configured it in the frontend designer. It captures every object's text,
    # formatting, image data, and position. This JSON is used to:
    # 1. Reproduce the design in the backend for review/approval
    # 2. Generate print-ready files for production
    # 3. Allow customers to re-edit their saved designs
    #
    # EXAMPLE JSON:
    # {
    #     "objects": [
    #         {
    #             "type": "i-text",
    #             "text": "Jane Doe",
    #             "fontFamily": "Montserrat",
    #             "fontSize": 28,
    #             "fill": "#1E293B",
    #             "textAlign": "center",
    #             "fontWeight": "bold",
    #             "fontStyle": "normal",
    #             "underline": false,
    #             "left": 120,
    #             "top": 80
    #         },
    #         {
    #             "type": "image",
    #             "src": "data:image/png;base64,iVBORw0KGgo...",
    #             "left": 50,
    #             "top": 30,
    #             "scaleX": 0.5,
    #             "scaleY": 0.5
    #         }
    #     ]
    # }
    # -------------------------------------------------------------------------
    design_json = fields.Text(
        string="Design Data (JSON)",
        help="Complete customer design stored as JSON. Contains all canvas objects "
             "including text, formatting, images, and positions. See source code for format details."
    )
    preview_image = fields.Binary(
        string="Design Preview (Front)",
        attachment=True,
        help="Screenshot or rendered preview of the front side design. "
             "Displayed in the backend and on the customer's order confirmation."
    )
    preview_image_back = fields.Binary(
        string="Design Preview (Back)",
        attachment=True,
        help="Screenshot or rendered preview of the back side design. "
             "Only used for two-sided (front/back) products."
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('saved', 'Saved'),
        ('ordered', 'Ordered'),
        ('approved', 'Approved'),
        ('in_production', 'In Production'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string="Status", default='draft',
        help="Current stage of this design in the workflow:\n"
             "- Draft: Customer is still working on the design\n"
             "- Saved: Customer saved but hasn't ordered yet\n"
             "- Ordered: Added to cart and order placed\n"
             "- Approved: Design reviewed and approved for production\n"
             "- In Production: Currently being manufactured\n"
             "- Completed: Production finished and shipped\n"
             "- Cancelled: Design was cancelled"
    )

    sale_order_line_id = fields.Many2one(
        'sale.order.line',
        string="Sale Order Line",
        help="The sale order line this design is linked to. "
             "Set automatically when the customer adds the designed product to their cart."
    )
    customization_line_ids = fields.One2many(
        'product.design.customization.line',
        'customization_id',
        string="Design Elements",
        help="Individual customization details for each design element. "
             "Each line represents one text or image object's content and styling."
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to assign a unique sequence number to new designs."""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'product.design.customization') or 'New'
        return super().create(vals_list)


class ProductDesignCustomizationLine(models.Model):
    """Model for tracking individual elements (text/image) within a design customization."""
    _name = 'product.design.customization.line'
    _description = 'Product Design Customization Line'

    customization_id = fields.Many2one(
        'product.design.customization',
        string="Customization",
        required=True,
        ondelete='cascade',
        help="The parent customization record this line belongs to."
    )

    custom_text = fields.Text(
        string="Custom Text",
        help="The text content the customer entered for this element. "
             "Example: 'John Smith', 'Call us at 555-0123'."
    )
    custom_image = fields.Binary(
        string="Custom Image",
        attachment=True,
        help="The image the customer uploaded for this element (e.g., company logo, photo)."
    )
    font_family = fields.Char(
        string="Font Family",
        help="The font the customer selected for text in this element. "
             "Example: 'Montserrat', 'Arial', 'Playfair Display'."
    )
    font_size = fields.Integer(
        string="Font Size (px)",
        help="The font size in pixels the customer chose. Example: 28 for names, 14 for fine print."
    )
    font_color = fields.Char(
        string="Font Color",
        help="The text color in hex format. Example: '#000000' (black), '#FFFFFF' (white)."
    )
    text_alignment = fields.Selection([
        ('left', 'Left'),
        ('center', 'Center'),
        ('right', 'Right'),
    ], string="Text Alignment",
        help="How the text is aligned within the element: left, center, or right."
    )
    is_bold = fields.Boolean(
        string="Bold",
        help="Whether the customer applied bold formatting to the text."
    )
    is_italic = fields.Boolean(
        string="Italic",
        help="Whether the customer applied italic formatting to the text."
    )
    is_underline = fields.Boolean(
        string="Underline",
        help="Whether the customer applied underline formatting to the text."
    )
    pos_x = fields.Float(
        string="Position X (%)",
        help="Horizontal position of the element, as moved by the customer via drag & drop (0-100%%)."
    )
    pos_y = fields.Float(
        string="Position Y (%)",
        help="Vertical position of the element, as moved by the customer via drag & drop (0-100%)."
    )
    custom_width = fields.Float(
        string="Width",
        help="Width of the element in pixels."
    )
    custom_height = fields.Float(
        string="Height",
        help="Height of the element in pixels."
    )
    custom_rotation = fields.Float(
        string="Rotation",
        help="Rotation angle of the element in degrees."
    )
