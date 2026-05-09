# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import fields, models
from odoo.addons.base.models.ir_module import assert_log_admin_access


class IrModule(models.Model):
    """
    Inherits from ir.module.module to override installation, uninstallation,
    and upgrade buttons for tracking module activity history.
    """
    _inherit = 'ir.module.module'

    @assert_log_admin_access
    def button_immediate_install(self):
        """
        Overrides the standard installation button to record a new
        entry in the installation history logs.
        """
        res = super(IrModule, self).button_immediate_install()
        # Verify the activity tracking module is installed
        tracking_module = self.env['ir.module.module'].search(
            [('name', '=', 'module_activity')], limit=1)
        if tracking_module.state == 'installed':
            curr_date = fields.Datetime.now()
            for rec in self:
                # Skip logging for module_activity itself
                if rec.name == 'module_activity':
                    continue
                module_activity = self.env['module.activity'].search(
                    [('modules_id', '=', rec.id)], limit=1)
                if not module_activity:
                    self.env['module.activity'].create({
                        'modules_id': rec.id,
                        'installed_history_ids': [(0, 0, {
                            'installed_module_id': rec.id,
                            'technical_name': rec.display_name,
                            'user_id': self.env.user.id,
                            'installed_date': curr_date
                        })]
                    })
                else:
                    module_activity.write({
                        'installed_history_ids': [(0, 0, {
                            'installed_module_id': rec.id,
                            'technical_name': rec.display_name,
                            'user_id': self.env.user.id,
                            'installed_date': curr_date
                        })]
                    })
        return res

    @assert_log_admin_access
    def button_immediate_uninstall(self):
        """
        Overrides the standard uninstallation button to record a new
        entry in the uninstallation history logs before removal.
        """
        # Capture the explicitly targeted modules BEFORE they are uninstalled
        if 'module.activity' in self.env:
            user_id = self.env.user.id
            curr_date = fields.Datetime.now()
            for rec in self:
                # Skip logging for module_activity itself
                if rec.name == 'module_activity':
                    continue
                module_activity = self.env["module.activity"].search(
                    [('modules_id', '=', rec.id)], limit=1)
                if not module_activity:
                    self.env['module.activity'].create({
                        'modules_id': rec.id,
                        'uninstalled_history_ids': [(0, 0, {
                            'uninstalled_module_id': rec.id,
                            'technical_name': rec.display_name,
                            'user_id': user_id,
                            'uninstalled_date': curr_date
                        })]
                    })
                else:
                    module_activity.write({
                        'uninstalled_history_ids': [(0, 0, {
                            'uninstalled_module_id': rec.id,
                            'technical_name': rec.display_name,
                            'user_id': user_id,
                            'uninstalled_date': curr_date
                        })]
                    })
        return super(IrModule, self).button_immediate_uninstall()

    @assert_log_admin_access
    def button_immediate_upgrade(self):
        """
        Overrides the standard upgrade button to record a new
        entry in the upgrade history logs.
        """
        res = super(IrModule, self).button_immediate_upgrade()
        # Ensure we log the upgrade even if no activity record existed yet
        if 'module.activity' in self.env:
            curr_date = fields.Datetime.now()
            user_id = self.env.user.id
            for rec in self:
                # Skip logging for module_activity itself
                if rec.name == 'module_activity':
                    continue
                module_activity = self.env['module.activity'].search(
                    [('modules_id', '=', rec.id)], limit=1)
                if not module_activity:
                    self.env['module.activity'].create({
                        'modules_id': rec.id,
                        'upgrade_history_ids': [(0, 0, {
                            'upgrade_module_id': rec.id,
                            'technical_name': rec.display_name,
                            'user_id': user_id,
                            'upgrade_date': curr_date
                        })]
                    })
                else:
                    module_activity.write({
                        'upgrade_history_ids': [(0, 0, {
                            'upgrade_module_id': rec.id,
                            'technical_name': rec.display_name,
                            'user_id': user_id,
                            'upgrade_date': curr_date
                        })]
                    })
        return res
