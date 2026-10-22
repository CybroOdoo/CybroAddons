# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Safa KB (odoo@cybrosys.com)
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
from odoo import fields, http
from odoo.exceptions import ValidationError
from odoo.http import request

CLEANING_TIMES = ('morning', 'evening', 'night')


class CleaningRequest(http.Controller):
    """Controller for the cleaning website form."""

    @http.route('/cleaning/available_teams', type='jsonrpc', auth='public',
                website=True)
    def available_teams(self, cleaning_date=None, cleaning_time=None):
        """Teams of the chosen shift that are free on the chosen date."""
        if cleaning_time not in CLEANING_TIMES:
            return []
        try:
            date = fields.Date.to_date(cleaning_date)
        except (ValueError, TypeError):
            return []
        if not date:
            return []
        busy_teams = request.env['cleaning.team.duty'].sudo().search([
            ('cleaning_date', '=', date),
            ('cleaning_time', '=', cleaning_time),
            ('state', 'not in', ['cancelled', 'cleaned']),
        ]).team_id
        teams = request.env['cleaning.team'].sudo().search([
            ('duty_type', '=', cleaning_time),
            ('id', 'not in', busy_teams.ids),
        ])
        return [{'id': team.id, 'name': team.name} for team in teams]

    @staticmethod
    def _get_form_values(**extra):
        """Values needed to render the booking form template."""
        env = request.env
        values = {
            'customer_name_rec': env.user.partner_id,
            'building_type_rec': env['building.type'].sudo().search([]),
            'location_state_id': env['res.country.state'].sudo().search([]),
            'cleaning_team_id': env['cleaning.team'].sudo().search([]),
        }
        values.update(extra)
        return values

    @http.route(['/cleaning/request/form'], type='http',
                auth="user", website=True)
    def request_form(self):
        """Render the online booking form."""
        return request.render("cleaning_management.cleaning_online_request",
                              self._get_form_values())

    @http.route(['/cleaning/request/form/submit'], type='http',
                auth="user", website=True)
    def online_request_cleaning_form(self, **kw):
        """Validate and store the submitted booking, never returns a 500."""
        try:
            cleaning_date_raw = kw.get('cleaning_date')
            if not cleaning_date_raw:
                raise ValidationError(request.env._("Cleaning date is required."))
            cleaning_date = fields.Date.to_date(cleaning_date_raw)
            required = {
                'customer_name_id': request.env._("Customer"),
                'address': request.env._("Address"),
                'building_type_id': request.env._("Building Type"),
                'cleaning_team_id': request.env._("Cleaning Team"),
                'location_state_id': request.env._("State"),
            }
            for field, label in required.items():
                if not kw.get(field):
                    raise ValidationError(request.env._("%s is required.", label))
            if int(kw['customer_name_id']) != request.env.user.partner_id.id:
                raise ValidationError(request.env._(
                    "You can only book for your own account."))
            if kw.get('cleaning_time') not in CLEANING_TIMES:
                raise ValidationError(
                    request.env._("Please choose a valid cleaning time."))
            booking = request.env['cleaning.booking'].sudo().create({
                'customer_name_id': int(kw['customer_name_id']),
                'address': kw['address'],
                'building_type_id': int(kw['building_type_id']),
                'booking_date': kw.get('booking_date') or fields.Date.today(),
                'cleaning_date': cleaning_date,
                'cleaning_time': kw['cleaning_time'],
                'cleaning_team_id': int(kw['cleaning_team_id']),
                'location_state_id': int(kw['location_state_id']),
                'description': kw.get('description'),
            })
        except (ValidationError, ValueError, TypeError) as err:
            message = (str(err) if isinstance(err, ValidationError)
                       else request.env._("Invalid data submitted. Please check the form."))
            return request.render(
                "cleaning_management.cleaning_online_request",
                self._get_form_values(error=message))
        return request.render("cleaning_management.cleaning_online_thanks",
                              {'vals': booking})