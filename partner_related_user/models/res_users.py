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
from odoo import api, fields, models


class ResUsers(models.Model):
    """ Class for inherited model res users.Contains required fields and
     functions of the module.
    Methods:
        get_views(self, views, options=None):
            Super get_views function to write into fields associated with
            filters when opening the view """
    _inherit = 'res.users'

    sales_user = fields.Boolean(default=False, string='Sales User',
                                help='Field for Sales user filter')
    invoice_user = fields.Boolean(default=False, string='Invoice User',
                                  help='Field for Invoice user filter')
    purchase_user = fields.Boolean(default=False, string='Purchase User',
                                   help='Field for Purchase user filter')
    website_user = fields.Boolean(default=False, string='Website User',
                                  help='Field for Website user filter')
    inventory_user = fields.Boolean(default=False, string='Inventory User',
                                    help='Field for Inventory user filter')
    pos_user = fields.Boolean(default=False, string='POS User',
                              help='Field for POS user filter')
    project_user = fields.Boolean(default=False, string='Project User',
                                  help='Field for Project user filter')
    manufacturing_user = fields.Boolean(default=False,
                                        string='Manufacturing User',
                                        help='Field for Manufacturing user filter')

    @api.model
    def get_views(self, views, options=None):
        """ Super get_views function to write into fields associated with
        filters when opening the view.
            :param views: list of [view_id, view_type]
            :param dict options: a dict optional boolean flags, set to enable:
            :return: dictionary with fields_views, fields and optionally filters
        """
        res = super().get_views(views, options)
        res_users = self.sudo().search([])
        update_batches = {}

        for user in res_users:
            groups = set(user.group_ids.privilege_id.category_id.mapped('xml_id'))
            vals = {
                'sales_user': 'base.module_category_sales_sales' in groups,
                'invoice_user': 'base.module_category_accounting_accounting' in groups,
                'purchase_user': 'base.module_category_inventory_purchase' in groups,
                'website_user': 'base.module_category_website_website' in groups,
                'inventory_user': 'base.module_category_inventory_inventory' in groups,
                'pos_user': 'base.module_category_sales_point_of_sale' in groups,
                'project_user': 'base.module_category_services_project' in groups,
                'manufacturing_user': 'base.module_category_manufacturing_manufacturing' in groups,
            }

            # Check if any values actually need to be updated
            update_vals = {k: v for k, v in vals.items() if user[k] != v}

            if update_vals:
                update_key = frozenset(update_vals.items())
                if update_key not in update_batches:
                    update_batches[update_key] = user
                else:
                    update_batches[update_key] |= user

        # Perform bulk writes for each unique set of values
        for update_key, users_to_update in update_batches.items():
            users_to_update.write(dict(update_key))

        return res
