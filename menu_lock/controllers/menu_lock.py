# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Gayathri V(<https://www.cybrosys.com>)
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
from odoo import http
from odoo.http import request


class LockModel(http.Controller):
    """This is used to find the locked models"""
    @http.route('/locked_models', auth='public', type='json')
    def lock_model(self, **kw):
        """This is used to return the locked model"""
        if kw.get('action_type') == 'ir.actions.act_window':
            action = request.env['ir.actions.act_window'].browse(
                int(kw.get('action')))
            models_to_lock = request.env.user.models_to_lock_ids.mapped('model')
            if action.res_model in models_to_lock:
                return True
            else:
                return False
