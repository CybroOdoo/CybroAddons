# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import base64
import logging
import os
import re
import tempfile
from PIL import Image, ImageOps
import requests
from odoo import api, fields, models
from odoo.exceptions import UserError
from . import downloader

try:
    from resizeimage import resizeimage
except ImportError:
    resizeimage = None

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    """
    Check if the searched image limit is greater than 10 and a warning
    message will be raised.
    """
    _inherit = 'product.template'

    search_image_ids = fields.One2many(
        'product.image.suggestion',
        'product_tmpl_id',
        string='Images',
        readonly=True,
        help="To show the images downloaded.",
    )
    search_field = fields.Char(
        string='Search Text',
        help="Type the text to be searched.",
    )
    image_limit = fields.Integer(
        string='Limit',
        default=5,
        help="Limit of images to display.",
    )
    resize_image = fields.Boolean(
        default=True,
        help="Resize the image.",
    )

    @api.onchange('image_limit')
    def _onchange_image_limit(self):
        """
        Check if the searched image limit is greater than 10 and a warning
        message will be raised.
        """
        if self.image_limit > 10:
            raise UserError(self.env._(
                'Setting a limit higher than 10 may slow down image search. '
                'Please try to reduce the limit.'
            ))

    def action_search_image(self):
        """
        Clear search images and add new search
        """
        for rec in self:
            rec.search_image_ids = [[5, 0, 0]]
            if rec.image_limit > 10:
                _logger.warning(
                    "A high image limit may slow down the image search."
                )
            if not rec.search_field:
                raise UserError(self.env._(
                    'Please enter a keyword in "Search here..." to search for '
                    'images.'
                ))
            try:
                # Sanitize search text to prevent path traversal
                clean_field = re.sub(r'[/\\.]+', '_', rec.search_field)
                query_string = (
                    clean_field.replace(" ", "_").replace(",", "_")
                )
                image_datas = downloader.download(
                    query_string,
                    limit=rec.image_limit,
                    output_dir=None,
                    adult_filter_off=False,
                    timeout=60,
                    verbose=True,
                )
            except AttributeError:
                raise UserError(self.env._(
                    'No internet connection available or an error occurred '
                    'while searching for images.'
                ))
            if image_datas:
                for img in image_datas:
                    temp_name = ''
                    try:
                        img_request = requests.get(
                            img.strip(), timeout=10
                        ).content
                        if rec.resize_image:
                            fd, temp_name = tempfile.mkstemp(suffix='.png')
                            os.close(fd)
                            with open(temp_name, "wb") as file:
                                file.write(img_request)
                            img_data = Image.open(temp_name)
                            if resizeimage:
                                img_data = resizeimage.resize_contain(
                                    img_data, [1024, 1024]
                                )
                            else:
                                img_data = ImageOps.contain(
                                    img_data, (1024, 1024)
                                )
                            img_data.save(temp_name, img_data.format or 'PNG')
                            with open(temp_name, "rb") as image_file:
                                binary_image = base64.b64encode(
                                    image_file.read()
                                ).decode('utf-8')
                        else:
                            byte_image = bytearray(img_request)
                            binary_image = base64.b64encode(
                                byte_image
                            ).decode('utf-8')
                        vals = {
                            'image': binary_image,
                            'product_tmpl_id': rec.id,
                        }
                        self.env['product.image.suggestion'].create(vals)
                    except Exception:
                        _logger.exception("Failed to display image in page.")
                        continue
                    finally:
                        if temp_name and os.path.exists(temp_name):
                            try:
                                os.remove(temp_name)
                            except OSError:
                                _logger.debug(
                                    "Failed to remove temporary file %s",
                                    temp_name,
                                )
            else:
                raise UserError(self.env._(
                    'No image suggestions found for this query.'
                ))
