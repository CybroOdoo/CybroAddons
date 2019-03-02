# -*- coding: utf-8 -*-
import base64
import logging
import os
from PIL import Image
import tempfile
from resizeimage import resizeimage
from . import google_images_download
from odoo import models, fields, api, _
from odoo.exceptions import UserError, Warning


_logger = logging.getLogger(__name__)


class ProductImageSelection(models.TransientModel):
    _name = "product.image.suggestion"

    image = fields.Binary('Image', attachment=True)
    product_tmpl_id = fields.Many2one('product.template', 'Related Product', copy=True)

    @api.multi
    def action_set_image(self):
        """Set product images from suggested images"""
        self_image = self.image
        if self_image:
            self.product_tmpl_id.image = self_image


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def get_search_string(self):
        for prod in self:
            prod.search_field = prod.name

    search_image_ids = fields.One2many('product.image.suggestion', 'product_tmpl_id', string='Images', readonly=True)
    search_field = fields.Char('Search Text', compute=get_search_string, readonly=False, store=True)
    image_limit = fields.Integer('Limit', default=5)
    resize_image = fields.Boolean('Resize Image', default=True)

    @api.onchange('image_limit')
    def war_image_limit(self):
        if self.image_limit > 10:
            raise Warning(_('This may slow down image search..!! !'))

    @api.multi
    def search_images_button(self):
        """Clear search images and add new search"""
        self.search_image_ids = [[5,0,0,]]
        if self.image_limit > 10:
            _logger.warning("High limit number slow down the image searches")
        try:
            response = google_images_download.googleimagesdownload()
            query_string = self.search_field.replace(" ", "_").replace(",", "_")
            arguments = {"keywords": query_string, "limit": self.image_limit, "print_urls": False, 'safe_search': True}
            image_datas = response.download(arguments)  # passing the arguments to the function
        except AttributeError:
            raise UserError(_('No internet connection available or Something wrong !'))
        if image_datas:
            for im in image_datas:
                temp_name = ''
                try:
                    if self.resize_image:
                        temp_file, temp_name = tempfile.mkstemp(suffix='.png')
                        file = open(temp_name, "wb")
                        file.write(im)
                        file.close()
                        img = Image.open(temp_name)
                        img = resizeimage.resize_contain(img, [1024, 1024])
                        img.save(temp_name, img.format)
                        with open(temp_name, "rb") as image_file:
                            binary_image = base64.b64encode(image_file.read())
                    else:
                        b = bytearray(im)
                        binary_image = base64.b64encode(b)
                    vals = dict(image=binary_image, product_tmpl_id=self.id)
                    self.env['product.image.suggestion'].create(vals)

                    if self.resize_image:
                        os.remove(temp_name)
                except:
                    _logger.exception(_("failed to display in page"))
                    continue
        else:
            raise UserError(_('No image suggestions for this image'))
