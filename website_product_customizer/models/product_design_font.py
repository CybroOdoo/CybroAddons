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
from odoo import api, fields, models


class ProductDesignFont(models.Model):
    """Model defining the fonts available for use in the product designer."""
    _name = 'product.design.font'
    _description = 'Product Design Font'
    _order = 'sequence, name'

    name = fields.Char(string="Name", required=True, help="Display name of the font (e.g. 'Roboto')")
    font_family_name = fields.Char(string="Font Family", required=True, help="CSS font-family name (e.g. 'Roboto', 'Arial')")
    
    provider = fields.Selection([
        ('google', 'Google Fonts'),
        ('custom', 'Custom Upload'),
        ('system', 'System Font'),
    ], string="Provider", default='google', required=True)

    # Google Fonts
    google_url = fields.Char(string="Google Font URL", help="e.g. https://fonts.googleapis.com/css2?family=Roboto&display=swap")

    # Custom Fonts
    font_file = fields.Binary(string="Font File", attachment=True, help="Upload .ttf, .otf, or .woff file")
    font_filename = fields.Char(string="Font Filename")

    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(default=True)

    @api.depends('provider', 'google_url', 'font_file')
    def _compute_css_url(self):
        """Computes the correct CSS URL endpoint based on the font provider."""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for record in self:
            if record.provider == 'google':
                record.css_url = record.google_url
            elif record.provider == 'custom' and record.font_file:
                record.css_url = f"{base_url}/web/content/{record._name}/{record.id}/font_file/{record.font_filename}"
            else:
                record.css_url = False

    css_url = fields.Char(compute='_compute_css_url', string="CSS URL")
