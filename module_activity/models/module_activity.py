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


class ModuleActivity(models.Model):
    """Record module activity and history details."""
    _name = "module.activity"
    _description = "Module Activity"
    _rec_name = "name"

    name = fields.Char(string="Module Name",
                                 related="modules_id.shortdesc",
                                 help="Name of the module")
    modules_id = fields.Many2one('ir.module.module', string="Module",
                                 help="Module identifier")
    technical_name = fields.Char(string="Technical Name",
                                 related="modules_id.name",
                                 help="Technical name of the module")
    status = fields.Selection(
        related="modules_id.state", string="Status",
        help="Status of the module")
    uninstalled_history_ids = fields.One2many(
        'module.activity.uninstall.history', 'uninstall_id',
        help="History of uninstallation of the module")
    installed_history_ids = fields.One2many(
        'module.activity.install.history', 'install_id',
        help="History of installation of the module")
    upgrade_history_ids = fields.One2many(
        'module.activity.upgrade.history', 'upgrade_id',
        help="History of upgrade of the module")


class InstalledHistory(models.Model):
    _name = 'module.activity.install.history'
    _description = "Installation History"

    installed_module_id = fields.Many2one('ir.module.module',
                                          string='Installed', help="Installed "
                                                                   "Module "
                                                                   "Identifier")
    technical_name = fields.Char(help="Technical name of the module")
    user_id = fields.Many2one('res.users', string="Responsible User",
                              help="Responsible user who installed the module")
    installed_date = fields.Datetime(string="Installed On",
                                     help="Installed date")
    install_id = fields.Many2one('module.activity', string="Inverse Install")


class UninstalledHistory(models.Model):
    _name = 'module.activity.uninstall.history'
    _description = "Uninstallation History"

    uninstalled_module_id = fields.Many2one('ir.module.module',
                                            string="Uninstalled module",
                                            help="Uninstalled module name")
    technical_name = fields.Char(help="Technical name of the module")
    user_id = fields.Many2one('res.users', string="Responsible User",
                              help="Responsible user for the uninstallation")
    uninstalled_date = fields.Datetime(string="Last Uninstalled On",
                                       help="Uninstalled date")
    uninstall_id = fields.Many2one('module.activity', string="Uninstalled",
                                   help="Uninstalled inverse of module.activity")


class UpgradeHistory(models.Model):
    _name = 'module.activity.upgrade.history'
    _description = "Upgrade History"

    upgrade_module_id = fields.Many2one('ir.module.module',
                                        string="Upgrade module name",
                                        help="Upgrade module identifier using name")
    technical_name = fields.Char(help="Technical name of the module")
    user_id = fields.Many2one('res.users', string="Responsible User",
                              help="Responsible user who upgraded the module")
    upgrade_date = fields.Datetime(string="Upgraded On", help="Upgraded date")
    upgrade_id = fields.Many2one('module.activity',
                                 help="Upgrade inverse of module.activity")
