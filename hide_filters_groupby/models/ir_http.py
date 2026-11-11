# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from ast import literal_eval
from odoo import models


class IrHttp(models.AbstractModel):
    """This class is used to add additional functionality to the 'ir.http'
    model. It inherits from the models.AbstractModel' class, allowing it to
    extend the behavior of the 'ir.http' model."""
    _inherit = 'ir.http'

    def session_info(self):
        """Get additional session information."""
        res = super().session_info()
        icp = self.env['ir.config_parameter'].sudo()
        res['hide_filters_groupby'] = icp.get_str(
            'hide_filters_groupby.hide_filters_groupby', default='global')
        model_ids_str = icp.get_str(
            'hide_filters_groupby.ir_model_ids', default='[]')
        res['ir_model_ids'] = model_ids_str
        try:
            model_ids = literal_eval(model_ids_str) if model_ids_str else []
            if isinstance(model_ids, list):
                res['hide_filters_groupby_models'] = self.env[
                    'ir.model'].sudo().browse(model_ids).mapped('model')
            else:
                res['hide_filters_groupby_models'] = []
        except Exception:
            res['hide_filters_groupby_models'] = []
        res['is_hide_filters_groupby_enabled'] = icp.get_bool(
            'hide_filters_groupby.is_hide_filters_groupby_enabled', default=False)
        return res
