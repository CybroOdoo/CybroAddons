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
from odoo.osv.expression import AND, OR


class PosConfig(models.Model):
    """Inherit POS config to handle multi-category restriction"""
    _inherit = 'pos.config'

    def _get_available_product_domain(self):
        """Override to handle multi-category filtering using pos_categ_ids."""
        domain = super()._get_available_product_domain()

        if self.iface_available_categ_ids:
            categ_ids = self.iface_available_categ_ids.ids
            new_domain = []
            replaced = False
            for condition in domain:
                if (isinstance(condition, (list, tuple))
                        and len(condition) == 3
                        and condition[0] == 'pos_categ_id'):
                    # Drop the preceding '&' operator AND() may have injected
                    if new_domain and new_domain[-1] == '&':
                        new_domain.pop()
                    # Replace with the many2many filter
                    new_domain.append(('pos_categ_ids', 'in', categ_ids))
                    replaced = True
                    continue
                new_domain.append(condition)

            if not replaced:
                new_domain = AND([new_domain,
                                  [('pos_categ_ids', 'in', categ_ids)]])

            domain = new_domain

        return domain

    def open_ui(self):
        """Override to use pos_categ_ids when checking for available products.

        Native Odoo uses pos_categ_id (Many2one — first category only) to
        check whether any products exist for this POS.  That check fails for
        products whose restricted category is NOT their first category.
        We override to use pos_categ_ids (many2many) instead.
        """
        self.ensure_one()
        if (self.limit_categories and self.iface_available_categ_ids):
            # Run the pre-flight product check ourselves using pos_categ_ids
            # so that multi-category products are found correctly.
            domain = [
                ('available_in_pos', '=', True),
                ('pos_categ_ids', 'in', self.iface_available_categ_ids.ids),
            ]
            if not self.env['product.product'].search(domain, limit=1):
                return {
                    'name': ("There is no product linked to your PoS"),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'pos.session.check_product_wizard',
                    'target': 'new',
                    'context': {'config_id': self.id},
                }
            # Skip the native open_ui check; go straight to open the UI.
            # (We replicate the rest of native open_ui logic.)
            if not self.current_session_id:
                self._check_before_creating_new_session()
            self._validate_fields(self._fields)
            return self._action_to_open_ui()

        return super().open_ui()

    def get_limited_products_loading(self, fields):
        """Override to use pos_categ_ids (Many2many) via ORM — no

        The native method filters by pos_categ_id (Many2one — first category
        only).  Using the ORM with ('pos_categ_ids', 'in', ...) covers ALL
        assigned categories without any raw SQL.
        """
        if not (self.limit_categories and self.iface_available_categ_ids):
            return super().get_limited_products_loading(fields)

        categ_ids = self.iface_available_categ_ids.ids
        domain = [
            ('available_in_pos', '=', True),
            ('sale_ok', '=', True),
            '|',
            ('company_id', '=', self.company_id.id),
            ('company_id', '=', False),
            ('pos_categ_ids', 'in', categ_ids),
        ]
        # Include tip product if configured
        if self.iface_tipproduct and self.tip_product_id:
            domain = ['|', ('id', '=', self.tip_product_id.id)] + domain

        return self.env['product.product'].search_read(
            domain, fields=fields, limit=self.limited_products_amount
        )