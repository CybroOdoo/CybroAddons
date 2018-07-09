# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2016-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Cybrosys Technologies(<https://www.cybrosys.com>)
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
import json
from odoo.addons.base_geolocalize.models.res_partner import geo_find, geo_query_address
from odoo import models, fields, api


class PartnerGeoLocation(models.Model):
    _inherit = 'res.partner'

    google_map_partner = fields.Char(string="Map")

    @api.onchange('zip', 'street', 'city', 'state_id', 'country_id')
    def map_location_setter(self):
        result = geo_find(geo_query_address(street=self.street,
                                            zip=self.zip,
                                            city=self.city,
                                            state=self.state_id.name,
                                            country=self.country_id.name))
        if result:
            if not self.google_map_partner:
                maps_loc = {u'position': {u'lat': 20.593684, u'lng': 78.96288}, u'zoom': 3}
                json_map = json.dumps(maps_loc)
                self.google_map_partner = json_map
            if self.google_map_partner:
                map_loc = self.google_map_partner
                maps_loc = json.loads(map_loc)
                maps_loc['position']['lat'] = result[0]
                maps_loc['position']['lng'] = result[1]
                maps_loc['zoom'] = 3
            json_map = json.dumps(maps_loc)
            self.google_map_partner = json_map
