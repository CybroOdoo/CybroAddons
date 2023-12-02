# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj (odoo@cybrosys.com)
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
    """Class for inherited model res users.Contains required fields and
    functions of the module.
    Methods:
        load_views(self, views, options=None):
            Super load_views function to write into fields associated with
            filters when opening the view
    """
    _inherit = 'res.users'

    sales_user = fields.Boolean(default=False, string='Sales User',
                                help='field for Sales user filter')
    invoice_user = fields.Boolean(default=False, string='Invoice User',
                                  help='field for Invoice user filter')
    purchase_user = fields.Boolean(default=False, string='Purchase User',
                                   help='field for Purchase user filter')
    website_user = fields.Boolean(default=False, string='Website User',
                                  help='field for Website user filter')
    inventory_user = fields.Boolean(default=False, string='Inventory User',
                                    help='field for Inventory user filter')
    pos_user = fields.Boolean(default=False, string='POS User',
                              help='field for POS user filter')
    project_user = fields.Boolean(default=False, string='Project User',
                                  help='field for Project user filter')
    manufacturing_user = fields.Boolean(default=False,
                                        string='Manufacturing User',
                                        help='field for Manufacturing user filter')

    @api.model
    def load_views(self, views, options=None):
        """ Super load_views function to write into fields associated with
        filters when opening the view.
            :param views: list of [view_id, view_type]
            :param dict options: a dict optional boolean flags, set to enable:
            :return: dictionary with fields_views, fields and optionally filters
        """
        res = super().load_views(views, options)
        for users in self.search([]):
            groups = users.groups_id.category_id.mapped('xml_id')
            if 'base.module_category_sales_sales' in groups:
                users.write({
                    'sales_user': True,
                })
            else:
                users.write({
                    'sales_user': False,
                })
            if 'base.module_category_accounting_accounting' in groups:
                users.write({
                    'invoice_user': True,
                })
            else:
                users.write({
                    'invoice_user': False,
                })
            if 'base.module_category_inventory_purchase' in groups:
                users.write({
                    'purchase_user': True,
                })
            else:
                users.write({
                    'purchase_user': False,
                })
            if 'base.module_category_website_website' in groups:
                users.write({
                    'website_user': True,
                })
            else:
                users.write({
                    'website_user': False,
                })

            if 'base.module_category_inventory_inventory' in groups:
                users.write({
                    'inventory_user': True,
                })
            else:
                users.write({
                    'inventory_user': False,
                })
            if 'base.module_category_sales_point_of_sale' in groups:
                users.write({
                    'pos_user': True,
                })
            else:
                users.write({
                    'pos_user': False,
                })
            if 'base.module_category_services_project' in groups:
                users.write({
                    'project_user': True,
                })
            else:
                users.write({
                    'project_user': False,
                })
            if 'base.module_category_manufacturing_manufacturing' in groups:
                users.write({
                    'manufacturing_user': True,
                })
            else:
                users.write({
                    'manufacturing_user': False,
                })
        return res
