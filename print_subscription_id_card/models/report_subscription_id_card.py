# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies(odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
import io
import logging

from PIL import Image, UnidentifiedImageError, WebPImagePlugin

from odoo import api, models
from odoo.tools.image import image_apply_opt, image_data_uri

_logger = logging.getLogger(__name__)


class ReportSubscriptionIdCard(models.AbstractModel):
    """Values of the Subscription ID Card report."""
    _name = 'report.print_subscription_id_card.report_subscription_id_card'
    _description = 'Subscription ID Card Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Pass the card data plus the partner record, so the template can
        embed the photo instead of linking a URL wkhtmltopdf cannot open."""
        data = data or {}
        partner = self.env['res.partner'].browse(data.get('partner_id')).exists()
        return dict(data, partner=partner, partner_image=self._get_partner_image(partner))

    @api.model
    def _get_partner_image(self, partner):
        """Data URI of the partner photo, as PNG.

        wkhtmltopdf cannot open /web/image URLs (no session) nor display WebP,
        the format Odoo often stores photos in, so the photo is converted to a
        PNG and embedded. Without a photo, the generated avatar is used."""
        if not partner:
            return False
        if partner.image_1920:
            try:
                return image_data_uri(self._image_to_png(partner.image_1920.content))
            except (OSError, UnidentifiedImageError, ValueError):
                _logger.warning("Could not convert the photo of partner %s", partner.id,
                                exc_info=True)
                # avatar_1920 would be the same unreadable photo: use the
                # generated initials avatar instead.
                return image_data_uri(partner._avatar_generate_svg() if partner.name
                                      else partner._avatar_get_placeholder())
        return image_data_uri(partner.avatar_1920)

    @api.model
    def _image_to_png(self, content):
        """Return ``content`` (PNG, JPEG, GIF or WebP) as a PNG of at most
        256 px. Odoo only preloads Pillow's basic formats, so WebP is opened
        with its plugin explicitly."""
        stream = io.BytesIO(content)
        if content[:4] == b'RIFF' and content[8:12] == b'WEBP':
            image = WebPImagePlugin.WebPImageFile(stream)
        else:
            image = Image.open(stream)
        # Square centre crop, so the photo fills the round frame on the card.
        side = min(image.size)
        left, top = (image.width - side) // 2, (image.height - side) // 2
        image = image.crop((left, top, left + side, top + side))
        image.thumbnail((256, 256))
        if image.mode not in ('1', 'L', 'P', 'RGB', 'RGBA'):
            image = image.convert('RGBA')
        return image_apply_opt(image, 'PNG')
