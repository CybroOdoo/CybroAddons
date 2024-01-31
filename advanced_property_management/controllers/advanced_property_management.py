# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import werkzeug.utils
from odoo import fields, http
from odoo.http import request


class PropertyController(http.Controller):
    """A controller class that shows the related functions to the property"""

    @http.route('/property', auth='user', website=True)
    def property(self):
        """ Returns the property_view for the route """
        return request.render('advanced_property_management.property_view', {
            'property_ids': request.env['property.property'].sudo().search([])
        })

    @http.route('/property/<int:property_id>', auth='user', website=True)
    def property_item(self, property_id):
        """ Shows each corresponding properties view in property_view_item """
        return request.render('advanced_property_management.property_view_item',
                              {
                                  'property_id': request.env[
                                      'property.property'].sudo().browse(
                                      property_id),
                              })

    @http.route('/map/<latitude>/<longitude>', type='http', auth='user')
    def redirect_map(self, latitude, longitude):
        """ Returns the Google map location for the corresponding latitude
        and longitude """
        return werkzeug.utils.redirect(
            "https://www.google.com/maps/@%s,%s,115m/data=!3m1!1e3" % (
                latitude, longitude))

    @http.route('/property/auction/', type='json', auth='user')
    def auction(self):
        """Returns properties in three different states"""
        auction_ids = request.env['property.auction'].sudo().search([
            ('state', '!=', 'draft')
        ])
        context = {
            'confirmed': [],
            'started': [],
            'ended': [],
        }
        for auction_id in auction_ids:
            participants = sorted(auction_id.participant_ids,
                                  key=lambda x: x.bid_amount, reverse=True)
            data = {
                'id': auction_id.id,
                'name': auction_id.property_id.name,
                'code': auction_id.auction_seq,
                'image': auction_id.property_id.image,
                'start': auction_id.start_time,
                'start_price': auction_id.bid_start_price,
                'last': participants[0].bid_amount if participants else 0,
                'end': auction_id.end_time,
                'winner': auction_id.auction_winner_id.name,
                'final_rate': auction_id.final_price,
                'total_participant': len(auction_id.participant_ids.ids)
            }
            if auction_id.state == 'confirmed':
                context['confirmed'].append(data)
            elif auction_id.state == 'started':
                context['started'].append(data)
            elif auction_id.state == 'ended':
                context['ended'].append(data)
        response = http.Response(
            template='advanced_property_management.auction_view',
            qcontext=context)
        return response.render()

    @http.route('/property/auction/<int:prop_id>/bid', type='json',
                auth='user')
    def auction_bid_submit(self, prop_id, **kw):
        """Return success when auction is submitted"""
        auction_id = request.env['property.auction'].sudo().browse(int(prop_id))
        auction_id.write({
            'participant_ids': [
                fields.Command.create({
                    'partner_id': request.env.user.partner_id.id,
                    'bid_time': fields.Datetime.now(),
                    'bid_amount': float(kw.get('bid_amount'))
                })
            ]
        })
        return {'message': 'success'}
