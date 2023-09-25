# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohammed Shahil MP @cybrosys(odoo@cybrosys.com)
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
import requests
import base64
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProductImage(models.Model):
    _inherit = 'product.template'

    image_url = fields.Char(string='Image URL')
    image_added = fields.Binary("Image (1920x1920)",
                                compute='_compute_image_added', store=True)

    @api.depends('image_url')
    def _compute_image_added(self):
        """ Function to load an image from URL or local file path """
        image = False
        if self.image_url:
            if self.image_url.startswith(('http://', 'https://')):
                # Load image from URL
                try:
                    image = base64.b64encode(
                        requests.get(self.image_url).content)
                except Exception as e:
                    # Handle URL loading errors
                    raise UserError(_(f"Error loading image from URL: {str(e)}"))
            else:
                # Load image from local file path
                try:
                    with open(self.image_url, 'rb') as image_file:
                        image = base64.b64encode(image_file.read())
                except Exception as e:
                    # Handle local file loading errors
                    raise UserError(
                        _(f"Error loading image from local path: {str(e)}"))
        image_added = image
        if image_added:
            self.image_1920 = image_added


class ProductVariantImage(models.Model):
    _inherit = 'product.product'

    image_url = fields.Char(string='Image URL')
    image_added = fields.Binary("Image (1920x1920)",
                                compute='_compute_image_added', store=True)

    @api.depends('image_url')
    def _compute_image_added(self):
        """ Function to load an image from URL or local file path """
        image = False
        if self.image_url:
            if self.image_url.startswith(('http://', 'https://')):
                # Load image from URL
                try:
                    image = base64.b64encode(
                        requests.get(self.image_url).content)
                except Exception as e:
                    # Handle URL loading errors
                    raise UserError(_(f"Error loading image from URL: {str(e)}"))
            else:
                # Load image from local file path
                try:
                    with open(self.image_url, 'rb') as image_file:
                        image = base64.b64encode(image_file.read())
                except Exception as e:
                    # Handle local file loading errors
                    raise UserError(
                        _(f"Error loading image from local path: {str(e)}"))
        image_added = image
        if image_added:
            self.image_1920 = image_added
