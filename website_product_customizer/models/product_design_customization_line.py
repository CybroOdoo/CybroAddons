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
