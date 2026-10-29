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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
import base64
import logging
import os
import certifi
import urllib3
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Many image CDNs (Unsplash included) return 403 to requests that don't
# look like they came from a browser. Sending a normal User-Agent avoids
# that class of failure.
_IMAGE_REQUEST_HEADERS = {
    'User-Agent': ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/124.0 Safari/537.36'),
}
_IMAGE_REQUEST_RETRIES = urllib3.Retry(
    total=3, connect=3, read=3, redirect=5, backoff_factor=0.5)
_IMAGE_REQUEST_TIMEOUT = urllib3.Timeout(connect=10.0, read=20.0)
_HTTP = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())


class ProductImageUrlMixin(models.AbstractModel):
    """ Load a product image from a web URL or a local file path """
    _name = 'product.image.url.mixin'
    _description = 'Product Image URL Mixin'

    image_url = fields.Char(
        string='Image URL',
        help="URL or local file path of the product image. The image is "
             "loaded when the record is saved.")

    @api.model_create_multi
    def create(self, vals_list):
        """ Load the image of every record created with an image URL """
        return super().create([self._prepare_image_vals(vals)
                               for vals in vals_list])

    def write(self, vals):
        """ Reload the image when the image URL changes """
        return super().write(self._prepare_image_vals(vals))

    @api.model
    def _prepare_image_vals(self, vals):
        """ Return a copy of vals with image_1920 loaded from image_url """
        if not vals.get('image_url'):
            return vals
        image, reason = self._get_image_from_source(vals['image_url'])
        if not image:
            raise UserError(self.env._(
                "Could not load the image from %(location)s: %(reason)s",
                location=vals['image_url'], reason=reason))
        return dict(vals, image_1920=image)

    @api.model
    def _get_image_from_source(self, source):
        """ Return (base64_data, None) for a web URL or an absolute local
        path, or (False, reason) when the image cannot be loaded. """
        source = source.strip()
        if source.startswith(('http://', 'https://')):
            return self._fetch_image_b64(source)
        if os.path.isabs(source):
            return self._read_local_image_b64(source)
        return False, "not a web URL or an absolute file path"

    @api.model
    def _fetch_image_b64(self, url):
        """ Download an image, retrying transient failures and sending a
        browser-like User-Agent so CDNs that block bot requests still work. """
        try:
            response = _HTTP.request(
                'GET', url,
                headers=_IMAGE_REQUEST_HEADERS,
                timeout=_IMAGE_REQUEST_TIMEOUT,
                retries=_IMAGE_REQUEST_RETRIES,
            )
        except Exception as e:
            reason = "connection error: %s" % e
            _logger.warning("Failed to fetch product image %s (%s)", url, reason)
            return False, reason

        if response.status != 200:
            reason = "HTTP %s" % response.status
            _logger.warning("Product image fetch for %s returned %s", url, reason)
            return False, reason

        content_type = response.headers.get('Content-Type', '')
        if content_type and not content_type.startswith('image'):
            reason = "unexpected content-type '%s' (URL may need to be a " \
                     "direct image link)" % content_type
            _logger.warning("Product image fetch for %s: %s", url, reason)
            return False, reason

        return base64.b64encode(response.data).decode(), None

    @api.model
    def _read_local_image_b64(self, path):
        """ Read an image file from the Odoo server """
        if not os.path.isfile(path):
            reason = "file does not exist on the Odoo server"
            _logger.warning("Product image path not found: %s", path)
            return False, reason
        try:
            with open(path, 'rb') as image_file:
                return base64.b64encode(image_file.read()).decode(), None
        except OSError as e:
            _logger.warning("Failed to read product image %s: %s", path, e)
            return False, str(e)
