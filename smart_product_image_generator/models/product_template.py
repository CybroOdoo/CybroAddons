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
#############################################################################
import base64
import logging

from markupsafe import Markup

from odoo import fields, models
from odoo.tools import BinaryValue

_logger = logging.getLogger(__name__)


def extract_raw_bytes(data):
    """Extract raw bytes from BinaryValue, base64 string, or bytes."""
    if not data:
        return b''
    if isinstance(data, BinaryValue):
        return data.content
    if hasattr(data, 'content'):
        return data.content
    if isinstance(data, (bytes, bytearray, memoryview)):
        raw = bytes(data)
        if raw.startswith((b'\x89PNG', b'\xff\xd8', b'RIFF', b'GIF')):
            return raw
        try:
            return base64.b64decode(raw)
        except Exception:
            return raw
    if isinstance(data, str):
        try:
            return base64.b64decode(data)
        except Exception:
            return data.encode('utf-8')
    return bytes(data)


class ProductTemplate(models.Model):
    """Extend products with AI image generation metadata and actions."""
    _inherit = 'product.template'

    ai_last_generated_date = fields.Datetime(
        string='Last AI Image Generated',
        readonly=True,
        copy=False,
    )
    ai_generation_count = fields.Integer(
        string='AI Generation Count',
        default=0,
        readonly=True,
        copy=False,
    )

    def _apply_ai_generated_image(
        self, image_data, provider_label='', style_label='', size='', is_bulk=False
    ):
        """Apply an AI-generated image to the product and post a chatter note."""
        self.ensure_one()
        ai_count = int(self.ai_generation_count or 0) + 1
        self.write({
            'image_1920': image_data,
            'ai_last_generated_date': fields.Datetime.now(),
            'ai_generation_count': ai_count,
        })
        try:
            if is_bulk:
                body = Markup(
                    '<b>AI Image Generated &amp; Applied (Bulk)</b><br/>'
                    'Provider: {provider}<br/>'
                    'Size: {size}'
                ).format(provider=provider_label, size=size)
            else:
                body = Markup(
                    '<b>AI Image Generated &amp; Applied</b><br/>'
                    'Provider: {provider}<br/>'
                    'Style: {style}<br/>'
                    'Size: {size}<br/>'
                    'Generation #: {count}'
                ).format(
                    provider=provider_label,
                    style=style_label,
                    size=size,
                    count=ai_count,
                )
            image_bytes = extract_raw_bytes(image_data)
            self.message_post(
                body=body,
                attachments=[('ai_generated_image.png', image_bytes)],
            )
        except Exception:
            _logger.warning(
                'Chatter post failed for product %s (non-critical)',
                self.name,
                exc_info=True,
            )

    def action_open_ai_image_wizard(self):
        """Open the AI image generation wizard for this product."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Generate Product Image with AI',
            'res_model': 'smart.product.image.generator',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.id,
            },
        }

    def action_bulk_generate_ai_images(self):
        """Bulk action: open wizard configured for bulk generation."""
        product_ids = self.env.context.get('active_ids', [])
        if not product_ids:
            return False

        return {
            'type': 'ir.actions.act_window',
            'name': 'Bulk Generate AI Images',
            'res_model': 'smart.product.image.generator',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_bulk_mode': True,
                'default_bulk_product_ids': [(6, 0, product_ids)],
                'default_product_id': product_ids[0] if product_ids else False,
            },
        }
