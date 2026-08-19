# -- coding: utf-8 --
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
import json
import base64

from odoo import http
from odoo.http import request


class WebsiteProductDesigner(http.Controller):
    """Handle website routes for the product designer.

        This controller provides endpoints for displaying designable products and
        categories, managing customer customizations, handling design templates,
        uploading images, configuring design areas, and adding customized products
        to the shopping cart.
        """

    @http.route('/shop/designer', type='http', auth='public', website=True, sitemap=True)
    def designer_categories(self, **kwargs):
        """Display all design categories."""
        # Get public categories that have at least one designable product
        all_cats = request.env['product.public.category'].sudo().search([])
        categories = all_cats.filtered(
            lambda c: request.env['product.template'].sudo().search_count([
                ('design_category_id', '=', c.id),
                ('is_designable', '=', True),
                ('is_published', '=', True),
            ]) > 0
        )
        return request.render('website_product_customizer.designer_categories_page', {
            'categories': categories,
        })

    @http.route('/shop/designer/category/<int:category_id>', type='http', auth='public',
                website=True, sitemap=True)
    def designer_category_products(self, category_id, **kwargs):
        """Display products in a design category."""
        category = request.env['product.public.category'].sudo().browse(category_id)
        if not category.exists():
            return request.redirect('/shop/designer')

        products = request.env['product.template'].sudo().search([
            ('design_category_id', '=', category_id),
            ('is_designable', '=', True),
            ('is_published', '=', True),
        ])
        return request.render('website_product_customizer.designer_category_products_page', {
            'category': category,
            'products': products,
        })

    @http.route('/shop/designer/<int:product_id>', type='http', auth='public',
                website=True, sitemap=True)
    def designer_page(self, product_id, **kwargs):
        """Display the product designer page."""
        product = request.env['product.template'].sudo().browse(product_id)
        if not product.exists() or not product.is_designable:
            return request.redirect('/shop')

        # Capture the selected variant ID from query parameters
        variant_raw = kwargs.get('variant_id', '0')
        variant_id = int(variant_raw.split('?')[0]) if variant_raw else 0

        # Resolve the selected variant
        selected_variant = None
        if variant_id:
            selected_variant = request.env['product.product'].sudo().browse(variant_id)
            if not selected_variant.exists() or selected_variant.product_tmpl_id.id != product.id:
                selected_variant = None

        # Default to the first variant if none selected
        if not selected_variant:
            selected_variant = product.product_variant_ids[:1]

        # Build variant data for the variant selector (when product has multiple variants)
        variants = product.product_variant_ids
        has_variants = len(variants) > 1
        variant_data = []
        if has_variants:
            for v in variants:
                attr_names = v.product_template_attribute_value_ids.mapped('name')
                variant_data.append({
                    'id': v.id,
                    'name': ', '.join(attr_names) if attr_names else v.display_name,
                    'price': v.lst_price,
                    'selected': v.id == selected_variant.id if selected_variant else False,
                })

        # Use variant-specific price
        variant_price = selected_variant.lst_price if selected_variant else product.list_price

        # Get effective design config from the variant (falls back to template)
        design_config = selected_variant._get_design_config() if selected_variant else {}

        # Fetch fonts: use variant/template-specific fonts, or all active fonts
        config_fonts = design_config.get('design_font_ids')
        if config_fonts:
            fonts = config_fonts
        else:
            fonts = request.env['product.design.font'].sudo().search([('active', '=', True)])

        # Check if the customer has a saved design for this product/variant
        saved_customization = self._get_saved_customization(
            product_id, variant_id=selected_variant.id if selected_variant else 0
        )
        saved_customization_id = saved_customization.id if saved_customization else 0

        # Check if user is an internal/admin user who can configure the template
        is_admin_user = request.env.user.has_group('base.group_user')

        return request.render('website_product_customizer.designer_page', {
            'product': product,
            'selected_variant': selected_variant,
            'variant_data': variant_data,
            'has_variants': has_variants,
            'variant_price': variant_price,
            'design_config': design_config,
            'fonts': fonts,
            'bg_colors': design_config.get('design_bg_color_ids', product.design_bg_color_ids),
            'text_colors': design_config.get('design_text_color_ids', product.design_text_color_ids),
            'saved_customization_id': saved_customization_id,
            'is_admin_user': is_admin_user,
            'variant_id': selected_variant.id if selected_variant else 0,
        })

    def _get_saved_customization(self, product_id, variant_id=0):
        """Return the latest saved/draft customization for the current customer and product.

        When variant_id is provided, first tries to find a design for that
        specific variant, then falls back to any design for the template.
        """
        partner_id = request.env.user.partner_id.id if not request.env.user._is_public() else False
        session_id = request.httprequest.cookies.get('session_id', '') if not partner_id else ''

        base_domain = [
            ('product_tmpl_id', '=', int(product_id)),
            ('state', 'in', ['draft', 'saved']),
        ]
        if partner_id:
            base_domain.append(('partner_id', '=', partner_id))
        else:
            base_domain.append(('session_id', '=', session_id))

        Customization = request.env['product.design.customization'].sudo()

        # Try variant-specific design first
        if variant_id:
            result = Customization.search(
                base_domain + [('product_id', '=', int(variant_id))],
                order='write_date desc', limit=1,
            )
            if result:
                return result

        # Fall back to any design for this template
        return Customization.search(base_domain, order='write_date desc', limit=1)

    @http.route('/shop/designer/save', type='json', auth='public', website=True)
    def save_design(self, product_id, design_data,
                    quantity=1, customization_id=None, variant_id=None, **kwargs):
        """Save (upsert) the customer's design customization.

        If a customization_id is provided (or a draft/saved record already exists
        for this customer+product), the existing record is updated instead of
        creating a new one.  This ensures one saved draft per customer per product.
        """
        product = request.env['product.template'].sudo().browse(int(product_id))
        if not product.exists():
            return {'error': 'Product not found'}

        partner_id = request.env.user.partner_id.id if not request.env.user._is_public() else False
        session_id = request.httprequest.cookies.get('session_id', '') if not partner_id else ''

        if isinstance(design_data, str):
            design_data = json.loads(design_data)

        vals = {
            'product_tmpl_id': product.id,
            'partner_id': partner_id,
            'session_id': session_id,
            'design_json': json.dumps(design_data),
            'quantity': int(quantity),
            'state': 'saved',
        }

        # Store the variant reference if provided
        if variant_id:
            variant = request.env['product.product'].sudo().browse(int(variant_id))
            if variant.exists() and variant.product_tmpl_id.id == product.id:
                vals['product_id'] = variant.id


        preview_image = kwargs.get('preview_image')
        if preview_image:
            try:
                if ',' in preview_image:
                    preview_image = preview_image.split(',')[1]
                vals['preview_image'] = preview_image
            except Exception:
                pass

        preview_image_back = kwargs.get('preview_image_back')
        if preview_image_back:
            try:
                if ',' in preview_image_back:
                    preview_image_back = preview_image_back.split(',')[1]
                vals['preview_image_back'] = preview_image_back
            except Exception:
                pass

        customization_lines = []

        # HANDLE FABRIC.JS DATA (New Format)
        if isinstance(design_data, dict) and ('objects' in design_data or 'front' in design_data):
            # The design data might just be the canvas JSON (with 'objects'),
            # or a combined { front: {...}, back: {...} } structure.
            sides_to_process = []
            if 'objects' in design_data:
                sides_to_process.append(design_data['objects'])
            if 'front' in design_data and isinstance(design_data['front'], dict):
                sides_to_process.append(design_data['front'].get('objects', []))
            if 'back' in design_data and isinstance(design_data['back'], dict):
                sides_to_process.append(design_data['back'].get('objects', []))

            for objects_list in sides_to_process:
                for obj in objects_list:
                    if obj.get('isPlaceholder') or obj.get('isGuide') or obj.get('isDesignAreaBg'):
                        continue

                    # Handle Text Objects
                    if obj.get('type') in ('text', 'i-text', 'textbox'):
                        line_vals = {
                            'custom_text': obj.get('text', ''),
                            'font_family': obj.get('fontFamily', ''),
                            'font_size': int(obj.get('fontSize', 0)),
                            'font_color': obj.get('fill', '#000000'),
                            'text_alignment': obj.get('textAlign', 'center'),
                            'is_bold': obj.get('fontWeight') == 'bold',
                            'is_italic': obj.get('fontStyle') == 'italic',
                            'is_underline': obj.get('underline', False),
                            'pos_x': obj.get('left', 0),
                            'pos_y': obj.get('top', 0),
                            'custom_width': obj.get('width', 0) * obj.get('scaleX', 1),
                            'custom_height': obj.get('height', 0) * obj.get('scaleY', 1),
                            'custom_rotation': obj.get('angle', 0),
                        }
                        customization_lines.append((0, 0, line_vals))

                    # Handle Image Objects
                    elif obj.get('type') == 'image':
                        src = obj.get('src', '')
                        image_data = False
                        if src.startswith('data:image'):
                            try:
                                # Extract base64 part
                                image_data = src.split(',')[1]
                            except IndexError:
                                pass

                        line_vals = {
                            'custom_image': image_data,
                            'pos_x': obj.get('left', 0),
                            'pos_y': obj.get('top', 0),
                            'custom_width': obj.get('width', 0) * obj.get('scaleX', 1),
                            'custom_height': obj.get('height', 0) * obj.get('scaleY', 1),
                            'custom_rotation': obj.get('angle', 0),
                        }
                        customization_lines.append((0, 0, line_vals))



        vals['customization_line_ids'] = customization_lines

        # --- UPSERT: update existing draft/saved record if one exists ---
        existing = None
        if customization_id:
            existing = request.env['product.design.customization'].sudo().browse(
                int(customization_id)
            )
            if not existing.exists() or existing.state not in ('draft', 'saved'):
                existing = None

        if not existing:
            existing = self._get_saved_customization(product_id)

        if existing:
            # Replace customization lines and update fields
            vals['customization_line_ids'] = [(5, 0, 0)] + customization_lines
            existing.write(vals)
            customization = existing
        else:
            customization = request.env['product.design.customization'].sudo().create(vals)

        return {
            'success': True,
            'customization_id': customization.id,
        }

    @http.route('/shop/designer/load_saved', type='json', auth='public', website=True)
    def load_saved_design(self, product_id, variant_id=None, **kwargs):
        """Return the customer's latest saved design JSON for a product/variant.

        Returns an empty dict if no saved design exists.
        """
        customization = self._get_saved_customization(
            product_id, variant_id=int(variant_id) if variant_id else 0
        )
        if not customization:
            return {}

        return {
            'customization_id': customization.id,
            'design_json': customization.design_json,
            'variant_id': customization.product_id.id if customization.product_id else 0,
            'quantity': customization.quantity,
        }

    @http.route('/shop/designer/save_area_config', type='json', auth='user', website=True)
    def save_area_config(self, product_id, config_data, side='front',
                         variant_id=None, **kwargs):
        """Save the configured design area.

        When a variant_id is provided and the variant has design_variant_override
        enabled, the area config is saved to the variant. Otherwise it is saved
        to the product template (affecting all variants).
        """
        if not request.env.user.has_group('base.group_user'):
            return {'error': 'Unauthorized'}

        product = request.env['product.template'].sudo().browse(int(product_id))
        if not product.exists():
            return {'error': 'Product not found'}

        # Determine write target: variant (if override enabled) or template
        target = product
        if variant_id:
            variant = request.env['product.product'].sudo().browse(int(variant_id))
            if variant.exists() and variant.product_tmpl_id.id == product.id and variant.design_variant_override:
                target = variant

        try:
            if target._name == 'product.product':
                # Write to variant-specific fields
                prefix = 'variant_design_area_back_' if side == 'back' else 'variant_design_area_'
                target.write({
                    prefix + 'left': float(config_data.get('left', 0)),
                    prefix + 'top': float(config_data.get('top', 0)),
                    prefix + 'width': float(config_data.get('width', 100)),
                    prefix + 'height': float(config_data.get('height', 100)),
                })
            else:
                # Write to template fields
                if side == 'back':
                    target.write({
                        'design_area_back_left': float(config_data.get('left', 0)),
                        'design_area_back_top': float(config_data.get('top', 0)),
                        'design_area_back_width': float(config_data.get('width', 100)),
                        'design_area_back_height': float(config_data.get('height', 100)),
                    })
                else:
                    target.write({
                        'design_area_left': float(config_data.get('left', 0)),
                        'design_area_top': float(config_data.get('top', 0)),
                        'design_area_width': float(config_data.get('width', 100)),
                        'design_area_height': float(config_data.get('height', 100)),
                    })
            return {'success': True}
        except Exception as e:
            return {'error': str(e)}

    @http.route('/shop/designer/add_to_cart', type='json', auth='public', website=True)
    def designer_add_to_cart(self, product_id, customization_id, quantity=1, variant_id=None, **kwargs):
        """Add the designed product to the cart."""
        product_tmpl = request.env['product.template'].sudo().browse(int(product_id))
        if not product_tmpl.exists():
            return {'error': 'Product not found'}

        customization = request.env['product.design.customization'].sudo().browse(
            int(customization_id)
        )
        if not customization.exists():
            return {'error': 'Design not found'}

        # Use the specific variant if provided, otherwise fall back to the first variant
        product = None
        if variant_id:
            product = request.env['product.product'].sudo().browse(int(variant_id))
            # Validate the variant belongs to this template
            if not product.exists() or product.product_tmpl_id.id != product_tmpl.id:
                product = None
        if not product:
            product = product_tmpl.product_variant_ids[:1]
        if not product:
            return {'error': 'No product variant found'}


        # Build description
        desc_parts = [product.name]

        for line in customization.customization_line_ids:
            if line.custom_text:
                desc_parts.append(f"Custom Text: {line.custom_text[:80]}")
            elif line.custom_image:
                desc_parts.append("Custom Image: [Image Uploaded]")


        sale_order = request.website.sale_get_order(force_create=True)

        # Add to cart — force a new line so each customization stays separate
        cart_values = sale_order._cart_update(
            product_id=product.id,
            add_qty=int(quantity),
            force_new_design_line=True,
        )

        # Link customization
        if cart_values.get('line_id'):
            so_line = request.env['sale.order.line'].sudo().browse(cart_values['line_id'])
            so_line.write({
                'design_customization_id': customization.id,
                'name': '\n'.join(desc_parts),
            })

            customization_vals = {
                'state': 'ordered',
                'sale_order_line_id': so_line.id,
                'product_id': product.id,
            }
            preview_img = kwargs.get('preview_image')
            if preview_img:
                try:
                    if ',' in preview_img:
                        preview_img = preview_img.split(',')[1]
                    customization_vals['preview_image'] = preview_img
                except Exception:
                    pass

            preview_img_back = kwargs.get('preview_image_back')
            if preview_img_back:
                try:
                    if ',' in preview_img_back:
                        preview_img_back = preview_img_back.split(',')[1]
                    customization_vals['preview_image_back'] = preview_img_back
                except Exception:
                    pass

            customization.write(customization_vals)

        return {
            'success': True,
            'cart_quantity': sale_order.cart_quantity,
        }

    @http.route('/shop/designer/upload_image', type='json', auth='public', website=True)
    def upload_design_image(self, image_data, **kwargs):
        """Handle image upload for the designer."""
        if not image_data:
            return {'error': 'No image data provided'}

        # Validate image
        max_size = int(request.env['ir.config_parameter'].sudo().get_param(
            'website_product_customizer.max_upload_size', 10
        ))

        # Convert base64 to check size
        try:
            image_bytes = base64.b64decode(image_data.split(',')[1] if ',' in image_data else image_data)
            size_mb = len(image_bytes) / (1024 * 1024)
            if size_mb > max_size:
                return {'error': f'Image too large. Maximum size is {max_size}MB'}
        except Exception:
            return {'error': 'Invalid image data'}

        return {
            'success': True,
            'image_data': image_data,
        }

    @http.route('/shop/designer/get_templates', type='json', auth='public', website=True)
    def get_design_templates(self, product_id=None, category_id=None, **kwargs):
        """Get design templates for a product or category."""
        domain = [('active', '=', True)]
        if product_id:
            domain.append(('product_tmpl_id', '=', int(product_id)))
        elif category_id:
            domain.append(('design_category_id', '=', int(category_id)))

        templates = request.env['product.design.template'].sudo().search(domain, limit=20)

        return [{
            'id': t.id,
            'name': t.name,
            'style': t.template_style,
            'preview_url': f'/web/image/product.design.template/{t.id}/preview_image',
            'design_data': t.design_data,
            'color_primary': t.color_primary,
            'color_secondary': t.color_secondary,
            'is_premium': t.is_premium,
        } for t in templates]

    @http.route('/shop/designer/save_as_template', type='json', auth='user', website=True)
    def save_as_template(self, product_id, design_data, template_name='', preview_image=None, preview_image_back=None, **kwargs):
        """Save the current canvas design as a reusable design template. Admin only."""
        if not request.env.user.has_group('base.group_user'):
            return {'error': 'Unauthorized — only internal users can save templates.'}

        product = request.env['product.template'].sudo().browse(int(product_id))
        if not product.exists():
            return {'error': 'Product not found'}

        if not template_name:
            template_name = f"{product.name} — Template"

        # Prepare preview image binary (front)
        preview_binary = False
        if preview_image:
            try:
                if ',' in preview_image:
                    preview_image = preview_image.split(',')[1]
                preview_binary = preview_image
            except Exception:
                pass

        # Prepare preview image binary (back)
        preview_back_binary = False
        if preview_image_back:
            try:
                if ',' in preview_image_back:
                    preview_image_back = preview_image_back.split(',')[1]
                preview_back_binary = preview_image_back
            except Exception:
                pass

        vals = {
            'name': template_name,
            'design_data': design_data if isinstance(design_data, str) else json.dumps(design_data),
            'preview_image': preview_binary,
            'preview_image_back': preview_back_binary,
            'product_tmpl_id': product.id,
            'design_category_id': product.design_category_id.id if product.design_category_id else False,
            'active': True,
        }

        try:
            template = request.env['product.design.template'].sudo().create(vals)
            return {
                'success': True,
                'template_id': template.id,
                'template_name': template.name,
            }
        except Exception as e:
            return {'error': str(e)}

    @http.route('/shop/designer/update_template', type='json', auth='user', website=True)
    def update_template(self, template_id, design_data, template_name='',
                        preview_image=None, preview_image_back=None, **kwargs):
        """Update an existing design template with new canvas data. Admin only."""
        if not request.env.user.has_group('base.group_user'):
            return {'error': 'Unauthorized — only internal users can update templates.'}

        template = request.env['product.design.template'].sudo().browse(int(template_id))
        if not template.exists():
            return {'error': 'Template not found'}

        vals = {
            'design_data': design_data if isinstance(design_data, str) else json.dumps(design_data),
        }

        if template_name:
            vals['name'] = template_name

        # Update preview image (front)
        if preview_image:
            try:
                if ',' in preview_image:
                    preview_image = preview_image.split(',')[1]
                vals['preview_image'] = preview_image
            except Exception:
                pass

        # Update preview image (back)
        if preview_image_back:
            try:
                if ',' in preview_image_back:
                    preview_image_back = preview_image_back.split(',')[1]
                vals['preview_image_back'] = preview_image_back
            except Exception:
                pass

        try:
            template.write(vals)
            return {
                'success': True,
                'template_id': template.id,
                'template_name': template.name,
            }
        except Exception as e:
            return {'error': str(e)}

    @http.route('/shop/designer/get_variant_info', type='json', auth='public', website=True)
    def get_variant_info(self, product_id, variant_id, **kwargs):
        """Return variant-specific info including design config for AJAX updates.

        This endpoint is called when the user changes the variant selector in
        the designer.  It returns everything the JS needs to update the canvas:
        price, images, design area, limits, front/back flag, etc.
        """
        product = request.env['product.template'].sudo().browse(int(product_id))
        if not product.exists():
            return {'error': 'Product not found'}

        variant = request.env['product.product'].sudo().browse(int(variant_id))
        if not variant.exists() or variant.product_tmpl_id.id != product.id:
            return {'error': 'Invalid variant'}

        config = variant._get_design_config()

        # Build image URLs — use variant model so computed fields give
        # variant-specific image when set, template image as fallback.
        front_image_url = '/web/image/product.product/%s/design_base_image' % variant.id
        if not variant.design_base_image:
            # No design base image at all — fall back to the main product image
            front_image_url = '/web/image/product.product/%s/image_1920' % variant.id

        back_image_url = ''
        if config.get('has_front_back'):
            back_image_url = '/web/image/product.product/%s/design_base_image_back' % variant.id

        # Serialize fonts for the frontend
        config_fonts = config.get('design_font_ids')
        if not config_fonts:
            config_fonts = request.env['product.design.font'].sudo().search([('active', '=', True)])
        fonts_data = [{
            'id': f.id,
            'name': f.name,
            'font_family_name': f.font_family_name,
            'provider': f.provider,
            'css_url': f.css_url,
        } for f in config_fonts]

        # Serialize colors
        bg_colors_data = [{
            'id': c.id, 'name': c.name, 'color_code': c.color_code,
        } for c in config.get('design_bg_color_ids', product.design_bg_color_ids)]

        text_colors_data = [{
            'id': c.id, 'name': c.name, 'color_code': c.color_code,
        } for c in config.get('design_text_color_ids', product.design_text_color_ids)]

        return {
            'success': True,
            'variant_id': variant.id,
            'price': variant.lst_price,
            'display_name': variant.display_name,
            # Images
            'front_image_url': front_image_url,
            'back_image_url': back_image_url,
            # Design area (front)
            'design_area_left': config.get('design_area_left', 0),
            'design_area_top': config.get('design_area_top', 0),
            'design_area_width': config.get('design_area_width', 100),
            'design_area_height': config.get('design_area_height', 100),
            # Design area (back)
            'design_area_back_left': config.get('design_area_back_left', 0),
            'design_area_back_top': config.get('design_area_back_top', 0),
            'design_area_back_width': config.get('design_area_back_width', 100),
            'design_area_back_height': config.get('design_area_back_height', 100),
            # Settings
            'has_front_back': config.get('has_front_back', False),
            'design_max_texts': config.get('design_max_texts', 0),
            'design_max_images': config.get('design_max_images', 0),
            'design_max_characters': config.get('design_max_characters', 0),
            'min_order_quantity': config.get('min_order_quantity', 1),
            'max_order_quantity': config.get('max_order_quantity', 10000),
            'production_time_days': config.get('production_time_days', 3),
            'design_instruction': config.get('design_instruction', ''),
            # Fonts & Colors
            'fonts': fonts_data,
            'bg_colors': bg_colors_data,
            'text_colors': text_colors_data,
        }
