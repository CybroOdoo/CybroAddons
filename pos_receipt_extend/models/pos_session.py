# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import models


class PosSessionLoadFields(models.Model):
    """
    Extends 'pos.session' model to load additional POS UI models and fields.
    """
    _inherit = 'pos.session'

    def _pos_ui_models_to_load(self):
        """
        Get the list of POS UI models to be loaded.
        return: List of POS UI models to load.
        """
        result = super()._pos_ui_models_to_load()
        result += ['pos.config']
        return result

    def _loader_params_res_config_settings(self):
        """
        Get the loader parameters for res.config.settings.
        return: Loader parameters for res.config.settings.
        """
        return {
            'search_params': {
                'fields': ['is_qr_code', 'is_invoice_number',
                           'is_customer_name',
                           'is_customer_address', 'is_customer_mobile',
                           'is_customer_phone', 'is_customer_email',
                           'is_customer_vat'],
            },
        }

    def _get_pos_ui_pos_config(self, params):
        """
        Get POS UI data for pos.config.
        params: Loader parameters.
        return: POS UI data for pos.config.
        """
        return self.env['pos.config'].search_read(
            **params['search_params'])
