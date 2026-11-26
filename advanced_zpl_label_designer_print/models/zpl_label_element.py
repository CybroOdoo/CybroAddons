# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
from odoo import fields, models

class ZplLabelElement(models.Model):
    _name = 'zpl.label.element'
    _description = 'ZPL Label Element'
    _order = 'sequence'

    template_id = fields.Many2one(
        'zpl.label.template', ondelete='cascade',
        required=True, help="ZPL label template this element belongs to.")
    sequence = fields.Integer(
        default=10,
        help="Determines the order in which elements are drawn on the label.")
    name = fields.Char(
        required=True,
        help="Label/name of the element shown in the designer, and used as "
             "fallback text when no Odoo field is configured.")
    type = fields.Selection([
        ('text', 'Text'),
        ('barcode', 'Barcode'),
        ('qrcode', 'QR Code'),
        ('image', 'Image'),
        ('line', 'Line'),
        ('rect', 'Rectangle')
    ], default='text', required=True,
        help="Kind of element to draw on the label (text, barcode, QR code, "
             "image, line or rectangle).")

    x_pos = fields.Integer(
        string='X Position', default=0,
        help="Horizontal position of the element on the design canvas, in "
             "pixels from the left edge.")
    y_pos = fields.Integer(
        string='Y Position', default=0,
        help="Vertical position of the element on the design canvas, in "
             "pixels from the top edge.")
    width = fields.Integer(
        default=100,
        help="Width of the element on the design canvas, in pixels.")
    height = fields.Integer(
        default=50,
        help="Height of the element on the design canvas, in pixels.")
    thickness = fields.Integer(
        default=2,
        help="Line thickness used when drawing rectangle/line elements.")
    rounding = fields.Integer(
        default=0,
        help="Corner rounding radius used when drawing rectangle elements.")

    font_size = fields.Integer(
        default=20,
        help="Font size for text elements, or bar height for barcode "
             "elements.")
    rotation = fields.Selection([
        ('0', '0°'),
        ('90', '90°'),
        ('180', '180°'),
        ('270', '270°')
    ], default='0',
        help="Rotation angle applied to the element when printed.")

    model_id = fields.Many2one(
        'ir.model', related='template_id.model_id',
        readonly=True,
        help="Model configured on the parent template, used to restrict "
             "the Odoo Field selection below.")
    field_id = fields.Many2one('ir.model.fields', string='Odoo Field', ondelete='cascade', domain="[('model_id', '=', model_id)]", help="The Odoo field to pull data from (e.g., default_code for barcode)")
    data_format = fields.Char(help="A string placeholder like Price: {{price}}")

    barcode_type = fields.Selection([
        ('code128', 'Code 128'),
        ('code39', 'Code 39'),
        ('ean13', 'EAN 13'),
        ('upca', 'UPC-A')
    ], help="Barcode symbology to use when the element type is Barcode.")

    active = fields.Boolean(
        default=True,
        help="Uncheck to hide the element without deleting it.")
