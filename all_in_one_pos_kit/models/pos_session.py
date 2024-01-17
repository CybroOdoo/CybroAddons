# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra MP (odoo@cybrosys.com)
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
###############################################################################
from odoo import models


class PosSession(models.Model):
    """Inherit POS Session to load model and fields"""
    _inherit = 'pos.session'

    def _pos_ui_models_to_load(self):
        """Supering the function for loading res.config.settings to pos
        session"""
        result = super()._pos_ui_models_to_load()
        result += ['res.config.settings', 'pos.order', 'pos.order.line',
                   'multi.barcode.product', 'meals.planning']
        return result

    def _loader_params_res_config_settings(self):
        """Returning the field required"""
        return {
            'search_params': {'fields': ['enable_service_charge', 'visibility',
                                         'global_selection', 'global_charge',
                                         'global_product_id',
                                         'custom_tip_percentage', 'barcode',
                                         'invoice_number', 'customer_details',
                                         'customer_name', 'customer_address',
                                         'customer_mobile', 'customer_phone',
                                         'customer_email', 'customer_vat',
                                         'barcode_type'], }, }

    def _get_pos_ui_res_config_settings(self, params):
        """Returns the model"""
        return self.env['res.config.settings'].search_read(
            **params['search_params'])

    def _loader_params_pos_order(self):
        """pos_order model field load in pos session"""
        return {'search_params': {
            'domain': [],
            'fields': ['name', 'date_order', 'pos_reference',
                       'partner_id', 'lines', 'exchange']}}

    def _get_pos_ui_pos_order(self, params):
        """Return the model pos_order"""
        return self.env['pos.order'].search_read(**params['search_params'])

    def _loader_params_pos_order_line(self):
        """pos_order_line model field load in pos session"""
        return {'search_params': {'domain': [],
                                  'fields': ['product_id', 'qty',
                                             'price_subtotal',
                                             'total_cost']}}

    def _get_pos_ui_pos_order_line(self, params):
        """Return the model pos_order_line"""
        return self.env['pos.order.line'].search_read(
            **params['search_params'])

    def _loader_params_product_product(self):
        """loaded product template field into pos session"""
        result = super()._loader_params_product_product()
        result['search_params']['fields'].extend(
            ['is_age_restrict', 'product_multi_barcodes_ids', 'name', 'id'])
        return result

    def _get_pos_ui_multi_barcode_product(self, params):
        """"Return the model multi_barcode_product"""
        return self.env['multi.barcode.product'].with_context(
            **params['context']).search_read(**params['search_params'])

    def _loader_params_multi_barcode_product(self):
        """loaded multi_barcode_product field into pos session"""
        return {'search_params': {'fields': ['multi_barcode'], },
                'context': {'display_default_code': False}, }

    def _loader_params_meals_planning(self):
        """ returning corresponding data to pos"""
        data = [rec.id for rec in self.env['meals.planning'].search(
            [('state', '=', 'activated'),
             ('pos_ids', 'in', self.config_id.id)])]

        return {'search_params': {'domain': [('id', '=', data)],
                                  'fields': ['name', 'product_ids',
                                             'time_from', 'time_to', 'state',
                                             'pos_ids']}}

    def _get_pos_ui_meals_planning(self, params):
        """"Return the model meals_planning"""
        return self.env['meals.planning'].search_read(**params['search_params'])
