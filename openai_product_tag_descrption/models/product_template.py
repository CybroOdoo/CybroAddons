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
from openai import OpenAI

from odoo import models, _
from odoo.exceptions import ValidationError
from odoo.tools import html2plaintext


class ProductTemplate(models.Model):
    """Inherit product.template model."""
    _inherit = 'product.template'

    def action_generate_tags_from_internal_note(self):
        """Create product tags from the product internal note."""
        api_key = self.env['ir.config_parameter'].sudo().get_param(
            'openai_api_key')
        if not api_key:
            raise ValidationError(
                _("Invalid API key provided. Please ensure that you have "
                  "entered the correct API key."))
        product_ids = self.env.context.get('active_ids', [])
        if not product_ids:
            raise ValidationError(_("No active product found."))

        products = self.env['product.template'].browse(product_ids)

        success_products = []
        skipped_products = []
        tag_model = self.env['product.tag']
        existing_tags = tag_model.search([])
        client = OpenAI(api_key=api_key)

        for product in products:
            plain_text = html2plaintext(product.description or '').strip()

            if not plain_text:
                skipped_products.append(product.name)
                continue

            prompt = f"""
            Generate product tags.

            Rules:
            - Return ONLY comma-separated values
            - No numbering
            - No hashtags
            - No explanation

            Description:
            {plain_text}
            """

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI assistant"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.8,
                top_p=1
            )
            if not response or not response.choices:
                raise ValidationError(
                    _("Failed to generate response from AI for product: %s")
                    % product.name)

            tags = response.choices[0].message.content
            if '#' in tags and ',' not in tags:
                tags = tags.replace('#', ',')

            tags = [tag.strip() for tag in tags.split(',') if tag.strip()]

            tag_model = self.env['product.tag']
            # existing_tags = tag_model.search([])
            tag_ids = [
                (existing_tags.filtered(lambda t: t.name == tag)[:1].id)
                if existing_tags.filtered(lambda t: t.name == tag)
                else tag_model.create({
                    'name': tag,
                    'product_template_ids': [(4, product.id)]
                }).id
                for tag in tags
            ]

            product.write({
                'product_tag_ids': [(4, tag_id) for tag_id in tag_ids]
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
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def action_generate_internal_notes_from_tags(self):
        """Generate product internal note from product tags."""
        api_key = self.env['ir.config_parameter'].sudo().get_param(
            'openai_api_key')
        if not api_key:
            raise ValidationError(
                _("Invalid API key provided. Please ensure that you have "
                  "entered the correct API key."))
        product_ids = self.env.context.get('active_ids', [])
        if not product_ids:
            raise ValidationError(_("No active product found."))

        products = self.env['product.template'].browse(product_ids)

        success_products = []
        skipped_products = []
        client = OpenAI(api_key=api_key)

        for product in products:
            if not product.product_tag_ids:
                skipped_products.append(product.name)
                continue

            tag_names = product.product_tag_ids.mapped('name')
            prompt = "Generate a description for a product based on the following tags:\n{}\n\nDescription:".format(
                "\n".join(f"- {name}" for name in tag_names)
            )

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI assistant"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.8,
                top_p=1
            )

            if not response or not response.choices:
                raise ValidationError(
                    _("Failed to generate response from AI for product: %s")
                    % product.name)

            product.description = response.choices[0].message.content
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
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
