# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anjana P V  (Contact : odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
##############################################################################
from odoo import models


class pos_session(models.Model):
    """Extends the 'pos.session' model to customize data processing
    and UI models for point of sale sessions."""
    _inherit = 'pos.session'

    def _pos_data_process(self, loaded_data):
        """Process loaded data for the point of sale session, extending the
         base class method."""
        super()._pos_data_process(loaded_data)
        if self.config_id:
            loaded_data['type_by_id'] = {order_type['id']: order_type for
                                         order_type in
                                         loaded_data['delivery.type']}

    def _pos_ui_models_to_load(self):
        """Get the list of UI models to load for the point of sale session."""
        result = super()._pos_ui_models_to_load()
        result += ['delivery.type']
        return result

    def _loader_params_delivery_type(self):
        """Get the loader parameters for the 'delivery.type' model."""
        return {
            'search_params': {
                'domain': [('id', '=', self.env['res.config.settings'].search(
                    []).delivery_methods.ids)],
                'fields': ['name']}, }

    def _get_pos_ui_delivery_type(self, params):
        """Retrieve UI data for 'delivery.type' based on provided parameters."""
        return self.env['delivery.type'].search_read(**params['search_params'])
