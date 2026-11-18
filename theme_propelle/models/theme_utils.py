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
from odoo import models
from odoo.tools import BinaryBytes, file_open


class ThemeUtils(models.AbstractModel):
    """Configure the website the way Propelle is designed on theme install."""
    _inherit = 'theme.utils'

    def _theme_propelle_post_copy(self, mod):
        """Set the header defaults, logo and menus of the Propelle design.

        Everything set here stays editable from the website builder.
        """
        self._propelle_configure_header()
        website = self.env.website
        with file_open('theme_propelle/static/src/img/logo.png', 'rb') as logo:
            website.logo = BinaryBytes(logo.read())
        with file_open('theme_propelle/static/src/img/favicon.png',
                       'rb') as favicon:
            website.favicon = BinaryBytes(favicon.read())
        self._propelle_resolve_placeholders(website)
        self._propelle_configure_pages(website)

    def _propelle_configure_header(self):
        """Start from the header of the Propelle design, all of it standard.

        The default header template stays fixed while scrolling and keeps
        its call to action and the sign in link, which only shows to
        visitors who are not signed in. The page search and the text element
        are left out, as in the design. They are options of the website
        builder and stay changeable there.
        """
        self.enable_view('website.template_header_default')
        self.enable_view('website.footer_custom')
        self.disable_view('website.header_visibility_standard')
        self.enable_view('website.header_visibility_fixed')
        self.enable_view('website.header_call_to_action')
        self.enable_view('portal.user_sign_in')
        for xml_id in (
                'website.header_search_box',
                'website.header_text_element',
        ):
            self.disable_view(xml_id)

    def _propelle_resolve_placeholders(self, website):
        """Replace the record placeholders of the Propelle views by real ones.

        Page views are static HTML so that the website builder can edit them,
        which means the newsletter list is only known once the theme is on a
        website.

        :param website: the website the theme is installed on.
        """
        mailing_list = self.env.ref(
            'mass_mailing.mailing_list_data', raise_if_not_found=False)
        replacements = {
            'propelle_mailing_list': str(
                mailing_list.id if mailing_list else 0),
        }
        views = self.env['ir.ui.view'].with_context(active_test=False).search([
            ('key', '=like', 'theme_propelle.%'),
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

    def _propelle_configure_pages(self, website):
        """Put the header over the photo of the home page, and remove the
        default Contact menu: the design links the contact page from the call
        to action of the header.

        :param website: the website the theme is installed on.
        """
        self.set_page_option('header_overlay', True)
        self.env['website.menu'].search([
            ('website_id', '=', website.id),
            ('parent_id', '=', website.menu_id.id),
            ('theme_template_id', '=', False),
            ('url', '=', '/contactus'),
            ('child_id', '=', False),
        ]).unlink()
