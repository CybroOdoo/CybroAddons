# -*- coding: utf-8 -*-
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

from odoo import models, fields, api, tools


class OdooDebrand(models.Model):
    """
     Fields to access from the database manager.
    """
    _inherit = "website"

    def get_company_logo(self):
        self.company_logo_url ="/web/image/res.company/%s/logo"%(self.id)

    def get_favicon(self):
        id = self.env['website'].sudo().search([])
        self.favicon_url ="/web/image/website/%s/favicon"%(id[0].id)

    favicon_url = fields.Text("Url", compute='get_favicon')
    company_logo_url = fields.Text("Url", compute='get_company_logo')
