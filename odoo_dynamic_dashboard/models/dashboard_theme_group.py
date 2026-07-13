# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
import base64
import io
import logging

from PIL import Image

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DashboardThemeGroup(models.Model):
    """Model representing a visual theme configuration for dashboards."""
    _name = 'dashboard.theme.group'
    _description = 'Dashboard Theme Group'
    _order = 'sequence, name'

    @api.model
    def _default_sequence(self):
        """Find the maximum sequence and return it + 1."""
        last_rec = self.search([], limit=1, order='sequence desc')
        return (last_rec.sequence + 1) if last_rec else 1

    name = fields.Char(string='Theme Name', required=True, help='Name of the theme.')
    sequence = fields.Integer(string='Sequence', default=_default_sequence, help='Sequence order of the theme.')
    active = fields.Boolean(string='Active', default=True, help='Set to True if the theme is active.')

    # Colors
    background_color = fields.Char(string='Background Color', default='#F4F7F6', help='Main dashboard background color.')
    card_background_color = fields.Char(string='Card Background Color', default='#FFFFFF', help='Background color for dashboard cards (light mode only).')
    card_text_color = fields.Char(string='Card Text Color', default='#1a1a1a', help='Text color inside dashboard cards.')
    button_color = fields.Char(string='Button Color', default='#007BFF', help='Primary button color.')
    text_color = fields.Char(string='Text Color', default='#333333', help='Main text color.')
    sidebar_toggle_color = fields.Char(string='Sidebar Toggle Color', default='#FFFFFF', help='Color of the sidebar toggle button.')
    navbar_color = fields.Char(string='Navbar Color', default='#FFFFFF', help='Background color of the top navbar.')

    # Specific for Ocean Blue or others
    dashboard_card_color = fields.Char(string='Dashboard Card Color', default='#FFFFFF', help='Color applied to dashboard cards.')
    card_spacing = fields.Integer(string='Card Spacing (px)', default=15, help='Spacing between cards in pixels.')

    # Gradient options if needed
    is_gradient = fields.Boolean(string='Use Gradient', default=False, help='Enable gradient backgrounds for the theme.')
    gradient_color_1 = fields.Char(string='Gradient Color 1', help='First color of the gradient.')
    gradient_color_2 = fields.Char(string='Gradient Color 2', help='Second color of the gradient.')
    gradient_degree = fields.Integer(string='Gradient Degree', default=90, help='Angle of the gradient.')

    # Background Image
    background_image = fields.Binary(string='Background Image', attachment=True, help='Image to be used as background.')
    background_image_name = fields.Char(string='Image Name', help='Filename of the uploaded background image.')
    background_size = fields.Selection([
        ('cover', 'Cover (Fill)'),
        ('stretch', 'Stretch (Distort)'),
        ('auto', 'Auto (Original)')
    ], string='Background Fit', default='auto', help='How the background image should be displayed.')

    # Default color schemes for each theme
    is_default_theme = fields.Boolean(compute='_compute_is_default_theme', string='Is Default Theme', help='Indicates if this is a built-in default theme.')

    @api.depends('name')
    def _compute_is_default_theme(self):
        """Determine if the current theme is one of the built-in default themes."""
        default_themes = ['Light', 'Dark', 'Ocean Blue', 'Cyberpunk']
        for rec in self:
            rec.is_default_theme = rec.name in default_themes

    @api.onchange('background_image')
    def _onchange_background_image(self):
        """Reset background size to 'auto' when a new image is uploaded."""
        if self.background_image:
            self.background_size = 'auto'

    def action_analyse_from_company_logo(self):
        """Extract dominant colours from the active company's logo and apply them to this theme record."""
        self.ensure_one()
        company = self.env.company
        if not company.logo:
            raise UserError("The active company has no logo configured. Upload a logo on the company record first.")

        try:
            logo_bytes = base64.b64decode(company.logo)
        except Exception as exc:
            raise UserError("Couldn't decode the company logo: {}".format(exc))

        dominant = self._extract_dominant_colors(logo_bytes, num_colors=6)
        if not dominant:
            raise UserError("No usable brand colours could be extracted from the logo.")

        vals = self._derive_theme_palette(dominant)
        if not self.name:
            vals['name'] = "{} Brand Theme".format(company.name)
        self.write(vals)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Theme Generated',
                'message': 'Palette extracted from "{}" logo and applied.'.format(company.name),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    @staticmethod
    def _extract_dominant_colors(logo_bytes, num_colors=6):
        """Return a list of (R, G, B) tuples ordered by frequency, skipping
        near-white (likely background) and near-black noise pixels."""
        try:
            img = Image.open(io.BytesIO(logo_bytes))
        except Exception as exc:
            _logger.error("Failed to open logo image: %s", exc)
            return []

        # Flatten transparency onto white so transparent corners don't dominate.
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            bg = Image.new('RGB', img.size, (255, 255, 255))
            rgba = img.convert('RGBA')
            bg.paste(rgba, mask=rgba.split()[-1])
            img = bg
        else:
            img = img.convert('RGB')

        # Shrink for speed; quantize to a small palette using median-cut.
        img.thumbnail((150, 150))
        quantized = img.quantize(colors=max(num_colors * 4, 16), method=0)  # 0 = MEDIANCUT
        palette = quantized.getpalette() or []
        counts = quantized.getcolors() or []

        ordered = []
        for count, idx in sorted(counts, key=lambda x: -x[0]):
            r, g, b = palette[idx * 3:idx * 3 + 3]
            # Skip very light (background) and very dark (anti-alias) pixels.
            brightness = (r * 299 + g * 587 + b * 114) / 1000
            # Skip near-monochrome low-saturation tones too (helps logos with
            # heavy black/grey text dominating frequency).
            mx, mn = max(r, g, b), min(r, g, b)
            saturation = 0 if mx == 0 else (mx - mn) / mx
            if 25 < brightness < 235 and saturation > 0.15:
                ordered.append((r, g, b))
            if len(ordered) >= num_colors:
                break

        # If filtering was too strict (e.g. monochrome logo), fall back to the
        # raw most-frequent colours minus pure white/black.
        if not ordered:
            for count, idx in sorted(counts, key=lambda x: -x[0]):
                r, g, b = palette[idx * 3:idx * 3 + 3]
                if (r, g, b) not in ((255, 255, 255), (0, 0, 0)):
                    ordered.append((r, g, b))
                if len(ordered) >= num_colors:
                    break
        return ordered

    @staticmethod
    def _rgb_to_hex(rgb):
        """Convert an (R, G, B) tuple into a hex color string."""
        return '#{:02X}{:02X}{:02X}'.format(*rgb)

    @staticmethod
    def _mix(rgb, target, ratio):
        """Linearly mix rgb toward target by ratio (0 = original, 1 = target)."""
        return tuple(int(c + (t - c) * ratio) for c, t in zip(rgb, target))

    @staticmethod
    def _relative_luminance(rgb):
        """Calculate the relative luminance of an RGB color."""
        return (rgb[0] * 0.299 + rgb[1] * 0.587 + rgb[2] * 0.114) / 255

    def _derive_theme_palette(self, dominant):
        """Map a list of dominant (R,G,B) tuples into the theme.group field
        values: brand colour drives accents, neutral tints for surfaces, dark
        text for contrast."""
        primary = dominant[0]
        secondary = dominant[1] if len(dominant) > 1 else primary

        # Surfaces: very pale tint of the brand mixed toward white.
        surface = self._mix(primary, (255, 255, 255), 0.96)        # page bg (~4% brand)
        card_surface = self._mix(primary, (255, 255, 255), 0.99)   # cards (~1% brand, nearly white)

        # Text: keep dark for readability; pull slightly toward the brand for warmth.
        text = self._mix(primary, (28, 28, 32), 0.85)              # near-black w/ brand whisper

        # Card text: a deeper-than-page tone that pops against the near-white card.
        # 70% mix toward dark so a bit more brand colour comes through inside cards.
        card_text = self._mix(primary, (20, 20, 24), 0.70)

        # Hover / muted accent — primary mixed slightly toward white.
        accent_hover = self._mix(primary, (255, 255, 255), 0.25)

        is_gradient = len(dominant) > 1 and dominant[0] != dominant[1]

        return {
            'background_color': self._rgb_to_hex(surface),
            'card_background_color': self._rgb_to_hex(card_surface),
            'card_text_color': self._rgb_to_hex(card_text),
            'dashboard_card_color': self._rgb_to_hex(card_surface),
            'navbar_color': self._rgb_to_hex(card_surface),
            'button_color': self._rgb_to_hex(primary),
            'text_color': self._rgb_to_hex(text),
            'sidebar_toggle_color': self._rgb_to_hex(accent_hover),
            'card_spacing': 15,
            'is_gradient': is_gradient,
            'gradient_color_1': self._rgb_to_hex(self._mix(primary, (255, 255, 255), 0.85)),
            'gradient_color_2': self._rgb_to_hex(self._mix(secondary, (255, 255, 255), 0.90)),
            'gradient_degree': 135,
        }
