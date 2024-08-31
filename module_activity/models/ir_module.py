# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V (<https://www.cybrosys.com>)
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
    """This is used get the activities history for the module"""
    _inherit = 'ir.module.module'

    @assert_log_admin_access
    def button_immediate_install(self):
        """This is used to get the installation history of the modules"""
        res = super(IrModule, self).button_immediate_install()
        module = self.env['ir.module.module'].search(
            [('name', '=', 'module_activity')])
        if module.state == 'installed':
            module_activity = self.env['module.activity'].search(
                [('modules_id', '=', self.id)])
            if not module_activity:
                self.env['module.activity'].create({
                    'modules_id': self.id,
                    'installed_history_ids': [
                        (0, 0, {
                            'installed_module_id': self.id,
                            'technical_name': self.display_name,
                            'user_id': self.env.user.id,
                            'installed_date': fields.Date.today()

                        })]
                })
            else:
                module_activity.write({
                    'installed_history_ids': [
                        (0, 0, {
                            'installed_module_id': self.id,
                            'technical_name': self.display_name,
                            'user_id': self.env.user.id,
                            'installed_date': fields.Date.today()

                        })]
                })
        return res

    @assert_log_admin_access
    def module_uninstall(self):
        """This is used to get the uninstallation history of the modules"""
        res = super(IrModule, self).module_uninstall()
        for rec in self:
            module_un = self.env["module.activity"].search(
                [('modules_id', '=', rec.id)])

            if module_un:
                for ric in self:
                    module_un.write({
                        'uninstalled_history_ids': [(0, 0, {
                            'uninstalled_module_id': ric.id,
                            'technical_name': ric.display_name,
                            'user_id': self.env.user.id,
                            'uninstalled_date': fields.Date.today()
                        })]
                    })
        return res

    @assert_log_admin_access
    def button_immediate_upgrade(self):
        """This is used to get the upgrade history of the modules"""
        res = super(IrModule, self).button_immediate_upgrade()
        module_un = self.env["module.activity"].search(
            [('modules_id', '=', self.id)])
        if module_un:
                module_un.write({
                    'upgrade_history_ids': [(0, 0, {
                        'upgrade_module_id': self.id,
                        'technical_name': self.display_name,
                        'user_id': self.env.user.id,
                        'upgrade_date': fields.Date.today()
                    })]
                })
        return res
