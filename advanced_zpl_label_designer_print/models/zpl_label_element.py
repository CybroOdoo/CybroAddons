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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
import io
import logging

from PIL import Image

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ZplLabelElement(models.Model):
    """Store one drawable element used by a ZPL label template."""

    _name = 'zpl.label.element'
    _description = 'ZPL Label Element'
    _order = 'sequence'

    template_id = fields.Many2one('zpl.label.template', ondelete='cascade', required=True)
    sequence = fields.Integer(default=10)
    name = fields.Char(required=True)
    type = fields.Selection([
        ('text', 'Text'),
        ('barcode', 'Barcode'),
        ('qrcode', 'QR Code'),
        ('image', 'Image'),
        ('line', 'Line'),
        ('rect', 'Rectangle')
    ], default='text', required=True)

    x_pos = fields.Integer(string='X Position', default=0)
    y_pos = fields.Integer(string='Y Position', default=0)
    width = fields.Integer(default=100)
    height = fields.Integer(default=50)
    thickness = fields.Integer(default=2)
    rounding = fields.Integer(default=0)

    font_size = fields.Integer(default=20)
    rotation = fields.Selection([
        ('0', '0\u00b0'),
        ('90', '90\u00b0'),
        ('180', '180\u00b0'),
        ('270', '270\u00b0')
    ], default='0')

    model_id = fields.Many2one('ir.model', related='template_id.model_id', readonly=True)
    field_id = fields.Many2one(
        'ir.model.fields', string='Odoo Field', ondelete='cascade',
        domain="[('model_id', '=', model_id)]",
        help="The Odoo field to pull data from (e.g., default_code for barcode).")
    data_format = fields.Char(help="A string placeholder like Price: {{value}}.")
    image = fields.Binary(
        attachment=True,
        help="Picture printed for elements of type Image. "
             "It is converted to black and white when the label is generated.")

    barcode_type = fields.Selection([
        ('code128', 'Code 128'),
        ('code39', 'Code 39'),
        ('ean13', 'EAN 13'),
        ('upca', 'UPC-A')
    ])

    active = fields.Boolean(default=True)

    def _get_zpl_image_command(self, width_dots, height_dots):
        """Return the ^GFA graphic field command for the element image.

        The picture is flattened on a white background, resized to the given
        size in printer dots and converted to a 1-bit bitmap, where a set bit
        is a black dot.
        """
        self.ensure_one()
        if not self.image or width_dots <= 0 or height_dots <= 0:
            return ''
        try:
            source = Image.open(io.BytesIO(self.image.content))
            if source.mode in ('RGBA', 'LA', 'P'):
                rgba = source.convert('RGBA')
                background = Image.new('RGBA', rgba.size, (255, 255, 255, 255))
                background.alpha_composite(rgba)
                source = background
            gray = source.convert('L').resize((width_dots, height_dots), Image.Resampling.LANCZOS)
        except (OSError, ValueError):
            _logger.warning("Element %s has an image that cannot be read.", self.id)
            return ''
        bitmap = gray.point(lambda value: 255 if value < 128 else 0).convert('1')
        raw = bitmap.tobytes()
        bytes_per_row = (width_dots + 7) // 8
        return f"^GFA,{len(raw)},{len(raw)},{bytes_per_row},{raw.hex().upper()}"
