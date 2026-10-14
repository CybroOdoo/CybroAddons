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
from odoo.fields import Domain

class ThemeWebsiteMenu(models.Model):
    _inherit = 'theme.website.menu'

    def _convert_to_base_model(self, website, **kwargs):
        vals = super()._convert_to_base_model(website, **kwargs)
        if not vals.get('page_id') and vals.get('url') and vals.get('url') != '#':
            domain = website.website_domain() & (
                Domain("url", "=", vals["url"])
                | Domain("url", "=", "/" + vals["url"].lstrip("/"))
            )
            page = self.env['website.page'].search(domain, limit=1)
            if page:
                vals['page_id'] = page.id
            else:
                vals['manual_url'] = vals['url']
        return vals

class Website(models.Model):
    _inherit = 'website'

    def get_cineverse_movies(self, limit=None):
        """Helper to fetch active cineverse.movie records for templates."""
        domain = [('active', '=', True)]
        return self.env['cineverse.movie'].sudo().search(domain, order='sequence, id', limit=limit)

