# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import requests
from odoo import models, _
from odoo.exceptions import ValidationError
from odoo.tools import html2plaintext


class ProductProduct(models.Model):
    """Inherit product.product model"""
    _inherit = 'product.product'

    def _get_openai_api_key(self):
        """Helper to fetch and validate the OpenAI API key."""
        api_key = self.env['ir.config_parameter'].sudo().get_param('openai_api_key')
        if not api_key:
            raise ValidationError(
                _("Invalid API key provided. Please ensure that you have "
                  "entered the correct API key.")
            )
        return api_key

    def _call_openai_chat(self, api_key, prompt, max_tokens=200):
        """
        Central helper to call OpenAI Chat Completions API.
        Raises ValidationError on HTTP errors or missing 'choices'.
        """
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            json={
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "n": 1,
                "temperature": 0.5,
            },
            timeout=30,
        )

        if not response.ok:
            error_msg = response.json().get("error", {}).get("message", response.text)
            raise ValidationError(_("OpenAI API Error: %s") % error_msg)

        data = response.json()

        if "choices" not in data or not data["choices"]:
            raise ValidationError(
                _("Unexpected response from OpenAI API. No choices returned: %s") % data
            )

        return data["choices"][0]["message"]["content"]

    def action_generate_tags_from_internal_note(self):
        """Action to create tags from Internal notes (supports single & multi-select)."""
        api_key = self._get_openai_api_key()

        active_ids = self._context.get('active_ids') or self._context.get(
            'active_id')
        if not active_ids:
            active_ids = self.ids
        if isinstance(active_ids, int):
            active_ids = [active_ids]

        products = self.env['product.product'].browse(active_ids)

        # Pre-fetch all existing tags once for efficiency
        existing_tags = {
            tag.name: tag
            for tag in self.env['product.tag'].search([])
        }

        success_products = []
        skipped_products = []

        for product in products:
            plain_text = html2plaintext(product.description or '').strip()

            if not plain_text:
                skipped_products.append(product.name)
                continue

            prompt = (
                "Generate a comma-separated list of relevant product tags "
                "for the following description. Return only the tags, nothing else.\n\n"
                f"Description: {product.description}\n\nTags:"
            )

            raw_text = self._call_openai_chat(api_key, prompt, max_tokens=60)
            tags_list = [tag.strip() for tag in raw_text.split(",") if
                         tag.strip()]

            tag_ids_to_add = []
            for tag_name in tags_list:
                if tag_name in existing_tags:
                    tag_ids_to_add.append(existing_tags[tag_name].id)
                else:
                    new_tag = self.env['product.tag'].create({'name': tag_name})
                    existing_tags[tag_name] = new_tag
                    tag_ids_to_add.append(new_tag.id)

            if tag_ids_to_add:
                product.write({
                    'product_tag_ids': [(4, tid) for tid in tag_ids_to_add]
                })

            success_products.append(product.name)

        # Build notification message
        message_parts = []
        if success_products:
            message_parts.append(
                _("Tags generated successfully for: %s")
                % ', '.join(success_products)
            )
        if skipped_products:
            raise ValidationError(
                _("Tags not generated. Missing internal note for products: %s")
                % ', '.join(skipped_products)
            )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': None,
                'message': ' | '.join(message_parts),
                'type': 'success' if success_products else 'warning',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def action_generate_internal_notes_from_tags(self):
        """Action to generate Internal notes from tags (supports single & multi-select)."""
        api_key = self._get_openai_api_key()

        active_ids = self._context.get('active_ids') or self._context.get(
            'active_id')
        if not active_ids:
            active_ids = self.ids
        if isinstance(active_ids, int):
            active_ids = [active_ids]

        products = self.env['product.product'].browse(active_ids)

        success_products = []
        skipped_products = []

        for product in products:
            if not product.product_tag_ids:
                skipped_products.append(product.name)
                continue

            tag_lines = "\n".join(
                f"- {tag.name}" for tag in product.product_tag_ids)
            prompt = (
                "Generate a concise product description based on the following tags. "
                "Return only the description, nothing else.\n\n"
                f"Tags:\n{tag_lines}\n\nDescription:"
            )

            description = self._call_openai_chat(api_key, prompt,
                                                 max_tokens=200)
            product.description = description.strip()
            success_products.append(product.name)

        # Build notification message
        message_parts = []
        if success_products:
            message_parts.append(
                _("Internal note generated successfully for: %s")
                % ', '.join(success_products)
            )
        if skipped_products:
            raise ValidationError(
                _("Internal note not generated. Missing tags for products: %s")
                % ', '.join(skipped_products)
            )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': None,
                'message': ' | '.join(message_parts),
                'type': 'success' if success_products else 'warning',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
