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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import base64
import logging
import requests

from markupsafe import Markup

from odoo import models, fields, api
from odoo.tools import _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ProductAiImageLine(models.TransientModel):
    """Holds individual generated image variants returned from AI."""
    _name = 'product.ai.image.line'
    _description = 'AI Generated Image Line'

    wizard_id = fields.Many2one(
        'smart.product.image.generator',
        string='Wizard',
        required=True,
        ondelete='cascade',
    )
    image = fields.Binary(string='Generated Image', attachment=False)
    image_name = fields.Char(
        string='Image Name',
        default='ai_generated.png',
    )
    is_selected = fields.Boolean(string='Selected', default=False)
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
                _('Wizard session has expired. Please close and reopen.')
            )
        return wizard.action_apply_image(self.id)


class SmartProductImageGenerator(models.TransientModel):
    """Transient wizard model for AI image generation."""
    _name = 'smart.product.image.generator'
    _description = 'Smart Product Image Generator Wizard'

    product_id = fields.Many2one(
        'product.template',
        string='Product',
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
        string='Image Style',
        required=True,
        default='professional',
    )
    image_size = fields.Selection(
        selection=[
            ('1024x1024', '1024 x 1024 (Square)'),
            ('1792x1024', '1792 x 1024 (Landscape)'),
            ('1024x1792', '1024 x 1792 (Portrait)'),
        ],
        string='Image Size',
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
            ('applied', 'Applied'),
        ],
        string='State',
        default='draft',
    )
    bulk_mode = fields.Boolean(string='Bulk Mode', default=False)
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
        ICP = self.env['ir.config_parameter'].sudo()
        brand_dna = ICP.get_param(
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
            price = product.list_price
            if price < 50:
                price_tier = 'budget-friendly product'
            elif price < 200:
                price_tier = 'mid-range product'
            else:
                price_tier = 'premium product'
            lines = [intro]
            if brand_dna:
                lines.append(brand_dna.strip())
            lines.append(f'Product: {product.name}')
            lines.append(
                'Category: '
                + (
                    product.categ_id.complete_name
                    or product.categ_id.name
                )
            )
            if attributes_str:
                lines.append(f'Attributes: {attributes_str}')
            if product.description_sale:
                lines.append(
                    f'Description: {product.description_sale[:300]}'
                )
            lines.append(f'This is a {price_tier}.')
            rec.prompt = '\n'.join(lines)

    @api.constrains('num_variants')
    def _check_num_variants(self):
        """Validate that the number of image variants is within limits."""
        for rec in self:
            if rec.num_variants < 1 or rec.num_variants > 4:
                raise ValidationError(
                    _('Number of variants must be between 1 and 4.')
                )

    # ── Helpers ───────────────────────────────────────────────────

    def _get_api_key(self, provider):
        """Retrieve the configured API key for the selected AI provider."""
        ICP = self.env['ir.config_parameter'].sudo()
        key_map = {
            'openai': 'smart_product_image_generator.openai_api_key',
            'stability': 'smart_product_image_generator.stability_api_key',
            'gemini': 'smart_product_image_generator.gemini_api_key',
        }
        key = ICP.get_param(key_map.get(provider, ''), '').strip()
        if not key:
            raise UserError(
                f'No API key configured for {provider}. '
                'Go to Settings → Technical → System Parameters.'
            )
        return key

    def _get_admin_user_id(self):
        """Return an administrator user ID for privileged operations."""
        if self.env.user.has_group('base.group_system'):
            return self.env.user.id
        admin_user = self.env['res.users'].sudo().search(
            [('active', '=', True), ('share', '=', False)],
            limit=1,
        )
        if admin_user:
            return admin_user.id
        return self.env.user.id

    def _to_b64_bytes(self, data):
        """Convert raw image bytes or b64 string to b64 bytes."""
        if not data:
            return False
        if isinstance(data, bytes):
            is_png = data[:8] == b'\x89PNG\r\n\x1a\n'
            is_jpg = data[:2] == b'\xff\xd8'
            if is_png or is_jpg:
                return base64.b64encode(data)
            return data
        if isinstance(data, str):
            return data.encode('utf-8')
        return data

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
        """Generate product images using the OpenAI DALL-E API."""
        api_key = self._get_api_key('openai')
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }
        size = (
            image_size
            if image_size in ('1024x1024', '1792x1024', '1024x1792')
            else '1024x1024'
        )
        full_prompt = prompt
        if enhance_desc:
            full_prompt = f'{prompt}\n\nEnhancement: {enhance_desc}'
        images = []
        for _ in range(int(num_variants)):
            payload = {
                'model': 'dall-e-3',
                'prompt': full_prompt,
                'n': 1,
                'size': size,
                'quality': 'hd',
                'response_format': 'url',
            }
            try:
                resp = requests.post(
                    'https://api.openai.com/v1/images/generations',
                    headers=headers,
                    json=payload,
                    timeout=120,
                )
                resp.raise_for_status()
                image_url = resp.json()['data'][0]['url']
                img_resp = requests.get(image_url, timeout=60)
                img_resp.raise_for_status()
                images.append(self._to_b64_bytes(img_resp.content))
            except requests.exceptions.HTTPError as e:
                error_body = str(e)
                try:
                    error_body = (
                        e.response.json()
                        .get('error', {})
                        .get('message', str(e))
                    )
                except Exception:
                    pass
                raise UserError(
                    f'OpenAI API error: {error_body}'
                )
            except UserError:
                raise
            except Exception as e:
                raise UserError(
                    f'OpenAI request failed: {str(e)}'
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
                    'input_image.png', existing_image, 'image/png'
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
                except Exception:
                    pass
                raise UserError(
                    f'Stability AI API error: {error_body}'
                )
            except UserError:
                raise
            except Exception as e:
                raise UserError(
                    f'Stability AI request failed: {str(e)}'
                )
        return images

    # ── Provider: Gemini ──────────────────────────────────────────

    def _generate_gemini(self, prompt, num_variants, image_size,
                          existing_image=None, enhance_desc=''):
        """Generate product images using the Google Gemini API."""
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
        for i in range(min(int(num_variants), 4)):
            content_parts = []
            if existing_image and enhance_desc:
                img_data = existing_image
                if isinstance(img_data, bytes):
                    img_data = img_data.decode('utf-8')
                content_parts.append({
                    'inlineData': {
                        'mimeType': 'image/png',
                        'data': img_data,
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
                except Exception:
                    pass
                raise UserError(
                    f'Google Gemini API error: {error_body}'
                )
            except UserError:
                raise
            except Exception as e:
                raise UserError(
                    f'Google Gemini request failed: {str(e)}'
                )
        if not images:
            raise UserError(_(
                'Gemini returned no images. Check your API key.'
            ))
        return images

    # ── Main actions ──────────────────────────────────────────────

    def action_generate_images(self):
        """Generate image variants from the selected AI provider."""
        self.ensure_one()

        if not self.prompt:
            raise UserError(_('Prompt cannot be empty.'))

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
                f'Unknown AI provider: {provider}'
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
                f'Image generation failed: {str(e)}'
            )

        # ── Log success (non-critical) ─────────────────────────────
        self._safe_log(status='success')

        # ── Remove old lines ───────────────────────────────────────
        self.generated_image_ids.unlink()


        _fields_desc = self.fields_get(['image_style', 'ai_provider'])
        style_label = dict(
            _fields_desc['image_style']['selection']
        ).get(style, style)
        provider_label = dict(
            _fields_desc['ai_provider']['selection']
        ).get(provider, provider)

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
        """Apply a specific generated image to the product."""
        self.ensure_one()

        _logger.info(
            "action_apply_image called. Wizard ID=%s, Line ID=%s",
            self.id,
            line_id,
        )

        line = self.env['product.ai.image.line'].browse(int(line_id))
        if not line.exists() or line.wizard_id.id != self.id:
            raise UserError(_('Invalid image selection.'))

        # Plain Python values
        ai_count = int(self.product_id.ai_generation_count or 0)

        _logger.info(
            "Applying AI image to product '%s' (ID=%s)",
            self.product_id.name,
            self.product_id.id,
        )

        # Apply image to product
        self.product_id.write({
            'image_1920': line.image,
            'ai_last_generated_date': fields.Datetime.now(),
            'ai_generation_count': ai_count + 1,
        })

        _logger.info(
            "Image written successfully to product '%s'",
            self.product_id.name,
        )

        # ── Post chatter log with the generated image ──────────────
        try:
            provider_labels = dict(
                self.fields_get(['ai_provider'])['ai_provider']['selection']
            )
            style_labels = dict(
                self.fields_get(['image_style'])['image_style']['selection']
            )
            provider_label = provider_labels.get(
                self.ai_provider, self.ai_provider
            )
            style_label = style_labels.get(
                self.image_style, self.image_style
            )
            body = Markup(
                '<b>AI Image Generated &amp; Applied</b><br/>'
                'Provider: {provider}<br/>'
                'Style: {style}<br/>'
                'Size: {size}<br/>'
                'Generation #: {count}'
            ).format(
                provider=provider_label,
                style=style_label,
                size=self.image_size,
                count=ai_count + 1,
            )
            image_bytes = base64.b64decode(line.image)
            self.product_id.message_post(
                body=body,
                attachments=[('ai_generated_image.png', image_bytes)],
            )
        except Exception:
            _logger.warning(
                'Chatter post failed for product %s (non-critical)',
                self.product_id.name,
                exc_info=True,
            )

        try:
            self._safe_log(
                status='success',
                image_data=line.image,
                image_applied=True,
            )
            _logger.info(
                "Image application log created successfully for product '%s'",
                self.product_id.name,
            )
        except Exception:
            _logger.exception(
                "Failed to create image application log for product '%s'",
                self.product_id.name,
            )
            raise

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
        """Generate and apply AI images for multiple products in bulk."""
        self.ensure_one()
        products = self.bulk_product_ids
        if self.bulk_skip_existing:
            products = products.filtered(lambda p: not p.image_1920)
        if not products:
            raise UserError(_('No products to process.'))

        provider = str(self.ai_provider or '')
        size = str(self.image_size or '1024x1024')
        log_lines = []
        success_count = 0
        failed_count = 0
        skipped_count = len(self.bulk_product_ids) - len(products)

        provider_map = {
            'openai': self._generate_openai,
            'stability': self._generate_stability,
            'gemini': self._generate_gemini,
        }
        generator = provider_map.get(provider)

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
                    ai_count = int(
                        product.ai_generation_count or 0
                    )
                    product.sudo().write({
                        'image_1920': b64_images[0],
                        'ai_last_generated_date': fields.Datetime.now(),
                        'ai_generation_count': ai_count + 1,
                    })
                    self._safe_log(
                        status='success',
                        image_data=b64_images[0],
                        image_applied=True,
                    )
                    try:
                        product.message_post(
                            body=Markup(
                                '<b>AI Image Generated &amp; Applied (Bulk)</b><br/>'
                                'Provider: {provider}<br/>'
                                'Size: {size}'
                            ).format(provider=provider, size=size),
                            attachments=[(
                                'ai_generated_image.png',
                                base64.b64decode(b64_images[0]),
                            )],
                        )
                    except Exception:
                        _logger.warning(
                            'Bulk chatter post failed for %s (non-critical)',
                            product.name,
                            exc_info=True,
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

        self.bulk_progress_log = (
            f'Complete: ✓{success_count} ✗{failed_count} '
            f'⊘{skipped_count}\n' + '\n'.join(log_lines)
        )
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Bulk Complete'),
                'message': f'✓ {success_count} OK  ✗ {failed_count} failed  ⊘ {skipped_count} skipped',
                'type': (
                    'success' if not failed_count else 'warning'
                ),
                'sticky': True,
            },
        }
