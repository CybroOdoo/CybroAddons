# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Anjhana A K(<https://www.cybrosys.com>)
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
from ast import literal_eval
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """Adding configuration settings for the module."""
    _inherit = 'res.config.settings'

    res_rollback_model_ids = fields.Many2many('ir.model',
                                              string='Models',
                                              help="Configuration field"
                                                   " to add the models that"
                                                   " needs rollback feature.")

    def set_values(self):
        """Setting the value for Many2many field in the configuration"""
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'odoo_record_rollback.res_rollback_model_ids',
            self.res_rollback_model_ids.ids)
        return res

    @api.model
    def get_values(self):
        """Get the values from the Many2many field"""
        res = super(ResConfigSettings, self).get_values()
        com_contacts = self.env['ir.config_parameter'].sudo().get_param(
            'odoo_record_rollback.res_rollback_model_ids')
        res.update(res_rollback_model_ids=[(6, 0,
                                            literal_eval(com_contacts))
                                           ]if com_contacts else False)
        return res
