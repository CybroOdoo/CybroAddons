# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Rahna Rasheed (<https://www.cybrosys.com>)
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
from odoo import http
from odoo.http import request


class OnlineSubscription(http.Controller):
    """Online Vehicle subscription through website"""

    @http.route(['/online/subscription/city'], type='json', auth="public",
                website=True)
    def get_city(self, **kwargs):
        """Calling this function using ajax rpc in order to get city
        based on state """
        state = int(kwargs.get('state'))
        vehicle = request.env['fleet.vehicle'].sudo().search(
            [('states_id', '=', state)])
        states = [city.location for city in vehicle]
        return [*set(states)]

    @http.route('/online/subscription', auth='public', website=True)
    def subscription_form(self):
        """This function will return vehicle  with which state is not null"""
        vehicle_id = request.env['fleet.vehicle'].sudo().search(
            [('states_id', '!=', False)])
        insurance_type = request.env['insurance.type'].sudo().search([])
        vals = {
            'states': vehicle_id.states_id,
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
            states = kw.get('state')
            city = kw.get('city')
            start_date = kw.get('start_date')
            end_date = kw.get('end_date')
            insurance = kw.get('insurance_type')
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            seats = kw.get('seating_capacity')
            insurance_amount = request.env['vehicle.insurance'].sudo().browse(
                int(insurance)).insurance_amount
            insurance_type = request.env['vehicle.insurance'].sudo().search(
                [('insurance_type_id.id', '=', insurance),
                 ('start_date', '<=', start), ('end_date', '>=', end)])
            vehicle_ids = insurance_type.vehicle_id
            subscribed_vehicle_id = (request.env['fleet.subscription'].sudo().
                                     search(
                [('state', '=', 'subscribed')]).vehicle_id)
            vehicle = request.env['fleet.vehicle'].sudo().search(
                [('id', 'in', vehicle_ids.ids), ('states_id', '=', int(states)),
                 ('location', '=', city),
                 ('seats', '=', int(seats))])
            vehicle_id = vehicle.filtered(
                lambda v: v.id not in subscribed_vehicle_id.ids)
            if vehicle_id:
                for rec in vehicle_id:
                    rec.write({
                        'insurance': insurance,
                        'start': start,
                        'end': end,
                    })
                data = {
                    'vehicles': vehicle_id,
                    'amount': insurance_amount,
                    'customers': request.env.user.partner_id.name,
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
        product_id = request.env['product.product'].sudo().search(
            [('product_tmpl_id', '=', product_template_id)])
        vehicle = int(kwargs.get('vehicle'))
        customer = kwargs.get('customer')
        checked = int(kwargs.get('checked'))
        invoice_type = int(kwargs.get('invoice'))
        vehicle_id = request.env['fleet.vehicle'].sudo().browse(int(vehicle))
        customer_id = request.env['res.partner'].sudo().search(
            [('name', '=', customer)])
        if extra_km == '':
            km = 0
        else:
            km = extra_km
        subscribe = request.env['fleet.subscription'].sudo().create({
            'vehicle_id': vehicle_id.id,
            'customer_id': customer_id.id,
            'insurance_type_id': vehicle_id.insurance,
            'start_date': vehicle_id.start,
            'end_date': vehicle_id.end,
            'extra_km': km,
            'fuel': 'without_fuel' if checked == False else 'with_fuel'
        })
        subscribe.action_invoice()
        subscribe.sale_id.action_confirm()
        if invoice_type:
            subscribe.sale_id._create_invoices().action_post()
            subscribe.invoice_ids.is_subscription = True
            subscribe.sale_id.invoice_ids.is_subscription = True
        else:
            subscribe.sale_id.invoice_status = 'invoiced'
            total_price = subscribe.sale_id.order_line.price_unit
            duration = vehicle_id.duration
            per_day = total_price / duration
            start_date = vehicle_id.start
            end_date = vehicle_id.end
            next_invoice_day = start_date
            while next_invoice_day <= end_date:
                next_invoice_day = next_invoice_day + timedelta(days=30)
                if next_invoice_day <= end_date:
                    durations = (next_invoice_day - start_date).days
                    generate_invoice = request.env[
                        'account.move'].sudo().create({
                            'move_type': 'out_invoice',
                            'partner_id': customer_id.id,
                            'invoice_date': next_invoice_day,
                            'invoice_origin': subscribe.sale_id.name,
                            'invoice_line_ids': [(0, 0, {
                                'product_id': product_id.id,
                                'name': vehicle_id.name,
                                'price_unit': per_day * durations,
                            })]
                        })
                    generate_invoice.is_subscription = True
                    generate_invoice.action_post()
                    subscribe.sale_id.invoice_ids = [(4, generate_invoice.id)]
                    subscribe.invoice_ids = [(4, generate_invoice.id)]
                else:
                    next_invoice_day = end_date
                    durations = (next_invoice_day - start_date).days
                    generate_invoice = request.env[
                        'account.move'].sudo().create({
                            'move_type': 'out_invoice',
                            'partner_id': customer_id.id,
                            'invoice_date': next_invoice_day,
                            'invoice_line_ids': [(0, 0, {
                                'product_id': product_id.id,
                                'name': vehicle_id.name,
                                'price_unit': per_day * durations,
                            })]
                        })
                    generate_invoice.is_subscription = True
                    generate_invoice.action_post()
                    subscribe.sale_id.invoice_ids = [(4, generate_invoice.id)]
                    subscribe.invoice_ids = [(4, generate_invoice.id)]
                    break
                start_date = start_date + timedelta(days=30)
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

    @http.route(['/online/subscription/with/fuel'], type='json', auth="public",
                website=True)
    def get_with_fuel(self, **kwargs):
        """Calculate price for vehicle according to fuel type """
        vehicle = int(kwargs.get('vehicle'))
        km = kwargs.get('extra_km')
        vehicle = request.env['fleet.vehicle'].sudo().browse(vehicle)
        vehicle.write({
            'extra_km': km,
        })
        insurance_amount = vehicle.insurance
        amount = request.env['vehicle.insurance'].sudo() \
            .browse(int(insurance_amount)).insurance_amount
        if float(km) > vehicle.free_km:
            new_price = (((vehicle.extra_km / vehicle.mileage) *
                          vehicle.fuel_rate) +
                         (vehicle.duration * vehicle.subscription_price) +
                         amount)
        else:
            if float(km) <= vehicle.free_km:
                new_price = ((vehicle.duration * vehicle.subscription_price) +
                             amount)
        return str(new_price)

    @http.route(['/online/subscription/without/fuel'], type='json',
                auth="public",
                website=True)
    def get_without_fuel(self, **kwargs):
        """Calculate price for vehicle according to fuel type """
        vehicle = int(kwargs.get('vehicle'))
        km = kwargs.get('extra_km')
        vehicle = request.env['fleet.vehicle'].sudo().browse(vehicle)
        insurance_amount = vehicle.insurance
        amount = request.env['vehicle.insurance'].sudo() \
            .browse(int(insurance_amount)).insurance_amount
        vehicle.write({
            'extra_km': km,
        })
        if float(km) > vehicle.free_km:
            new_price = (((vehicle.duration * vehicle.subscription_price) +
                          amount) + (vehicle.charge_km * vehicle.extra_km))
        else:
            new_price = (vehicle.duration * vehicle.subscription_price) + amount
        return str(new_price)

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
        """Only display vehicle of  selected customer in website"""
        customer = kwargs.get('customer_id')
        customer_id = request.env['res.partner'].sudo().search(
            [('name', '=', customer)])
        vehicle_id = request.env['fleet.subscription'].sudo().search(
            [('state', '=', 'subscribed'),
             ('customer_id', '=', customer_id.id)]).mapped('vehicle_id')
        if vehicle_id:
            vehicle = [(rec.id, rec.name) for rec in vehicle_id]
        return [*set(vehicle)]

    @http.route('/online/cancellation/click', auth='public', type='http',
                website=True)
    def cancellation_click_form(self, **kwargs):
        """Proceed with cancellation button click"""
        customer = kwargs.get('customer')
        vehicle = int(kwargs.get('vehicle'))
        reason = kwargs.get('reason')
        customer_id = request.env['res.partner'].sudo().search(
            [('name', '=', customer)])
        vehicle_id = request.env['fleet.vehicle'].sudo().browse(vehicle)
        cancel_request = request.env['cancellation.request'].sudo().create({
            'customer_id': customer_id.id,
            'vehicle_id': vehicle_id.id,
            'reason': reason,
        })
        values = {
            'customer': customer,
            'vehicle': vehicle_id.name,
        }
        cancel_request.state = 'to_approve'
        return request.render('vehicle_subscription.booking_cancellation',
                              values)

    @http.route('/online/subscription/change', auth='public', website=True)
    def subscription_change_form(self):
        """Rendered response for the 'vehicle_subscription.
        subscription_change_form' template,
         containing the available vehicles and the current customer's name."""
        vehicle = request.env['fleet.vehicle'].sudo().search(
            [('states_id', '!=', False)])
        customer = request.env.user.partner_id.name
        customer_id = request.env['res.partner'].sudo().search(
            [('name', '=', customer)])
        vals = {
            'vehicles': vehicle,
            'customers': customer_id.name,
        }
        return http.request.render(
            'vehicle_subscription.subscription_change_form', vals)

    @http.route('/online/subscription/change/vehicle', auth='public',
                type='http', website=True)
    def change_click_form(self, **kwargs):
        """ Rendered response based on the conditions:
         - If the 'customer' parameter exists, render the
         'vehicle_subscription.subscription_change_button' template
           with the provided data.
         - If the 'customer' parameter does not exist, render the
         'vehicle_subscription.subscription_change_boolean_false'
           template."""
        if kwargs.get('customer'):
            customer = kwargs.get('customer')
            vehicle = int(kwargs.get('vehicle'))
            reason = kwargs.get('reason')
            checkbox = kwargs.get('checkbox_model')
            customer_id = request.env['res.partner'].sudo(). \
                search([('name', '=', customer)])
            vehicle_id = request.env['fleet.vehicle'].sudo().browse(vehicle)
            new_vehicle_id = request.env['fleet.vehicle'].sudo() \
                .search([('model_id', '=', vehicle_id.model_id.id)])
            if checkbox == 'on':
                values = {
                    'customer_name': customer_id.name,
                    'vehicle_name': vehicle_id.name,
                    'vehicles': [rec for rec in new_vehicle_id],
                    'reason': reason,
                }
                return request.render(
                    'vehicle_subscription.subscription_change_button', values)
            else:
                return request.render(
                    'vehicle_subscription.subscription_change_boolean_false')
        else:
            return request.render(
                'vehicle_subscription.subscription_change_button')

    @http.route('/online/subscription/change/button', auth='public',
                type='http', website=True)
    def click_form(self, **kwargs):
        """Rendered response for the
            'vehicle_subscription.change_subscription' template. """
        customer = kwargs.get('customer')
        reason = kwargs.get('reason')
        current_vehicle = kwargs.get('vehicle')
        vehicle_id = int(kwargs.get('new_vehicle'))
        current_vehicle_id = request.env['fleet.vehicle'].sudo() \
            .search([('name', '=', current_vehicle)])
        customer_id = request.env['res.partner'].sudo() \
            .search([('name', '=', customer)])
        vehicle = request.env['fleet.vehicle'].sudo().browse(vehicle_id)
        change_subscription = request.env['subscription.request'] \
            .sudo().create({
                'current_vehicle': current_vehicle_id.id,
                'new_vehicle_id': vehicle.id,
                'reason_to_change': reason,
                'customer_id': customer_id.id,
            })
        change_subscription.state = 'to_approve'
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
