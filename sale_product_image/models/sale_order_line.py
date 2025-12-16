# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ayana KP (<https://www.cybrosys.com>)
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
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import base64
import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

from wand.image import Image as WandImage


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    order_line_image = fields.Binary(
        string="Image",
        related="product_id.image_1920",
        help='Product Image in Sale orderLine'
    )

    image_for_report = fields.Binary(
        string='Report Image',
        compute='_compute_image_for_report',
        store=False,
        help='Product image optimized for PDF (JPEG format without transparency)'
    )

    @api.depends('product_id.image_128')
    def _compute_image_for_report(self):
        """Convert WebP to JPEG using ImageMagick/Wand"""
        for line in self:
            line.image_for_report = False
            if not line.order_line_image or not line.order_line_image:
                continue
            try:
                img_data = base64.b64decode(line.order_line_image)
                with WandImage(blob=img_data) as img:
                    img.background_color = 'white'
                    img.alpha_channel = 'remove'
                    img.format = 'jpeg'
                    img.compression_quality = 95
                    jpeg_blob = img.make_blob('jpeg')
                    line.image_for_report = base64.b64encode(jpeg_blob)
            except Exception as e:
                _logger.error(
                    f"Wand conversion failed for {line.product_id.name}: {e}")
                raise UserError(_(
                    "Image Conversion Failed!\n\n"
                    f"Product: {line.product_id.name}\n"
                    f"Error: {str(e)}\n\n"
                    "Please ensure ImageMagick is properly installed:\n"
                    "sudo apt-get install imagemagick libmagickwand-dev"
                ))
