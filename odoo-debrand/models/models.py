# -*- coding: utf-8 -*-

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
