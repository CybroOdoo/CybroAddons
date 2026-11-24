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
from markupsafe import escape

from odoo import models
from odoo.tools import BinaryBytes, file_open

# The Shop mega menu lists a few categories (one of them is the feature card);
# the others stay one click away through the Shop all link.
NUTIVO_MEGA_MENU_LIMIT = 4

NUTIVO_TILE_CLASSES = (
    'o_wsale_products_opt_layout_catalog '
    'o_wsale_products_opt_design_thumbs '
    'o_wsale_products_opt_name_color_regular '
    'o_wsale_products_opt_rounded_4 o_wsale_products_opt_thumb_4_5 '
    'o_wsale_products_opt_has_rating '
    'o_wsale_products_opt_thumb_cover o_wsale_products_opt_has_cta '
    'o_wsale_products_opt_actions_inline o_wsale_products_opt_actions_subtle '
    'o_wsale_products_opt_has_wishlist '
    'o_wsale_products_opt_wishlist_fixed '
    'o_wsale_products_opt_img_secondary_show o_wsale_products_opt_img_hover_zoom_in_light'
)
# Placeholder key of the footer links and the public category it points to.
NUTIVO_CATEGORIES = {
    'nuts': 'Nuts',
    'dried': 'Dates & Dried Fruits',
    'mixes': 'Trail Mixes',
    'hampers': 'Gift Hampers',
}


class ThemeUtils(models.AbstractModel):
    """Configure the website the way Nutivo is designed on theme install."""
    _inherit = 'theme.utils'

    def _theme_nutivo_post_copy(self, mod):
        """Set the header and shop defaults of the Nutivo design.

        Everything set here stays editable from the website builder. No
        product, category or review is created: the shop keeps the
        data of the website.
        """
        self._nutivo_configure_views()
        self._nutivo_configure_header()
        self._nutivo_configure_shop()
        website = self.env.website
        with file_open('theme_nutivo/static/src/img/logo.png', 'rb') as logo:
            website.logo = BinaryBytes(logo.read())
        with file_open('theme_nutivo/static/src/img/favicon.ico',
                       'rb') as favicon:
            website.favicon = BinaryBytes(favicon.read())
        website.write({
            'shop_ppr': 3,
            'shop_ppg': 20,
            'shop_gap': '24px',
            'shop_opt_products_design_classes': NUTIVO_TILE_CLASSES,
            'wishlist_opt_products_design_classes': NUTIVO_TILE_CLASSES,
            'wishlist_grid_columns': 4,
            'wishlist_gap': '24px',
        })
        self._nutivo_resolve_placeholders(website)
        self._nutivo_remove_default_menus(website)
        self._nutivo_build_mega_menu(website)

    def _nutivo_configure_header(self):
        """Start from the header of the Nutivo design, all of it standard.

        The menu is aligned right, the header goes away when scrolling down
        and comes back when scrolling up, the wishlist link always shows, and
        the call to action and the text of the header are left out. They are
        the options of the website builder and stay changeable there.
        """
        self.enable_view('website.template_header_default_align_right')
        self.disable_view('website.header_visibility_standard')
        self.enable_view('website.header_visibility_disappears')
        for xml_id in (
                'website.header_call_to_action',
                'website.header_text_element',
                'website_sale.header_hide_empty_wishlist_link',
        ):
            self.disable_view(xml_id)

    def _nutivo_configure_shop(self):
        """Start from the shop sidebar of the design: every filter group is
        collapsible. The options stay changeable in the website builder."""
        for xml_id in (
                'website_sale.products_attributes_collapsible',
                'website_sale.products_categories_list_collapsible',
        ):
            self.enable_view(xml_id)

    def _nutivo_build_mega_menu(self, website):
        """Turn the Shop menu into a mega menu listing the shop categories.

        The content is a regular mega menu of the website builder, written once
        from the published categories: the builder edits it afterwards like any
        mega menu. A Shop menu that already is a mega menu is left alone.

        :param website: the website the theme is installed on.
        """
        shop_menu = website.menu_id.child_id.filtered(
            lambda m: m.url == '/shop' and not m.is_mega_menu)[:1]
        categories = website._nutivo_categories(limit=NUTIVO_MEGA_MENU_LIMIT)
        if not shop_menu or not categories:
            return
        feature = next(
            (c for c in categories if 'hamper' in c['name'].lower()),
            categories[-1])
        items = ''.join(
            '<li><a class="nv-mega__item" href="{url}">'
            '<img src="{image}" alt="" loading="lazy" width="56" height="56"/>'
            '<span class="nv-mega__text"><span class="nv-mega__name">{name}</span>'
            '<span class="nv-mega__desc">{description}</span></span>'
            '<span class="nv-mega__count">{count}</span></a></li>'.format(
                **{k: escape(str(v)) for k, v in category.items()})
            for category in categories if category is not feature)
        shop_menu.write({
            'mega_menu_classes': 'nv-mega-menu',
            'mega_menu_content': (
                '<section class="s_mega_menu_nutivo pt16 pb16" data-name="Shop Mega Menu">'
                '<div class="container"><div class="nv-mega__inner">'
                '<div class="nv-mega__list">'
                '<p class="nv-mega__label">{label}</p>'
                '<ul>{items}</ul>'
                '<a class="nv-mega__all" href="/shop">{all_products}</a>'
                '</div>'
                '<a class="nv-mega__feature" href="{furl}">'
                '<img src="{fimage}" alt="" loading="lazy"/>'
                '<span class="nv-mega__feature-body">'
                '<span class="nv-mega__feature-tag">{tag}</span>'
                '<span class="nv-mega__feature-name">{fname}</span>'
                '<span class="nv-mega__feature-link">{fdesc}</span>'
                '</span></a>'
                '</div></div></section>'
            ).format(
                items=items,
                label=escape(self.env._('Shop by category')),
                all_products=escape(self.env._('Shop all products')),
                tag=escape(self.env._('Gifting')),
                furl=escape(feature['url']),
                fimage=escape(feature['image'].replace('image_256', 'image_1024')),
                fname=escape(feature['name']),
                fdesc=escape(feature['description']),
            ),
        })

    def _nutivo_configure_views(self):
        """Enable the eCommerce options the Nutivo pages rely on: the price
        and highlight filters of the shop sidebar and the customer reviews
        shown by the product cards."""
        for xml_id in (
                'website.footer_custom',
                'website_sale.filter_products_price',
                'website_sale.filter_products_tags',
                'website_sale.product_comment',
        ):
            self.enable_view(xml_id)

    def _nutivo_resolve_placeholders(self, website):
        """Replace the record placeholders of the Nutivo views by real ones.

        Page views are static HTML so that the website builder can edit them,
        which means the newsletter list and the category links are only known
        once the theme is on a website.

        :param website: the website the theme is installed on.
        """
        mailing_list = self.env.ref(
            'mass_mailing.mailing_list_data', raise_if_not_found=False)
        replacements = {
            'nutivo_mailing_list': str(mailing_list.id if mailing_list else 0),
        }
        Category = self.env['product.public.category'].sudo()
        for key, name in NUTIVO_CATEGORIES.items():
            category = Category.search([('name', '=', name)], limit=1)
            replacements['nutivo_category_{}'.format(key)] = (
                category.website_url if category else '/shop')
        views = self.env['ir.ui.view'].with_context(active_test=False).search([
            ('key', '=like', 'theme_nutivo.%'),
            ('website_id', '=', website.id),
        ])
        for view in views.filtered(lambda v: any(
                key in (v.arch_db or '') for key in replacements)):
            arch = view.arch_db
            for placeholder, value in replacements.items():
                arch = arch.replace(placeholder, value)
            # Written as a user change so that a theme update does not bring
            # the placeholders back.
            view.arch = arch

    def _nutivo_remove_default_menus(self, website):
        """Remove the default entries that the Nutivo navigation replaces.

        The navigation is Home, Our Story, Shop and Contact. Only
        untouched default entries are removed.

        :param website: the website the theme is installed on.
        """
        self.env['website.menu'].search([
            ('website_id', '=', website.id),
            ('parent_id', '=', website.menu_id.id),
            ('theme_template_id', '=', False),
            ('url', '=', '/blog'),
            ('child_id', '=', False),
        ]).unlink()
