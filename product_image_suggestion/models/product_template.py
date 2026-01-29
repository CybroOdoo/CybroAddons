# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: RAHUL CK (odoo@cybrosys.com)
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
###############################################################################
import base64
import logging
import os
import tempfile
import requests
from PIL import Image
from resizeimage import resizeimage
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from . import downloader

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    """
    Inherited product template to add new fields to show the downloaded image
    and set an image as product image.
    """
    _inherit = 'product.template'

    search_image_ids = fields.One2many('product.image.suggestion',
                                       'product_tmpl_id', string='Images',
                                       readonly=True,
                                       help="To show the images downloaded")
    search_field = fields.Char(string='Search Text',
                               help="Type the text to be searched")
    image_limit = fields.Integer(string='Limit', default=5,
                                 help="Limit of images to display")
    resize_image = fields.Boolean(string='Resize Image', default=True,
                                  help="Resize the image")

    @api.onchange('image_limit')
    def _onchange_image_limit(self):
        """
        Check if the searched image limit is greater than 10 and a warning
        message will be raised.
        """
        if self.image_limit > 10:
            raise UserError(_('This may slow down image search..!!!'))

    def action_search_image(self):
        """Clear search images and add new search"""
        for rec in self:
            rec.search_image_ids = [[5, 0, 0]]
            if rec.image_limit > 10:
                _logger.warning("High limit number slow down the image "
                                "searches")
            try:
                query_string = rec.search_field.replace(" ", "_").replace(",",
                                                                          "_")
                # Search the images from bing using download function from
                # downloader file
                image_datas = downloader.download(query_string,
                                                  limit=rec.image_limit,
                                                  output_dir='dataset',
                                                  adult_filter_off=False,
                                                  timeout=60, verbose=True)
            except:
                raise UserError(_('No internet connection available or '
                                'Something wrong !'))
            if image_datas:
                for img in image_datas:
                    temp_name = ''
                    try:
                        img_request = requests.get(img.strip()).content
                        # If resize image is enabled, downloaded images will be
                        # resized and shown in view.
                        if self.resize_image:
                            temp_file, temp_name = tempfile.mkstemp(
                                suffix='.png')
                            file = open(temp_name, "wb")
                            file.write(img_request)
                            file.close()
                            img_data = resizeimage.resize_contain(
                                Image.open(temp_name), [1024, 1024])
                            img_data.save(temp_name, img_data.format)
                            with open(temp_name, "rb") as image_file:
                                binary_image = base64.b64encode(
                                    image_file.read())
                        else:
                            binary_image = \
                                base64.b64encode(bytearray(img_request))
                        self.env['product.image.suggestion'].create({
                            'image': binary_image,
                            'product_tmpl_id': rec.id
                        })
                        if self.resize_image:
                            os.remove(temp_name)
                    except:
                        _logger.exception(_("failed to display in page"))
                        continue
            else:
                raise UserError(_('No image suggestions for this image'))
