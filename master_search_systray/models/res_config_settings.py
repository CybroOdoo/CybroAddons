# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anfas Faisal K (odoo@cybrosys.com)
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
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models
from ast import literal_eval


class ResConfigSettings(models.TransientModel):
    """
    This class extends the 'res.config.settings' model in Odoo to add a new
    Many2many field for selecting installed modules that will be included in
    the master search functionality.
    """
    _inherit = "res.config.settings"

    master_search_installed_ids = fields.Many2many(
        'ir.module.module',
        string='Installed Modules',
        help="Select the installed modules you want to include in the master "
             "search.",
        domain="[('state', '=', 'installed')]"
    )

    @api.model
    def get_values(self):
        """
        Retrieve the current values for the configuration settings, including
        the selected installed modules for the master search.
        """
        res = super(ResConfigSettings, self).get_values()
        master_search_installed_ids = self.env[
            'ir.config_parameter'].sudo().get_param(
            'master_search_systray.master_search_installed_ids')
        if master_search_installed_ids:
            res.update({
                'master_search_installed_ids': [
                    (6, 0, literal_eval(master_search_installed_ids))]
            })
        return res

    def set_values(self):
        """
        Save the current values for the configuration settings, including the
        selected installed modules for the master search.
        """
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'master_search_systray.master_search_installed_ids',
            self.master_search_installed_ids.ids)
        return res
