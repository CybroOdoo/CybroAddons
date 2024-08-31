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


class ModuleActivity(models.Model):
    """Creating a  new record to specify the histories"""
    _name = "module.activity"
    _description = "Module activity"

    modules_id = fields.Many2one('ir.module.module', string="Module",
                                 help="Module identifier")
    technical_name = fields.Char(string="Technical Name",
                                 related="modules_id.name",
                                 help="Technical name of the module")
    status = fields.Selection([('uninstallable', 'Uninstallable'),
                               ('uninstalled', 'Not Installed'),
                               ('installed', 'Installed'),
                               ('to upgrade', 'To be upgraded'),
                               ('to remove', 'To be removed'),
                               ('to install', 'To be installed')],
                              related="modules_id.state", string="Status",
                              help="Status of the module")
    uninstalled_history_ids = fields.One2many('uninstall.history',
                                              'uninstall_id',
                                              string='Uninstalled History',
                                              help="History of uninstallation "
                                                   "of the module")
    installed_history_ids = fields.One2many('install.history', 'install_id',
                                            string="Installed History",
                                            help="History of installation of "
                                                 "the module")
    upgrade_history_ids = fields.One2many('upgrade.history', 'upgrade_id',
                                          string='Upgrade History',
                                          help="History of upgrade of the "
                                               "module")


class InstalledHistory(models.Model):
    _name = 'install.history'
    _description = "Installation History"

    installed_module_id = fields.Many2one('ir.module.module',
                                          string='Installed', help="Installed "
                                                                   "Module "
                                                                   "Identifier")
    technical_name = fields.Char(string="Technical Name",
                                 help="Technical name of the module")
    user_id = fields.Many2one('res.users', string="Responsible User",
                              help="Responsible")
    installed_date = fields.Datetime(string="Installed On",
                                     help="Installed date")
    install_id = fields.Many2one('module.activity', string="Inverse Install")


class UninstalledHistory(models.Model):
    _name = 'uninstall.history'
    _description = "Uninstallation history"

    uninstalled_module_id = fields.Many2one('ir.module.module',
                                            string="Uninstalled module",
                                            help="Uninstalled module name")
    technical_name = fields.Char(string="Technical Name",
                                 help="Technical name of the module")
    user_id = fields.Many2one('res.users', string="Responsible User",
                              help="Responsible user for the uninstallation")
    uninstalled_date = fields.Datetime(string="Last Uninstalled On",
                                       help="Uninstalled date")
    uninstall_id = fields.Many2one('module.activity', string="Uninstalled",
                                   help="Uninstalled inverse of module.activity")


class UpgradeHistory(models.Model):
    _name = 'upgrade.history'
    _description = "Upgrade History"

    upgrade_module_id = fields.Many2one('ir.module.module',
                                        string="Upgrade module name",
                                        help="Upgrade module identifier using name")
    technical_name = fields.Char(string="Technical Name",
                                 help="Technical name of the module")
    user_id = fields.Many2one('res.users', string="Responsible user",
                              help="Responsible user to upgrade")
    upgrade_date = fields.Datetime(string="Upgrade On", help="Upgrade date")
    upgrade_id = fields.Many2one('module.activity', string="Upgrade",
                                 help="Upgrade inverse of module.activity")
