# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER 
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models
from odoo.addons.base.models.ir_module import assert_log_admin_access


class IrModule(models.Model):
    """This is used to get the activity history for the module."""
    _inherit = 'ir.module.module'

    def _log_install_history(self):
        """Record install history entry for modules in self."""
        tracking_module = self.env['ir.module.module'].search(
            [('name', '=', 'module_activity')], limit=1)
        if tracking_module.state == 'installed':
            curr_date = fields.Datetime.now()
            user_id = self.env.user.id
            for rec in self:
                if rec.name == 'module_activity':
                    continue
                module_activity = self.env['module.activity'].search(
                    [('modules_id', '=', rec.id)], limit=1)
                vals = {
                    'installed_module_id': rec.id,
                    'technical_name': rec.display_name,
                    'user_id': user_id,
                    'installed_date': curr_date,
                }
                if not module_activity:
                    self.env['module.activity'].create({
                        'modules_id': rec.id,
                        'installed_history_ids': [(0, 0, vals)],
                    })
                else:
                    module_activity.write({
                        'installed_history_ids': [(0, 0, vals)],
                    })

    def _log_uninstall_history(self):
        """Record uninstall history entry for modules in self."""
        if 'module.activity' in self.env:
            user_id = self.env.user.id
            curr_date = fields.Datetime.now()
            for rec in self:
                if rec.name == 'module_activity':
                    continue
                module_activity = self.env['module.activity'].search(
                    [('modules_id', '=', rec.id)], limit=1)
                vals = {
                    'uninstalled_module_id': rec.id,
                    'technical_name': rec.display_name,
                    'user_id': user_id,
                    'uninstalled_date': curr_date,
                }
                if not module_activity:
                    self.env['module.activity'].create({
                        'modules_id': rec.id,
                        'uninstalled_history_ids': [(0, 0, vals)],
                    })
                else:
                    module_activity.write({
                        'uninstalled_history_ids': [(0, 0, vals)],
                    })

    def _log_upgrade_history(self):
        """Record upgrade history entry for modules in self."""
        if 'module.activity' in self.env:
            curr_date = fields.Datetime.now()
            user_id = self.env.user.id
            for rec in self:
                if rec.name == 'module_activity':
                    continue
                module_activity = self.env['module.activity'].search(
                    [('modules_id', '=', rec.id)], limit=1)
                vals = {
                    'upgrade_module_id': rec.id,
                    'technical_name': rec.display_name,
                    'user_id': user_id,
                    'upgrade_date': curr_date,
                }
                if not module_activity:
                    self.env['module.activity'].create({
                        'modules_id': rec.id,
                        'upgrade_history_ids': [(0, 0, vals)],
                    })
                else:
                    module_activity.write({
                        'upgrade_history_ids': [(0, 0, vals)],
                    })

    @assert_log_admin_access
    def button_install(self):
        """Get the installation history for standard install operations."""
        res = super().button_install()
        if not self.env.context.get('skip_module_activity_logging'):
            self._log_install_history()
        return res

    @assert_log_admin_access
    def button_immediate_install(self):
        """Get the installation history for immediate install operations."""
        self._log_install_history()
        return super(
            IrModule, self.with_context(skip_module_activity_logging=True)
        ).button_immediate_install()

    @assert_log_admin_access
    def button_uninstall(self):
        """Get the uninstallation history for standard uninstall operations."""
        if not self.env.context.get('skip_module_activity_logging'):
            self._log_uninstall_history()
        return super().button_uninstall()

    @assert_log_admin_access
    def button_immediate_uninstall(self):
        """Get the uninstallation history for immediate uninstall operations."""
        self._log_uninstall_history()
        return super(
            IrModule, self.with_context(skip_module_activity_logging=True)
        ).button_immediate_uninstall()

    @assert_log_admin_access
    def button_upgrade(self):
        """Get the upgrade history for standard upgrade operations."""
        res = super().button_upgrade()
        if not self.env.context.get('skip_module_activity_logging'):
            self._log_upgrade_history()
        return res

    @assert_log_admin_access
    def button_immediate_upgrade(self):
        """Get the upgrade history for immediate upgrade operations."""
        self._log_upgrade_history()
        return super(
            IrModule, self.with_context(skip_module_activity_logging=True)
        ).button_immediate_upgrade()
