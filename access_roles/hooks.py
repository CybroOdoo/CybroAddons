# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """
    Post-installation hook that populates all registry tables and generates
    the role groups view.

    This hook runs exactly once — during module installation or upgrade —
    inside a single database transaction managed by the Odoo upgrade process.
    This avoids the serialization errors and thread-race conditions that
    occurred when these operations were triggered via _register_hook (which
    runs on every server startup across all worker processes simultaneously).
    """
    _logger.info("access_roles: Running post_init_hook — populating registries...")

    try:
        _logger.info("access_roles: Populating button registry...")
        env['button.registry'].get_all_buttons()
    except Exception as e:
        _logger.warning("access_roles: Could not populate button registry: %s", e)

    try:
        _logger.info("access_roles: Populating tab registry...")
        env['tab.registry'].get_all_tabs()
    except Exception as e:
        _logger.warning("access_roles: Could not populate tab registry: %s", e)

    try:
        _logger.info("access_roles: Populating filter registry...")
        env['filter.registry'].get_all_filters()
    except Exception as e:
        _logger.warning("access_roles: Could not populate filter registry: %s", e)

    try:
        _logger.info("access_roles: Populating groupby registry...")
        env['groupby.registry'].get_all_groupby()
    except Exception as e:
        _logger.warning("access_roles: Could not populate groupby registry: %s", e)

    try:
        _logger.info("access_roles: Generating role groups view...")
        env['res.groups']._update_role_groups_view()
    except Exception as e:
        _logger.warning("access_roles: Could not update role groups view: %s", e)

    _logger.info("access_roles: post_init_hook completed successfully.")
