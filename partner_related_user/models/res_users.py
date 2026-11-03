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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import api, fields, models


class ResUsers(models.Model):
    """Class for inherited model res users. Contains computed fields for
    module-based user filters."""
    _inherit = 'res.users'

    sales_user = fields.Boolean(
        string='Sales User',
        compute='_compute_module_users',
        store=True,
        compute_sudo=True,
        help='Field for Sales user filter',
    )
    invoice_user = fields.Boolean(
        string='Invoice User',
        compute='_compute_module_users',
        store=True,
        compute_sudo=True,
        help='Field for Invoice user filter',
    )
    purchase_user = fields.Boolean(
        string='Purchase User',
        compute='_compute_module_users',
        store=True,
        compute_sudo=True,
        help='Field for Purchase user filter',
    )
    website_user = fields.Boolean(
        string='Website User',
        compute='_compute_module_users',
        store=True,
        compute_sudo=True,
        help='Field for Website user filter',
    )
    inventory_user = fields.Boolean(
        string='Inventory User',
        compute='_compute_module_users',
        store=True,
        compute_sudo=True,
        help='Field for Inventory user filter',
    )
    pos_user = fields.Boolean(
        string='POS User',
        compute='_compute_module_users',
        store=True,
        compute_sudo=True,
        help='Field for POS user filter',
    )
    project_user = fields.Boolean(
        string='Project User',
        compute='_compute_module_users',
        store=True,
        compute_sudo=True,
        help='Field for Project user filter',
    )
    manufacturing_user = fields.Boolean(
        string='Manufacturing User',
        compute='_compute_module_users',
        store=True,
        compute_sudo=True,
        help='Field for Manufacturing user filter',
    )

    @api.depends('group_ids', 'group_ids.privilege_id.category_id')
    def _compute_module_users(self):
        """Compute boolean filter flags based on the user's assigned group categories."""
        for user in self:
            categories = user.group_ids.privilege_id.category_id
            if not categories and hasattr(user.group_ids, 'category_id'):
                categories = user.group_ids.category_id
            groups = set(categories.mapped('xml_id'))
            cat_ids = set(categories.ids)

            def has_category(xml_id):
                if xml_id in groups:
                    return True
                cat_rec = self.env.ref(xml_id, raise_if_not_found=False)
                return bool(cat_rec and cat_rec.id in cat_ids)

            user.sales_user = has_category('base.module_category_sales_sales')
            user.invoice_user = has_category('base.module_category_accounting_accounting')
            user.purchase_user = has_category('base.module_category_inventory_purchase')
            user.website_user = has_category('base.module_category_website_website')
            user.inventory_user = has_category('base.module_category_inventory_inventory')
            user.pos_user = has_category('base.module_category_sales_point_of_sale')
            user.project_user = has_category('base.module_category_services_project')
            user.manufacturing_user = has_category('base.module_category_manufacturing_manufacturing')
