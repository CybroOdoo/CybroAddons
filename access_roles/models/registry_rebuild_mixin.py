##############################################################################
# Copyright (c) 2026 braintec AG (https://braintec.com)
# All Rights Reserved
# Licensed under the Odoo Proprietary License v1.0 (OPL).
# See LICENSE file for full licensing details.
##############################################################################
import logging
import time

from odoo import SUPERUSER_ID, api, models

_logger = logging.getLogger(__name__)


def run_once(cr, lock_name):
    """Try to acquire a transaction-scoped advisory lock."""
    cr.execute("SELECT pg_try_advisory_xact_lock(hashtext(%s))", (lock_name,))
    return cr.fetchone()[0]


class RegistryRebuildMixin(models.AbstractModel):
    _name = 'access.roles.registry.rebuild.mixin'
    _description = 'Access Roles Registry Rebuild Coordinator'

    @api.model
    def _register_hook(self):
        super()._register_hook()
        _logger.info('Scheduling access roles registry rebuild in post-commit hook')
        self.env.cr.postcommit.add(self._run_all_registry_hooks_postcommit)
        return True

    def _run_all_registry_hooks_postcommit(self):
        start = time.monotonic()
        _logger.info(
            'Starting access roles registry rebuild after commit (db=%s)',
            self.env.cr.dbname,
        )
        with self.pool.cursor() as new_cr:
            if not run_once(new_cr, 'access_roles_registry_rebuild_all'):
                _logger.info(
                    'Skipping access roles registry rebuild; advisory lock not acquired (db=%s)',
                    new_cr.dbname,
                )
                return False

            try:
                new_env = api.Environment(
                    new_cr,
                    SUPERUSER_ID,
                    {'access_roles_registry_rebuild_running': True},
                )
                _logger.debug('Rebuilding button registry')
                new_env['button.registry'].get_all_buttons()
                _logger.debug('Rebuilding filter registry')
                new_env['filter.registry'].get_all_filters()
                _logger.debug('Rebuilding groupby registry')
                new_env['groupby.registry'].get_all_groupby()
                _logger.debug('Rebuilding tab registry')
                new_env['tab.registry'].get_all_tabs()
                _logger.debug('Rebuilding role groups view')
                new_env['res.groups']._update_role_groups_view()
                new_env.flush_all()
                new_cr.commit()
            except Exception:
                _logger.exception(
                    'Access roles registry rebuild failed in post-commit hook (db=%s)',
                    new_cr.dbname,
                )
                raise

        _logger.info(
            'Finished access roles registry rebuild in %.3fs (db=%s)',
            time.monotonic() - start,
            self.env.cr.dbname,
        )
        return True
