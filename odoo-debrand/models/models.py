# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Tintuk Tomin(<https://www.cybrosys.com>)
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

import base64
import os
from odoo import models, fields, api, tools


class OdooDebrand(models.Model):
    _inherit = "website"

    def get_company_logo(self):
        id = self.env.user.company_id.id
        self.company_logo_url ="/web/image/res.company/%s/logo"%(id)

    def get_favicon(self):
        id = self.env['website'].sudo().search([])

        self.favicon_url ="/web/image/website/%s/favicon"%(id[0].id)
        print("Wesite = ", self.favicon_url)

    company_logo = fields.Binary()
    favicon_url = fields.Text("Url", compute='get_favicon')
    company_logo_url = fields.Text("Url", compute='get_company_logo')
