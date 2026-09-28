# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
################################################################################
from odoo import models


class PosSession(models.Model):
    """inherited the pos session and loaded models to pos"""
    _inherit = 'pos.session'

    def _pos_ui_models_to_load(self):
        """load the models to pos"""
        res = super()._pos_ui_models_to_load()
        res.append('pos.keyboard.shortcut')
        res.append('pos.payment.method.key')
        return res

    def _loader_params_pos_config(self):
        """ Extend the loader to include our new shortcut fields"""
        res = super()._loader_params_pos_config()
        res['search_params']['fields'].extend([
            'is_enable_keyboard_shortcuts', 'select_shortcut_id',
            'shortcut_customer_screen', 'shortcut_next_screen',
            'shortcut_select_qty', 'shortcut_select_discount',
            'shortcut_select_price', 'shortcut_print_receipt',
            'shortcut_back_screen', 'shortcut_select_user',
            'shortcut_sent_email', 'shortcut_resume_order',
            'shortcut_new_order', 'shortcut_close_pos',
            'shortcut_select_invoice', 'shortcut_validate_order',
            'shortcut_click_ok', 'shortcut_click_cancel',
            'shortcut_next_screen_show', 'shortcut_delete_orderlines'
        ])
        return res

    def _loader_params_pos_keyboard_shortcut(self):
        """Load the fields and shortcut configuration for the POS keyboard shortcut model."""
        return {
            'search_params': {
                'fields': ['id', 'name', 'customer_screen', 'next_screen', 'select_qty',
                           'select_discount', 'select_price', 'print_receipt',
                           'back_screen', 'select_user', 'sent_email', 'resume_order',
                           'new_order', 'close_pos', 'select_invoice',
                           'validate_order', 'click_cancel', 'click_ok',
                           'next_screen_show', 'delete_orderlines'],
                'domain': [('id', '=', self.config_id.select_shortcut_id.id)]
            },
        }

    def _get_pos_ui_pos_keyboard_shortcut(self, params):
        """set the get function for return the fields values"""
        return self.env['pos.keyboard.shortcut'].search_read(
            **params['search_params'])

    def _loader_params_pos_payment_method_key(self):
        """Load the payment method key fields associated with the selected POS shortcut."""
        return {
            'search_params': {
                'fields': ['id', 'key_code', 'payment_method_id'],
                'domain': [('keyboard_shortcut_id', '=',
                            self.config_id.select_shortcut_id.id)]
            },
        }

    def _get_pos_ui_pos_payment_method_key(self, params):
        """set the get function for return the fields values"""
        return self.env['pos.payment.method.key'].search_read(
            **params['search_params'])