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
from odoo import api, models


class ProductPricelist(models.Model):
    """Class for the inherited model product_pricelist. Checking and filtering
        the applied pricelists for the uses by supering the _search() method."""
    _inherit = 'product.pricelist'

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, *,
                bypass_access=False, **kwargs):
        """
        Override _search to restrict pricelists visible to the current user
        when 'restrict_pricelist_user.is_restricted' is enabled.
        """
        # Get system parameter safely
        pricelist_restricted = (
            self.env['ir.config_parameter']
            .sudo()
            .get_param('restrict_pricelist_user.is_restricted')
        )
        if pricelist_restricted and not self.env.su:
            user_id = self.env.user.id
            if user_id:
                user_data = (
                    self.env['res.users']
                    .sudo()
                    .browse(user_id)
                    .read(['pricelist_ids'])
                )
                if user_data and user_data[0].get('pricelist_ids'):
                    user_pricelist_ids = user_data[0]['pricelist_ids']
                    domain = list(domain) if domain else []
                    domain.append(('id', 'in', user_pricelist_ids))
        return super()._search(
            domain,
            offset=offset,
            limit=limit,
            order=order,
            bypass_access=bypass_access,
            **kwargs
        )
