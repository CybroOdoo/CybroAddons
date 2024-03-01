# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Saneen K (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """ Configure the credentials in settings """
    _inherit = 'res.config.settings'

    owncloud_domain = fields.Char(string='Owncloud Domain', copy=False,
                                  config_parameter='odoo_owncloud_'
                                                   'connector.owncloud_domain',
                                  help="Add the domain of your ownCloud")
    owncloud_user_name = fields.Char(string='Owncloud Username', copy=False,
                                     config_parameter='odoo_owncloud_'
                                                      'connector.owncloud_'
                                                      'user_name',
                                     help="Add the username of your ownCloud")
    owncloud_password = fields.Char(string='Owncloud Password', copy=False,
                                    config_parameter='odoo_owncloud_'
                                                     'connector.owncloud_'
                                                     'password',
                                    help="Add the password of your ownCloud")
    owncloud_button = fields.Boolean(string='Owncloud Button',
                                     config_parameter='odoo_owncloud_'
                                                      'connector.owncloud_'
                                                      'button',
                                     help="Enables the ownCloud")
    owncloud_folder = fields.Char(string='Owncloud Folder', copy=False,
                                  config_parameter='odoo_owncloud_'
                                                   'connector.owncloud_folder',
                                  help="Give the exact folder name in the "
                                       "ownCloud where the files are stored")
