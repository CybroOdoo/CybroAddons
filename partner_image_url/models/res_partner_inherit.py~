# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Nilmar Shereef(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
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

