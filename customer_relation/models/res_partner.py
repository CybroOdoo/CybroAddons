# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sreerag PM (<odoo@cybrosys.com>)
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
###############################################################################
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    partner_relation_ids = fields.One2many('partner.relation', 'contact_id',
                                           'Relationship')
    relation_type_names = fields.Char(
        string='Relation Types',
        compute='_compute_relation_info',
        store=True,
        help="List of all unique relation types this partner has."
    )

    is_related = fields.Boolean(
        string='Has Relationship',
        compute='_compute_relation_info',
        store=True,
    )

    relation_category_names = fields.Char(
        string='Relation Categories',
        compute='_compute_relation_info',
        store=True,
        help="List of all unique relation categories this partner has."
    )

    # Update compute method to include category aggregation
    @api.depends(
        'partner_relation_ids.relation_type_id')  # Update dependencies
    def _compute_relation_info(self):
        for partner in self:
            # Aggregate Category Names
            categories = partner.partner_relation_ids.mapped(
                'relation_type_id.category_id.name')
            unique_categories = sorted(list(set(categories)))

            # 1. Update the category field
            partner.relation_category_names = ', '.join(
                unique_categories) if unique_categories else False

            # 2. Keep existing aggregation (optional, if you still want to search by specific role)
            relation_types = partner.partner_relation_ids.mapped(
                'reverse_relation_type_id.name')
            partner.relation_type_names = ', '.join(
                relation_types) if relation_types else False

            partner.is_related = bool(relation_types)  # Keep existing flag
