    # -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
import logging


_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """
    Enable Storage Locations in Inventory settings and groups upon install.
    """
    _logger.info(
        "Enabling Storage Locations (group_stock_multi_locations) for Waste Management..."
    )
    group_multi_loc = env.ref('stock.group_stock_multi_locations', raise_if_not_found=False)
    group_stock_user = env.ref('stock.group_stock_user', raise_if_not_found=False)
    group_stock_manager = env.ref('stock.group_stock_manager', raise_if_not_found=False)

    if group_multi_loc:
        if group_stock_user:
            group_stock_user.sudo().write({'implied_ids': [(4, group_multi_loc.id)]})
        if group_stock_manager:
            group_stock_manager.sudo().write({'implied_ids': [(4, group_multi_loc.id)]})

        group_user = env.ref('base.group_user', raise_if_not_found=False)
        if group_user:
            users_to_add = group_user.user_ids
            if users_to_add:
                group_multi_loc.sudo().write({'user_ids': [(4, u.id) for u in users_to_add]})
