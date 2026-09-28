# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Abhijith CK(<https://www.cybrosys.com>)
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
from datetime import datetime, timedelta
from odoo import http, fields
from odoo.http import request


class OnlineSubscription(http.Controller):
    """Online Vehicle subscription through website"""

    @http.route(['/online/subscription/city'], type='json', auth="public",
                website=True)
    def get_city(self, **kwargs):
        """Calling this function using ajax rpc in order to get city
        based on state """
        states = request.env['res.country.state'].sudo().search_read([],
                                                                     ['name'])
        return states

    @http.route('/online/subscription', auth='public', website=True)
    def subscription_form(self):
        """This function will return vehicle  with which state is not null"""
        vehicle_id = request.env['fleet.vehicle'].sudo().search(
            [('states_id', '!=', False)])
        insurance_type = request.env['insurance.type'].sudo().search([])
        vals = {
            'states': vehicle_id.states_id,
            'all_states': request.env['res.country.state'].sudo().search_read(
                [], ['name']),
            'cities': [rec.location for rec in vehicle_id],
            'insurance_type': insurance_type,
        }
        return http.request.render('vehicle_subscription.subscription_form',
                                   vals)

    @http.route('/online/subscription/next', auth='public', website=True)
    def vehicle_form(self, **kw):
        """Redirect to corresponding templates according to the
        data provided by user in form page """
        if kw.get('start_date'):
            start_date = kw.get('start_date')
            end_date = kw.get('end_date')
            insurance = kw.get('insurance_type')
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            insurance_type = request.env['vehicle.insurance'].sudo().search(
                [('insurance_type_id.id', '=', int(insurance)),
                 ('start_date', '<=', start), ('end_date', '>=', end)])
            insurance_amount = insurance_type[
                0].insurance_amount_per_day if insurance_type else 0
            vehicle_ids = insurance_type.vehicle_id
            start_date = fields.Date.to_date(start)
            end_date = fields.Date.to_date(end)

            subscribed_vehicle_id = request.env[
                'fleet.subscription'
            ].sudo().search([
                ('state', '=', 'subscribed'),
                ('start_date', '<=', end_date),
                ('end_date', '>=', start_date),
            ]).mapped('vehicle_id')
            vehicle = request.env['fleet.vehicle'].sudo().search(
                [('id', 'in', vehicle_ids.ids)])
            vehicle_id = vehicle.filtered(
                lambda v: v.id not in subscribed_vehicle_id.ids)
            seating_capacity = kw.get('seating_capacity')
            if seating_capacity:
                try:
                    vehicle_id = vehicle_id.filtered(lambda v: v.model_id.seats >= int(seating_capacity))
                except (ValueError, TypeError):
                    pass
            if vehicle_id:
                for rec in vehicle_id:
                    rec.write({
                        'insurance': insurance,
                        'start': start,
                        'end': end,
                    })
                country_id = False
                if kw.get('state'):
                    state = request.env['res.country.state'].sudo().browse(int(kw.get('state')))
                    country_id = state.country_id.id if state else False
                data = {
                    'vehicles': vehicle_id,
                    'amount': insurance_amount,
                    'customers': request.env.user.partner_id.name,
                    'city': kw.get('city') or kw.get('city_id'),
                    'state_id': kw.get('state'),
                    'country_id': country_id,
                    'seating_capacity': kw.get('seating_capacity'),
                }
                return http.request.render('vehicle_subscription.vehicle_form',
                                           data)
            else:
                return http.request.render(
                    'vehicle_subscription.subscription_vehicle_missing')
        else:
            return http.request.render('vehicle_subscription.vehicle_form')

    @http.route(['/online/subscription/book'], type='json', auth="public",
                website=True)
    def get_vehicle(self, **kwargs):
        """Ajax RPC handler for booking vehicle subscription and
         creating corresponding invoices in the backend."""
        extra_km = kwargs.get('extra_km')
        product_template_id = (request.env.ref(
            'vehicle_subscription.product_template_vehicle_subscription_form').
                               id)
        vehicle = int(kwargs.get('vehicle'))
        customer = kwargs.get('customer')
        checked = bool(kwargs.get('checked'))
        vehicle_id = request.env['fleet.vehicle'].sudo().browse(int(vehicle))
        customer_id = request.env['res.partner'].sudo().search(
            [('name', '=', customer)])
        if extra_km == '':
            km = 0
        else:
            km = extra_km
        fuel_choice = kwargs.get('fuel_choice')
        seating_capacity = int(kwargs.get('seating_capacity')) if kwargs.get('seating_capacity') else vehicle_id.model_id.seats
        
        insurance_rec = False
        if vehicle_id.insurance:
            try:
                ins_type_id = int(vehicle_id.insurance)
                insurance_rec = request.env['vehicle.insurance'].sudo().search([
                    ('vehicle_id', '=', vehicle_id.id),
                    ('insurance_type_id.id', '=', ins_type_id)
                ], limit=1)
            except (ValueError, TypeError):
                pass
        if not insurance_rec:
            insurance_rec = request.env['vehicle.insurance'].sudo().search([
                ('vehicle_id', '=', vehicle_id.id)
            ], limit=1)

        payment_type = kwargs.get('invoice_type')
        if not payment_type or payment_type not in ['full', 'monthly']:
            payment_type = 'monthly' if kwargs.get('invoice') in ['true', '1', 1, True] else 'full'

        subscribe = request.env['fleet.subscription'].sudo().create({
            'vehicle_id': vehicle_id.id,
            'customer_id': customer_id.id,
            'insurance_type_id': insurance_rec.id if insurance_rec else False,
            'start_date': vehicle_id.start,
            'end_date': vehicle_id.end,
            'extra_km': km,
            'fuel': fuel_choice if fuel_choice else False,
            'payment_type': payment_type,
            'seating_capacity': seating_capacity,
            'fuel_rate': vehicle_id.fuel_rate,
            'charge_km': vehicle_id.charge_km,
            'city': kwargs.get('city'),
            'state_id': int(kwargs.get('state_id')) if kwargs.get('state_id') else False,
            'country_id': int(kwargs.get('country_id')) if kwargs.get('country_id') else False,
        })
        subscribe.action_invoice()
        subscribe.sale_id.action_confirm()

        if payment_type == 'full' or vehicle_id.duration <= 30:
            created_invoices = subscribe.sale_id._create_invoices()
            created_invoices.action_post()
            for inv in created_invoices:
                inv.is_subscription = True
                subscribe.invoice_ids = [(4, inv.id)]
        else:
            subscribe.sale_id.invoice_status = 'invoiced'
            total_price = subscribe.sale_id.order_line.price_unit
            duration = vehicle_id.duration if vehicle_id.duration > 0 else 1
            per_day = total_price / duration
            start_date = vehicle_id.start
            end_date = vehicle_id.end
            curr_start = start_date
            while curr_start < end_date:
                curr_end = min(curr_start + timedelta(days=30), end_date)
                chunk_days = (curr_end - curr_start).days
                if chunk_days <= 0:
                    break
                inv_amount = per_day * chunk_days
                gen_inv = request.env['account.move'].sudo().create({
                    'move_type': 'out_invoice',
                    'partner_id': customer_id.id,
                    'invoice_date': curr_end,
                    'invoice_origin': subscribe.sale_id.name,
                    'invoice_line_ids': [(0, 0, {
                        'product_id': product_id.id,
                        'name': vehicle_id.name,
                        'price_unit': inv_amount,
                        'sale_line_ids': [(4, subscribe.sale_id.order_line[0].id)],
                    })]
                })
                gen_inv.is_subscription = True
                gen_inv.action_post()
                subscribe.sale_id.invoice_ids = [(4, gen_inv.id)]
                subscribe.invoice_ids = [(4, gen_inv.id)]
                curr_start = curr_end
        values = {
            'subscription_id': subscribe.id
        }
        return values

    @http.route(['/next/vehicle', '/next/vehicle/<int:subscription_id>'],
                auth='public', website=True, type='http')
    def subscription_create(self):
        """Return template for successful subscription"""
        current_vehicle = request.env['fleet.subscription'].sudo().search([
            ('customer_id', '=', request.env.user.partner_id.id),
            ('state', '=', 'subscribed'),
        ], order='write_date desc', limit=1)
        context = {
            'vehicle_name': current_vehicle.vehicle_id.name,
            'customer_name': request.env.user.partner_id.name,
        }
        return request.render('vehicle_subscription.subscription_form_success',
                              context)

    def _get_insurance_per_day(self, vehicle):
        """Helper method to resolve daily insurance rate for a fleet.vehicle"""
        ins_rec = False
        if vehicle.insurance:
            try:
                ins_type_id = int(vehicle.insurance)
                ins_rec = request.env['vehicle.insurance'].sudo().search([
                    ('vehicle_id', '=', vehicle.id),
                    ('insurance_type_id.id', '=', ins_type_id)
                ], limit=1)
            except (ValueError, TypeError):
                pass
        if not ins_rec:
            ins_rec = request.env['vehicle.insurance'].sudo().search([
                ('vehicle_id', '=', vehicle.id)
            ], limit=1)
        return ins_rec.insurance_amount_per_day if ins_rec else 0.0

    @http.route(['/online/subscription/with/fuel'], type='json', auth="public",
                website=True)
    def get_with_fuel(self, **kwargs):
        """Calculate price for vehicle with fuel option"""
        vehicle_id = int(kwargs.get('vehicle'))
        km = float(kwargs.get('extra_km') or 0)
        vehicle = request.env['fleet.vehicle'].sudo().browse(vehicle_id)
        vehicle.write({'extra_km': km})
        insurance_per_day = self._get_insurance_per_day(vehicle)
        base_price = vehicle.duration * (vehicle.subscription_price + insurance_per_day)
        extra_fuel_charge = 0.0
        mileage = vehicle.model_id.mileage or 12.0
        if km > 0 and mileage > 0:
            extra_fuel_charge = (km / mileage) * vehicle.fuel_rate
        new_price = base_price + extra_fuel_charge
        return str(round(new_price, 3))

    @http.route(['/online/subscription/without/fuel'], type='json',
                auth="public", website=True)
    def get_without_fuel(self, **kwargs):
        """Calculate price for vehicle without fuel option"""
        vehicle_id = int(kwargs.get('vehicle'))
        km = float(kwargs.get('extra_km') or 0)
        vehicle = request.env['fleet.vehicle'].sudo().browse(vehicle_id)
        vehicle.write({'extra_km': km})
        insurance_per_day = self._get_insurance_per_day(vehicle)
        base_price = vehicle.duration * (vehicle.subscription_price + insurance_per_day)
        extra_km_charge = 0.0
        if km > 0:
            extra_km_charge = km * vehicle.charge_km
        new_price = base_price + extra_km_charge
        return str(round(new_price, 3))

    @http.route('/online/subscription/cancel', auth='public', website=True)
    def cancellation_form(self):
        """Cancel subscription form through website"""
        customer_id = request.env['res.partner'].sudo().search(
            [('name', '=', request.env.user.partner_id.name)])
        vehicle_id = request.env['fleet.subscription'].sudo().search(
            [('customer_id', '=', customer_id.id),
             ('state', '=', 'subscribed')])
        vals = {
            'customers': customer_id.name,
            'vehicles': vehicle_id,
        }
        return http.request.render(
            'vehicle_subscription.subscription_cancellation_form', vals)

    @http.route('/online/choose/vehicle', type='json', auth="public",
                website=True)
    def choose_vehicle(self, **kwargs):
        """Only display vehicle of selected customer in website"""
        customer = kwargs.get('customer_id')
        customer_id = request.env['res.partner'].sudo().search(
            [('name', '=', customer)], limit=1)
        if not customer_id and request.env.user.partner_id:
            customer_id = request.env.user.partner_id

        subscriptions = request.env['fleet.subscription'].sudo().search([
            ('state', '=', 'subscribed'),
            ('customer_id', '=', customer_id.id)
        ])
        result = [(sub.vehicle_id.id, sub.vehicle_id.name) for sub in subscriptions if sub.vehicle_id]
        return result

    @http.route('/online/cancellation/click', auth='public', type='http',
                website=True)
    def cancellation_click_form(self, **kwargs):
        """Proceed with cancellation button click"""
        customer = kwargs.get('customer')
        vehicle_param = int(kwargs.get('vehicle'))
        reason = kwargs.get('reason')
        customer_id = request.env['res.partner'].sudo().search(
            [('name', '=', customer)], limit=1)
        if not customer_id and request.env.user.partner_id:
            customer_id = request.env.user.partner_id

        # Safely check whether passed parameter is fleet.vehicle ID or fleet.subscription ID
        vehicle_rec = request.env['fleet.vehicle'].sudo().browse(vehicle_param)
        if vehicle_rec.exists():
            vehicle_id = vehicle_rec
        else:
            subscription = request.env['fleet.subscription'].sudo().browse(vehicle_param)
            if not subscription.exists():
                subscription = request.env['fleet.subscription'].sudo().search([
                    ('customer_id', '=', customer_id.id),
                    ('state', '=', 'subscribed')
                ], limit=1)
            vehicle_id = subscription.vehicle_id if subscription.exists() else vehicle_rec

        existing_request = request.env['cancellation.request'].sudo().search([
            ('customer_id', '=', customer_id.id),
            ('vehicle_id', '=', vehicle_id.id),
            ('state', '!=', 'approved')
        ], limit=1)
        if existing_request:
            values = {
                'customer': customer,
                'vehicle': vehicle_id.name if vehicle_id else '',
                'existing_request': existing_request,
            }
            return request.render(
                'vehicle_subscription.existing_cancellation_popup', values)
        cancel_request = request.env['cancellation.request'].sudo().create({
            'customer_id': customer_id.id,
            'vehicle_id': vehicle_id.id,
            'reason': reason,
        })
        values = {
            'customer': customer,
            'vehicle': vehicle_id.name if vehicle_id else '',
            'existing_request': cancel_request,
        }
        cancel_request.state = 'to_approve'
        return request.render('vehicle_subscription.booking_cancellation',
                              values)

    @http.route('/online/subscription/change', auth='public', website=True)
    def subscription_change_form(self):
        """Rendered response for the subscription change form,
        containing the available subscribed vehicles for the logged-in customer."""
        partner = request.env.user.partner_id
        customer_id = request.env['res.partner'].sudo().search(
            [('id', '=', partner.id)], limit=1)

        subscriptions = request.env['fleet.subscription'].sudo().search([
            ('customer_id', '=', partner.id),
            ('state', '=', 'subscribed')
        ])
        vehicles = subscriptions.mapped('vehicle_id')

        # Check for any active pending subscription change requests
        existing_request = request.env['subscription.request'].sudo().search([
            ('customer_id', '=', partner.id),
            ('current_vehicle_id', 'in', vehicles.ids),
            ('state', '!=', 'cancel'),
            ('is_subscription', '!=', True)
        ], limit=1)

        if existing_request:
            values = {
                'customer': partner.name,
                'current_vehicle': existing_request.current_vehicle_id.name,
                'existing_request': existing_request,
            }
            return request.render(
                'vehicle_subscription.existing_subscription_popup', values)

        # Exclude vehicles that already submitted a change
        already_requests = request.env['subscription.request'].sudo().search([
            ('customer_id', '=', partner.id),
            ('current_vehicle_id', 'in', vehicles.ids),
            ('state', '!=', 'cancel'),
            ('is_subscription', '=', True)
        ])
        already_vehicle_ids = already_requests.mapped('current_vehicle_id.id')
        filtered_vehicles = vehicles.filtered(lambda v: v.id not in already_vehicle_ids)

        vals = {
            'vehicles': filtered_vehicles,
            'customers': partner.name,
        }
        return request.render(
            'vehicle_subscription.subscription_change_form', vals)

    @http.route('/online/subscription/change/vehicle', auth='public',
                type='http', website=True)
    def change_click_form(self, **kwargs):
        """ Rendered response based on the conditions:
         - If checkbox_model is 'on', list available vehicles of the same model.
         - If checkbox_model is not 'on', list available vehicles of different models.
         - Renders subscription_change_button template for vehicle selection."""
        if kwargs.get('customer'):
            customer = kwargs.get('customer')
            vehicle_param = int(kwargs.get('vehicle'))
            reason = kwargs.get('reason')
            checkbox = kwargs.get('checkbox_model')
            customer_id = request.env['res.partner'].sudo(). \
                search([('name', '=', customer)], limit=1)
            if not customer_id and request.env.user.partner_id:
                customer_id = request.env.user.partner_id

            # Safely check whether passed parameter is fleet.vehicle ID or fleet.subscription ID
            vehicle_id = request.env['fleet.vehicle'].sudo().browse(vehicle_param)
            if not vehicle_id.exists():
                sub = request.env['fleet.subscription'].sudo().browse(vehicle_param)
                if sub.exists() and sub.vehicle_id:
                    vehicle_id = sub.vehicle_id
                else:
                    sub = request.env['fleet.subscription'].sudo().search([
                        ('customer_id', '=', customer_id.id),
                        ('state', '=', 'subscribed')
                    ], limit=1)
                    if sub and sub.vehicle_id:
                        vehicle_id = sub.vehicle_id

            if checkbox == 'on':
                new_vehicle_id = request.env['fleet.vehicle'].sudo().search([
                    ('model_id', '=', vehicle_id.model_id.id),
                    ('id', '!=', vehicle_id.id)
                ])
            else:
                new_vehicle_id = request.env['fleet.vehicle'].sudo().search([
                    ('model_id', '!=', vehicle_id.model_id.id),
                    ('id', '!=', vehicle_id.id)
                ])
            values = {
                'customer_name': customer_id.name,
                'vehicle_name': vehicle_id.name if vehicle_id.exists() else '',
                'vehicle_id': vehicle_id.id if vehicle_id.exists() else False,
                'vehicles': new_vehicle_id,
                'reason': reason,
            }
            return request.render(
                'vehicle_subscription.subscription_change_button', values)
        else:
            return request.render(
                'vehicle_subscription.subscription_change_boolean_false')

    @http.route('/online/subscription/change/button', auth='public',
                type='http', website=True)
    def click_form(self, **kwargs):
        """Rendered response for the
            'vehicle_subscription.change_subscription' template. """
        customer = kwargs.get('customer')
        reason = kwargs.get('reason')
        vehicle_param = kwargs.get('vehicle_id') or kwargs.get('vehicle')
        new_vehicle_param = kwargs.get('new_vehicle')

        customer_id = request.env['res.partner'].sudo().search([('name', '=', customer)], limit=1)
        if not customer_id and request.env.user.partner_id:
            customer_id = request.env.user.partner_id

        # Resolve current_vehicle_id safely
        current_vehicle_id = False
        if vehicle_param:
            if str(vehicle_param).isdigit():
                current_vehicle_id = request.env['fleet.vehicle'].sudo().browse(int(vehicle_param))
            if not current_vehicle_id or not current_vehicle_id.exists():
                current_vehicle_id = request.env['fleet.vehicle'].sudo().search([('name', '=', str(vehicle_param))], limit=1)

        # Resolve new_vehicle safely
        new_vehicle = False
        if new_vehicle_param and str(new_vehicle_param).isdigit():
            new_vehicle = request.env['fleet.vehicle'].sudo().browse(int(new_vehicle_param))

        if not new_vehicle or not new_vehicle.exists() or not current_vehicle_id or not current_vehicle_id.exists():
            return request.redirect('/online/subscription/change')

        change_subscription = request.env['subscription.request'].sudo().create({
            'current_vehicle_id': current_vehicle_id.id,
            'new_vehicle_id': new_vehicle.id,
            'reason_to_change': reason,
            'customer_id': customer_id.id,
            'is_subscription': True,
            'state': 'to_approve',
        })
        return request.render('vehicle_subscription.change_subscription')

    @http.route('/online/proceed/cancellation', auth='public', type='http',
                website=True)
    def proceed_cancellation(self):
        """Proceed with cancellation in change subscription """
        return request.redirect('/online/subscription/cancel')

    @http.route(['/web/signup/user'], type='http', auth="user",
                website=True)
    def redirect_login(self):
        """Used to redirect on clicking signup page"""
        return request.redirect('/online/subscription')
