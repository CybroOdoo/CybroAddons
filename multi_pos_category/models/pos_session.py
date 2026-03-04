# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import models
from odoo.osv.expression import AND, OR


class PosSession(models.Model):
    """This is used to load the models and fields to pos session"""
    _inherit = 'pos.session'

    def _loader_params_product_product(self):
        """Fix category filtering so ALL assigned categories are matched.
        """
        result = super()._loader_params_product_product()

        if (self.config_id.limit_categories
                and self.config_id.iface_available_categ_ids):
            categ_ids = self.config_id.iface_available_categ_ids.ids

            # Mirror what native _loader_params_product_product does, but
            # replace pos_categ_id with pos_categ_ids so ALL categories match.
            domain = [
                '&', '&',
                ('sale_ok', '=', True),
                ('available_in_pos', '=', True),
                '|',
                ('company_id', '=', self.config_id.company_id.id),
                ('company_id', '=', False),
            ]
            # Use pos_categ_ids: matches products regardless of category order
            domain = AND([domain, [('pos_categ_ids', 'in', categ_ids)]])
            # Re-apply tip product OR if that feature is enabled
            if (self.config_id.iface_tipproduct
                    and self.config_id.tip_product_id):
                domain = OR([
                    domain,
                    [('id', '=', self.config_id.tip_product_id.id)]
                ])

            result['search_params']['domain'] = domain

        # Always load pos_categ_ids so the JS side has the full category list
        if 'pos_categ_ids' not in result['search_params']['fields']:
            result['search_params']['fields'].append('pos_categ_ids')

        return result