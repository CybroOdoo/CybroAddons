# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anjali VP (odoo@cybrosys.com)
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
import requests
from odoo import models, fields, api
from odoo.tools import _
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    """ Inheriting 'product.template' for adding image url """
    _inherit = 'product.template'

    image_url = fields.Char(string='Image URL', help="Url of Image")
    image_added = fields.Binary("Image (1920x1920)",
                                compute='_compute_image_added', store=True,
                                help="Uploaded Image")

    @api.depends('image_url')
    def _compute_image_added(self):
        """ Function to load an image from URL or local file path """
        for record in self:
            image = False
            if record.image_url:
                if record.image_url.startswith(('http://', 'https://')):
                    # Load image from URL
                    try:
                        image = base64.b64encode(
                            requests.get(record.image_url).content)
                    except Exception as e:
                        raise UserError(
                            _("Error loading image from URL: %s" % str(e)))
                else:
                    # Load image from local file path
                    try:
                        with open(record.image_url, 'rb') as image_file:
                            image = base64.b64encode(image_file.read())
                    except Exception as e:
                        raise UserError(
                            _("Error loading image from local path: %s" % str(
                                e)))

            if image:
                record.image_1920 = image
                record.image_added = image

class ProductVariantImage(models.Model):
    """ Inheriting 'product.product' for adding image url """
    _inherit = 'product.product'

    image_url = fields.Char(string='Image URL', help="Url of Image")
    image_added = fields.Binary("Image (1920x1920)",
                                compute='_compute_image_added', store=True,
                                help="Uploaded Image")

    @api.depends('image_url')
    def _compute_image_added(self):
        """ Function to load an image from URL or local file path """
        for record in self:
            image = False
            if record.image_url:
                if record.image_url.startswith(('http://', 'https://')):
                    # Load image from URL
                    try:
                        image = base64.b64encode(
                            requests.get(record.image_url).content)
                    except Exception as e:
                        raise UserError(
                            _("Error loading image from URL: %s" % str(e)))
                else:
                    # Load image from local file path
                    try:
                        with open(record.image_url, 'rb') as image_file:
                            image = base64.b64encode(image_file.read())
                    except Exception as e:
                        raise UserError(
                            _("Error loading image from local path: %s" % str(
                                e)))

            if image:
                record.image_1920 = image
                record.image_added = image
