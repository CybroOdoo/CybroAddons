# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import models
from odoo.http import request
from odoo.exceptions import AccessDenied


class IrHttp(models.AbstractModel):
    """Extend ir.http to enforce login restrictions."""
    _inherit = "ir.http"

    @classmethod
    def _authenticate(cls, endpoint):
        """Override authentication to check login restrictions."""
        res = super(IrHttp, cls)._authenticate(endpoint=endpoint)
        if request.session.uid:
            user = request.env["res.users"].browse(request.session.uid)
            if user.exists() and user._is_internal():
                try:
                    user.check_login_restrictions()
                except AccessDenied as e:
                    # Clear session and raise error
                    request.session.logout()
                    raise AccessDenied(str(e))
        return res

