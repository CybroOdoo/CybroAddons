# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import models


class IrHttp(models.AbstractModel):
    """This class is used to add additional functionality to the 'ir.http'
    model. It inherits from the models.AbstractModel' class, allowing it to
    extend the behavior of the 'ir.http' model."""
    _inherit = 'ir.http'

    def session_info(self):
        """Get additional session information."""
        res = super(IrHttp, self).session_info()
        res['hide_filters_groupby'] = self.env['ir.config_parameter'] \
            .sudo().get_param('hide_filters_groupby.hide_filters_groupby')
        res['ir_model_ids'] = self.env[
            'ir.config_parameter'].sudo().get_param(
            'hide_filters_groupby.ir_model_ids')
        res['is_hide_filters_groupby_enabled'] = self.env[
            'ir.config_parameter'].sudo().get_param(
            'hide_filters_groupby.is_hide_filters_groupby_enabled')
        return res
