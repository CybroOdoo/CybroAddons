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
from odoo import fields, models, api


class PosConfig(models.Model):
    """Inherit POS config to handle multi-category restriction"""
    _inherit = 'pos.config'

    def _get_available_product_domain(self):
        """Override to handle multi-category filtering"""
        domain = super()._get_available_product_domain()

        # Only modify if category restriction is enabled
        if self.iface_available_categ_ids:
            # Find and remove the original pos_categ_id filter
            new_domain = []
            for condition in domain:
                # Check if this is a pos_categ_id condition
                if isinstance(condition, (list, tuple)) and len(condition) == 3:
                    if condition[0] == 'pos_categ_id':
                        # Replace with our multi-category filter
                        new_domain.extend([
                            '|',  # OR condition
                            ('pos_categ_ids', 'in',
                             self.iface_available_categ_ids.ids),
                            ('pos_categ_id', 'in',
                             self.iface_available_categ_ids.ids)
                        ])
                        continue
                new_domain.append(condition)

            # If we didn't find/replace the pos_categ_id condition, add our filter
            if new_domain == domain:
                new_domain.extend([
                    '|',  # OR condition
                    ('pos_categ_ids', 'in', self.iface_available_categ_ids.ids),
                    ('pos_categ_id', 'in', self.iface_available_categ_ids.ids)
                ])

            domain = new_domain

        return domain