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
"""Wizard for generating and applying AI product images."""
import base64
import logging
import requests

from odoo import api, fields, models
from odoo.tools import BinaryBytes, BinaryValue
from odoo.exceptions import UserError, ValidationError

from ..models.product_template import extract_raw_bytes

_logger = logging.getLogger(__name__)


class ProductAiImageLine(models.TransientModel):
    """Holds individual generated image variants returned from AI."""
    _name = 'product.ai.image.line'
    _description = 'AI Generated Image Line'

    wizard_id = fields.Many2one(
        'smart.product.image.generator',
        required=True,
        ondelete='cascade',
    )
    image = fields.Binary(string='Generated Image', attachment=False)
    image_name = fields.Char(
        default='ai_generated.png',
    )
    provider_used = fields.Char(string='Provider')
    style_used = fields.Char(string='Style')

    def action_apply_image_line(self):
        """
        Called directly from the one2many list button.
        'self' is the specific product.ai.image.line record clicked.
        """
        self.ensure_one()
        wizard = self.wizard_id
        if not wizard.exists():
            raise UserError(
                self.env._('Wizard session has expired. Please close and reopen.')
            )
        return wizard.action_apply_image(self.id)


class SmartProductImageGenerator(models.TransientModel):
    """Transient wizard model for AI image generation."""
    _name = 'smart.product.image.generator'
    _description = 'Smart Product Image Generator Wizard'

    product_id = fields.Many2one(
        'product.template',
        required=True,
    )
    prompt = fields.Text(
        string='AI Prompt',
        compute='_compute_ai_prompt',
        store=True,
        readonly=False,
    )
    ai_provider = fields.Selection(
        selection=[
            ('openai', 'OpenAI DALL-E 3'),
            ('stability', 'Stability AI'),
            ('gemini', 'Google Gemini'),
        ],
        string='AI Provider',
        required=True,
        default='stability',
    )
    image_style = fields.Selection(
        selection=[
            ('professional', 'Professional Product Photo'),
            ('lifestyle', 'Lifestyle / In Context'),
            ('minimal', 'Minimal / White Background'),
            ('artistic', 'Artistic / Creative'),
        ],
        required=True,
        default='professional',
    )
    image_size = fields.Selection(
        selection=[
            ('1024x1024', '1024 x 1024 (Square)'),
            ('1792x1024', '1792 x 1024 (Landscape)'),
            ('1024x1792', '1024 x 1792 (Portrait)'),
        ],
        required=True,
        default='1024x1024',
    )
    num_variants = fields.Integer(
        string='Number of Variants',
        default=2,
    )
    enhance_existing = fields.Boolean(
        string='Improve Existing Image',
        default=False,
    )
    enhancement_description = fields.Text(
        string='Improvement Instructions',
    )
    current_image = fields.Binary(
        string='Current Image',
        related='product_id.image_1920',
        readonly=True,
    )
    generated_image_ids = fields.One2many(
        'product.ai.image.line',
        'wizard_id',
        string='Generated Images',
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('generated', 'Generated'),
            ('pending_approval', 'Pending Approval'),
            ('applied', 'Applied'),
        ],
        default='draft',
    )
    bulk_mode = fields.Boolean(default=False)
    bulk_product_ids = fields.Many2many(
        'product.template',
        string='Products (Bulk)',
    )
    bulk_skip_existing = fields.Boolean(
        string='Skip products that already have images',
        default=True,
    )
    bulk_progress_log = fields.Text(
        string='Progress',
        readonly=True,
    )

    @api.depends('product_id', 'image_style')
    def _compute_ai_prompt(self):
        """Generate an AI prompt based on product details and style."""
        brand_dna = self._get_config_param(
            'smart_product_image_generator.brand_dna', ''
        )
        style_intros = {
            'professional': (
                'Professional high-resolution product photograph for '
                'e-commerce. Clean white background, studio lighting, '
                'sharp focus. Faithfully represent the real product.'
            ),
            'lifestyle': (
                'Lifestyle product photograph in a real-world context. '
                'Natural environment, warm lighting, realistic setting.'
            ),
            'minimal': (
                'Minimalist product photograph. Pure white background, '
                'soft even lighting, product centered.'
            ),
            'artistic': (
                'Artistic product visualization. Unique perspective, '
                "creative lighting, highlights the product's character."
            ),
        }
        for rec in self:
            if not rec.product_id:
                rec.prompt = ''
                continue
            product = rec.product_id
            style_key = rec.image_style or 'professional'
            intro = style_intros.get(
                style_key, style_intros['professional']
            )
            attribute_lines = []
            for attr_line in product.attribute_line_ids:
                values = ', '.join(
                    attr_line.value_ids.mapped('name')
                )
                attribute_lines.append(
                    f'{attr_line.attribute_id.name}: {values}'
                )
            attributes_str = '; '.join(attribute_lines)
            price = float(product.list_price or 0.0)
            if price < 50:
                price_tier = 'budget-friendly product'
            elif price < 200:
                price_tier = 'mid-range product'
            else:
                price_tier = 'premium product'
            lines = [intro]
            if brand_dna and isinstance(brand_dna, str) and brand_dna.strip():
                lines.append(brand_dna.strip())
            lines.append(f'Product: {product.name or ""}')
            categ_name = (
                product.categ_id.display_name
                or product.categ_id.name
                or ''
            )
            if categ_name:
                lines.append(f'Category: {categ_name}')
            if attributes_str:
                lines.append(f'Attributes: {attributes_str}')
            if product.description_sale:
                lines.append(
                    f'Description: {str(product.description_sale)[:300]}'
                )
            lines.append(f'This is a {price_tier}.')
            rec.prompt = '\n'.join(lines)

    @api.constrains('num_variants')
    def _check_num_variants(self):
        """Validate that the number of image variants is within limits."""
        for rec in self:
            if rec.num_variants < 1 or rec.num_variants > 4:
                raise ValidationError(
                    self.env._('Number of variants must be between 1 and 4.')
                )

    # ── Helpers ───────────────────────────────────────────────────

    def _get_config_param(self, key, default=''):
        """Retrieve a system parameter."""
        val = self.env['ir.config_parameter'].sudo().get_str(key, default)
        return val if val is not None else default

    def _is_approval_required(self):
        """Return True when manager approval is required before applying images."""
        return self.env['ir.config_parameter'].sudo().get_bool(
            'smart_product_image_generator.approval_required', False
        )

    def _get_selection_labels(self):
        """Return human-readable (provider_label, style_label) for this wizard."""
        fields_desc = self.fields_get(['ai_provider', 'image_style'])
        provider_label = dict(
            fields_desc['ai_provider']['selection']
        ).get(self.ai_provider, self.ai_provider or '')
        style_label = dict(
            fields_desc['image_style']['selection']
        ).get(self.image_style, self.image_style or '')
        return provider_label, style_label

    def _get_api_key(self, provider):
        """Retrieve the configured API key for the selected AI provider."""
        key_map = {
            'openai': 'smart_product_image_generator.openai_api_key',
            'stability': 'smart_product_image_generator.stability_api_key',
            'gemini': 'smart_product_image_generator.gemini_api_key',
        }
        key = (self._get_config_param(key_map.get(provider, ''), '') or '').strip()
        if not key:
            raise UserError(
                self.env._(
                    'No API key configured for %s. '
                    'Go to Settings → Technical → System Parameters.',
                    provider,
                )
            )
        return key

    def _extract_raw_bytes(self, data):
        """Extract raw bytes from BinaryValue, base64 string, or bytes."""
        return extract_raw_bytes(data)

    def _to_b64_bytes(self, data):
        """Convert raw image bytes or b64 string to a format accepted by Odoo Binary fields."""
        if not data:
            return False
        if isinstance(data, BinaryValue):
            return data

        raw_bytes = self._extract_raw_bytes(data)
        return BinaryBytes(raw_bytes)

    def _safe_log(self, status, error_message='',
                  image_data=None, image_applied=False):
        """
        Write to ai.image.generation.log safely.
        Never raises an exception.
        """
        try:
            log_model = self.env['ai.image.generation.log']
            log_fields = log_model._fields.keys()

            vals = {
                'product_id': int(self.product_id.id),
                'status': str(status),
            }

            if 'prompt' in log_fields:
                vals['prompt'] = str(self.prompt or '')
            if 'ai_provider' in log_fields:
                vals['ai_provider'] = str(self.ai_provider or '')
            if 'image_style' in log_fields:
                vals['image_style'] = str(self.image_style or '')
            if 'error_message' in log_fields:
                vals['error_message'] = str(error_message or '')
            if 'image_generated' in log_fields and image_data:
                vals['image_generated'] = image_data
            if 'image_applied' in log_fields:
                vals['image_applied'] = bool(image_applied)
            if 'image_size' in log_fields:
                vals['image_size'] = str(self.image_size or '')
            if 'enhance_mode' in log_fields:
                vals['enhance_mode'] = bool(self.enhance_existing)
            if 'num_variants_requested' in log_fields:
                vals['num_variants_requested'] = int(
                    self.num_variants or 1
                )

            log_model.sudo().create(vals)

        except Exception as exc:
            _logger.warning(
                'AI image log write failed (non-critical): %s', exc
            )

    # ── Provider: OpenAI ──────────────────────────────────────────

    def _generate_openai(self, prompt, num_variants, image_size,
                         existing_image=None, enhance_desc=''):
        """Generate product images using the OpenAI Images API."""
        _ = existing_image
        api_key = self._get_api_key('openai')
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }
        size_map = {
            '1024x1024': '1024x1024',
            '1792x1024': '1536x1024',
            '1024x1792': '1024x1536',
        }
        size = size_map.get(image_size, '1024x1024')
        full_prompt = prompt
        if enhance_desc:
            full_prompt = f'{prompt}\n\nEnhancement: {enhance_desc}'
        images = []
        for _ in range(int(num_variants)):
            payload = {
                'model': 'gpt-image-1',
                'prompt': full_prompt,
                'n': 1,
                'size': size,
                'quality': 'high',
            }
            try:
                resp = requests.post(
                    'https://api.openai.com/v1/images/generations',
                    headers=headers,
                    json=payload,
                    timeout=120,
                )
                resp.raise_for_status()
                item = resp.json()['data'][0]
                if item.get('b64_json'):
                    images.append(self._to_b64_bytes(item['b64_json']))
                elif item.get('url'):
                    img_resp = requests.get(item['url'], timeout=60)
                    img_resp.raise_for_status()
                    images.append(self._to_b64_bytes(img_resp.content))
                else:
                    raise UserError(
                        self.env._('OpenAI returned no image data.')
                    )
            except requests.exceptions.HTTPError as e:
                error_body = str(e)
                try:
                    error_body = (
                        e.response.json()
                        .get('error', {})
                        .get('message', str(e))
                    )
                except Exception as parse_exc:
                    _logger.debug('Failed to parse OpenAI error JSON: %s', parse_exc)
                raise UserError(
                    self.env._('OpenAI API error: %s', error_body)
                )
            except UserError:
                raise
            except Exception as e:
                raise UserError(
                    self.env._('OpenAI request failed: %s', str(e))
                )
        return images

    # ── Provider: Stability AI ────────────────────────────────────

    def _generate_stability(self, prompt, num_variants, image_size,
                             existing_image=None, enhance_desc=''):
        """Generate product images using the Stability AI API."""
        api_key = self._get_api_key('stability')
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Accept': 'image/*',
        }
        size_map = {
            '1024x1024': '1:1',
            '1792x1024': '16:9',
            '1024x1792': '9:16',
        }
        aspect_ratio = size_map.get(image_size, '1:1')
        full_prompt = prompt
        if enhance_desc:
            full_prompt = f'{prompt}\n{enhance_desc}'
        images = []
        for _ in range(int(num_variants)):
            files = {
                'prompt': (None, full_prompt),
                'output_format': (None, 'png'),
                'aspect_ratio': (None, aspect_ratio),
            }
            if existing_image:
                files['image'] = (
                    'input_image.png', self._extract_raw_bytes(existing_image), 'image/png'
                )
            try:
                resp = requests.post(
                    'https://api.stability.ai/v2beta/'
                    'stable-image/generate/core',
                    headers=headers,
                    files=files,
                    timeout=120,
                )
                resp.raise_for_status()
                images.append(self._to_b64_bytes(resp.content))
            except requests.exceptions.HTTPError as e:
                error_body = str(e)
                try:
                    error_body = e.response.json().get(
                        'message', str(e)
                    )
                except Exception as parse_exc:
                    _logger.debug('Failed to parse Stability AI error JSON: %s', parse_exc)
                raise UserError(
                    self.env._('Stability AI API error: %s', error_body)
                )
            except UserError:
                raise
            except Exception as e:
                raise UserError(
                    self.env._('Stability AI request failed: %s', str(e))
                )
        return images

    # ── Provider: Gemini ──────────────────────────────────────────

    def _generate_gemini(self, prompt, num_variants, image_size,
                          existing_image=None, enhance_desc=''):
        """Generate product images using the Google Gemini API."""
        _ = image_size
        api_key = self._get_api_key('gemini')
        full_prompt = prompt
        if enhance_desc:
            full_prompt = f'{prompt}\n\nEnhancement: {enhance_desc}'
        gen_url = (
            'https://generativelanguage.googleapis.com/v1beta/models/'
            f'gemini-2.5-flash-image:generateContent?key={api_key}'
        )
        headers = {'Content-Type': 'application/json'}
        images = []
        for _idx in range(min(int(num_variants), 4)):
            content_parts = []
            if existing_image and enhance_desc:
                img_data = existing_image
                if hasattr(img_data, 'to_base64'):
                    img_b64_str = img_data.to_base64()
                else:
                    raw_bytes = self._extract_raw_bytes(img_data)
                    img_b64_str = base64.b64encode(raw_bytes).decode('ascii')
                content_parts.append({
                    'inlineData': {
                        'mimeType': 'image/png',
                        'data': img_b64_str,
                    }
                })
            content_parts.append({'text': full_prompt})
            payload = {
                'contents': [{'parts': content_parts}],
                'generationConfig': {
                    'responseModalities': ['TEXT', 'IMAGE'],
                },
            }
            try:
                resp = requests.post(
                    gen_url, headers=headers,
                    json=payload, timeout=120,
                )
                resp.raise_for_status()
                data = resp.json()
                found = False
                for candidate in data.get('candidates', []):
                    for part in (
                        candidate.get('content', {}).get('parts', [])
                    ):
                        if 'inlineData' in part:
                            b64 = part['inlineData'].get('data', '')
                            if b64:
                                images.append(
                                    self._to_b64_bytes(b64)
                                )
                                found = True
                                break
                    if found:
                        break
                if not found:
                    _logger.warning('Gemini: no image in response')
            except requests.exceptions.HTTPError as e:
                error_body = str(e)
                try:
                    error_body = (
                        e.response.json()
                        .get('error', {})
                        .get('message', str(e))
                    )
                except Exception as parse_exc:
                    _logger.debug('Failed to parse Gemini error JSON: %s', parse_exc)
                raise UserError(
                    self.env._('Google Gemini API error: %s', error_body)
                )
            except UserError:
                raise
            except Exception as e:
                raise UserError(
                    self.env._('Google Gemini request failed: %s', str(e))
                )
        if not images:
            raise UserError(self.env._(
                'Gemini returned no images. Check your API key.'
            ))
        return images

    # ── Main actions ──────────────────────────────────────────────

    def action_generate_images(self):
        """Generate image variants from the selected AI provider."""
        self.ensure_one()

        if not self.prompt:
            raise UserError(self.env._('Prompt cannot be empty.'))

        # Extract plain Python values ONCE at the start
        num = min(int(self.num_variants or 2), 4)
        provider = str(self.ai_provider or '')
        style = str(self.image_style or '')
        size = str(self.image_size or '1024x1024')
        enhance_desc = str(self.enhancement_description or '')


        existing_b64 = None
        if self.enhance_existing and self.product_id.image_1920:
            existing_b64 = self.product_id.image_1920

        provider_map = {
            'openai': self._generate_openai,
            'stability': self._generate_stability,
            'gemini': self._generate_gemini,
        }
        generator = provider_map.get(provider)
        if not generator:
            raise UserError(
                self.env._('Unknown AI provider: %s', provider)
            )

        try:
            b64_images = generator(
                prompt=str(self.prompt),
                num_variants=num,
                image_size=size,
                existing_image=existing_b64,
                enhance_desc=enhance_desc,
            )
        except UserError:
            raise
        except Exception as e:
            raise UserError(
                self.env._('Image generation failed: %s', str(e))
            )

        # ── Log success (non-critical) ─────────────────────────────
        self._safe_log(status='success')

        # ── Remove old lines ───────────────────────────────────────
        self.generated_image_ids.unlink()

        provider_label, style_label = self._get_selection_labels()

        for idx, b64_data in enumerate(b64_images):
            if not b64_data:
                continue
            self.env['product.ai.image.line'].create({
                'wizard_id': self.id,
                'image': b64_data,
                'image_name': f'ai_product_{idx + 1}.png',
                'provider_used': provider_label,
                'style_used': style_label,
            })

        self.state = 'generated'
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'smart.product.image.generator',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }

    def action_apply_image(self, line_id):
        """Apply a generated image to the product or submit for manager approval."""
        self.ensure_one()

        _logger.info(
            "action_apply_image called. Wizard ID=%s, Line ID=%s",
            self.id,
            line_id,
        )

        line = self.env['product.ai.image.line'].browse(int(line_id))
        if not line.exists() or line.wizard_id.id != self.id:
            raise UserError(self.env._('Invalid image selection.'))

        if self._is_approval_required():
            self._safe_log(
                status='pending_approval',
                image_data=line.image,
                image_applied=False,
            )
            self.state = 'pending_approval'
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'smart.product.image.generator',
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
                'context': self.env.context,
            }

        provider_label, style_label = self._get_selection_labels()
        self.product_id._apply_ai_generated_image(
            image_data=line.image,
            provider_label=provider_label,
            style_label=style_label,
            size=self.image_size or '',
        )
        self._safe_log(
            status='success',
            image_data=line.image,
            image_applied=True,
        )
        self.state = 'applied'

        # Reload the page so the new product image is immediately visible.
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def action_generate_more(self):
        """Generate additional image variants using the current settings."""
        self.ensure_one()
        return self.action_generate_images()

    def action_bulk_generate(self):
        """Generate and apply (or submit for approval) AI images for multiple products."""
        self.ensure_one()
        products = self.bulk_product_ids
        if self.bulk_skip_existing:
            products = products.filtered(lambda p: not p.image_1920)
        if not products:
            raise UserError(self.env._('No products to process.'))

        approval_required = self._is_approval_required()
        provider = str(self.ai_provider or '')
        size = str(self.image_size or '1024x1024')
        log_lines = []
        success_count = 0
        pending_count = 0
        failed_count = 0
        skipped_count = len(self.bulk_product_ids) - len(products)

        provider_map = {
            'openai': self._generate_openai,
            'stability': self._generate_stability,
            'gemini': self._generate_gemini,
        }
        generator = provider_map.get(provider)
        if not generator:
            raise UserError(
                self.env._('Unknown AI provider: %s', provider)
            )

        for product in products:
            try:
                self.product_id = product
                self._compute_ai_prompt()
                b64_images = generator(
                    prompt=str(self.prompt or ''),
                    num_variants=1,
                    image_size=size,
                )
                if b64_images and b64_images[0]:
                    if approval_required:
                        self._safe_log(
                            status='pending_approval',
                            image_data=b64_images[0],
                            image_applied=False,
                        )
                        pending_count += 1
                        log_lines.append(
                            f'⏳ {product.name} (pending approval)'
                        )
                    else:
                        product._apply_ai_generated_image(
                            image_data=b64_images[0],
                            provider_label=provider,
                            size=size,
                            is_bulk=True,
                        )
                        self._safe_log(
                            status='success',
                            image_data=b64_images[0],
                            image_applied=True,
                        )
                        success_count += 1
                        log_lines.append(f'✓ {product.name}')
            except Exception as e:
                failed_count += 1
                log_lines.append(
                    f'✗ {product.name}: {str(e)[:80]}'
                )
                _logger.warning(
                    'Bulk failed for %s: %s', product.name, e
                )

        if approval_required:
            if pending_count:
                self.state = 'pending_approval'
            self.bulk_progress_log = (
                f'Pending Approval: ⏳{pending_count} ✗{failed_count} '
                f'⊘{skipped_count}\n' + '\n'.join(log_lines)
            )
            summary_msg = (
                f'⏳ {pending_count} pending approval  ✗ {failed_count} failed  '
                f'⊘ {skipped_count} skipped'
            )
            title = self.env._('Bulk Submitted for Approval')
        else:
            self.bulk_progress_log = (
                f'Complete: ✓{success_count} ✗{failed_count} '
                f'⊘{skipped_count}\n' + '\n'.join(log_lines)
            )
            summary_msg = (
                f'✓ {success_count} OK  ✗ {failed_count} failed  '
                f'⊘ {skipped_count} skipped'
            )
            title = self.env._('Bulk Complete')

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': summary_msg,
                'type': (
                    'success' if not failed_count else 'warning'
                ),
                'sticky': True,
            },
        }
