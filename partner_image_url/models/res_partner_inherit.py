# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Nilmar Shereef(<https://www.cybrosys.com>)
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###################################################################################
import base64
import urllib2
import requests
from PIL import Image
from StringIO import StringIO
from odoo import models, fields, api, _
from odoo.exceptions import Warning


class HrEmployeeDocument(models.Model):
    _inherit = 'res.partner'

    web_url = fields.Char(string='Image URL', help='Automatically sanitized HTML contents', copy=False)

    @api.onchange('web_url')
    def onchange_image(self):
        link = self.web_url
        try:
            if link:
                r = requests.get(link)
                Image.open(StringIO(r.content))
                profile_image = base64.encodestring(urllib2.urlopen(link).read())
                val = {
                    'image': profile_image,
                }
                return {'value': val}
        except:
            raise Warning("Please provide correct URL or check your image size.!")


