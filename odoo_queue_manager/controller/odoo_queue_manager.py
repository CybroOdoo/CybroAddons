# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
import re
from datetime import datetime
from odoo import http, fields
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class GenerateToken(CustomerPortal):
    """Controller for handling token generation and queue management."""

    @http.route(
        '/generate/token',
        type='http',
        auth='public',
        website=True
    )
    def generate_token(self, **kwargs):
        """Render the token generation page with available departments."""
        department_rec = request.env['department'].sudo().search([])

        action = request.env['ir.actions.actions']._for_xml_id(
            'odoo_queue_manager.queue_counter_action'
        )['id']

        return request.render(
            'odoo_queue_manager.generate_token',
            {
                'department': department_rec,
                'action': action,
                'form_data': {},
            }
        )

    @http.route(
        '/create/token',
        type='http',
        auth='public',
        website=True,
        methods=['POST']
    )
    def create_token(self, **post):
        """Create a queue token for the selected department."""

        department_rec = request.env['department'].sudo().search([])

        action = request.env['ir.actions.actions']._for_xml_id(
            'odoo_queue_manager.queue_counter_action'
        )['id']

        def render_error(message):
            return request.render(
                'odoo_queue_manager.generate_token',
                {
                    'department': department_rec,
                    'action': action,
                    'error': message,
                    'form_data': post,
                }
            )

        name = (post.get('name') or '').strip()
        mobile = (post.get('mobile') or '').strip()
        department_id = post.get('department')

        # Name validation
        if not name:
            return render_error('Please enter your name.')

        # Department validation
        if not department_id:
            return render_error('Please select a department.')

        try:
            department = request.env['department'].sudo().browse(
                int(department_id)
            )
        except (TypeError, ValueError):
            return render_error('Selected department is invalid.')

        if not department.exists():
            return render_error('Selected department is invalid.')

        # Mobile validation
        pattern = r'^\+?[0-9()\-\s]{7,20}$'

        if not mobile:
            return render_error('Please enter a mobile number.')

        if not re.fullmatch(pattern, mobile):
            return render_error('Please enter a valid phone number.')

        today = fields.Date.today()

        start_dt = datetime.combine(
            today,
            datetime.min.time()
        )

        end_dt = datetime.combine(
            today,
            datetime.max.time()
        )

        last_token = request.env['token.token'].sudo().search(
            [
                ('department_id', '=', department.id),
                ('token_datetime', '>=', start_dt),
                ('token_datetime', '<=', end_dt),
            ],
            order='id desc',
            limit=1
        )

        next_token = 1

        if (
            last_token
            and last_token.token
            and last_token.token.isdigit()
        ):
            next_token = int(last_token.token) + 1

        new_token = request.env['token.token'].sudo().create({
            'token': str(next_token),
            'customer_name': name,
            'department_id': department.id,
            'mobile': mobile,
            'state': 'draft',
        })

        position = request.env['token.token'].sudo().search_count([
            ('department_id', '=', department.id),
            ('state', '=', 'draft'),
            ('id', '<=', new_token.id),
        ])

        current_token = request.env['token.token'].sudo().search(
            [
                ('department_id', '=', department.id),
                ('state', '=', 'in_progress'),
            ],
            limit=1
        )

        try:
            action_id = request.env['ir.actions.actions']._for_xml_id(
                'odoo_queue_manager.token_interface_action'
            ).get('id')
        except Exception:
            action_id = False
        menu_id = int(post.get('menu_id') or 0)
        return request.render(
            'odoo_queue_manager.token_detail',
            {
                'name': name,
                'mobile_number': mobile,
                'token': f'{department.code}-{next_token}',
                'department': department,
                'token_id': new_token.id,
                'action_id': action_id,
                'menu_id': menu_id,
                'position': position,
                'current_token': current_token,
            }
        )

    @http.route('/queue/counter/<int:department_id>/<int:counter_id>',
                type='http', auth="user", website=True)
    def counter_processing(self, department_id, counter_id):
        """Display the queue interface showing all tokens and the next token."""
        department = request.env['department'].sudo().browse(department_id)
        counter = request.env['queue.counter'].sudo().browse(counter_id)

        tokens = request.env['token.token'].sudo().search([
            ('department_id', '=', department_id)
        ], order='id asc')

        token_next = request.env['token.token'].sudo().search([
            ('department_id', '=', department_id),
            ('state', '=', 'draft')
        ], order='id asc', limit=1)

        return request.render('odoo_queue_manager.queue_counter', {
            'user': request.env.user.name,
            'department': department.name,
            'counter': counter,
            'tokens': tokens,
            'token_next': token_next
        })

    @http.route('/queue/display/<int:counter_id>',
                type='http',
                auth='public',
                website=True)
    def queue_display_screen(self, counter_id):
        """Render the public display screen with current and waiting tokens."""
        counter = request.env['queue.counter'].sudo().browse(counter_id)

        current_token = request.env['token.token'].sudo().search([
            ('counter_id', '=', counter_id),
            ('state', '=', 'in_progress')
        ], limit=1)

        waiting_tokens = request.env['token.token'].sudo().search([
            ('department_id', '=',
             current_token.department_id.id if current_token else False),
            ('state', 'in', ['draft', 'recall'])
        ], order='id asc', limit=8)

        return request.render(
            'odoo_queue_manager.queue_display_screen',
            {
                'counter': counter,
                'current_token': current_token,
                'waiting_tokens': waiting_tokens,
            }
        )

    @http.route('/process/individual/token/<int:token_next>/<int:counter>',
                type='http', auth="user", website=True)
    def individual_queue_processing(self, token_next, counter):
        """Process the next token by marking previous as done and setting current in progress."""
        current_token = request.env['token.token'].sudo().browse(token_next)

        request.env['token.token'].sudo().search([
            ('counter_id', '=', counter),
            ('state', '=', 'in_progress')
        ]).write({'state': 'done'})

        current_token.write({
            'state': 'in_progress',
            'counter_id': counter
        })
        if current_token.exists():
            return request.render(
                'odoo_queue_manager.individual_queue_processing',
                {
                    'current_token': current_token,
                    'counter_id': counter
                }
            )
        else:
            return request.render('odoo_queue_manager.page_empty_queue', {})

    @http.route('/empty/token', type='http', auth="user", website=True)
    def empty_token(self):
        """Render a page indicating that no tokens are available."""
        return request.render('odoo_queue_manager.page_empty_queue', {})

    @http.route('/queue/submit/<int:token_id>/<int:counter_id>',
                type='http',
                auth='user',
                website=True,
                methods=['POST'])
    def queue_submit(self, token_id, counter_id, **post):
        """Update token state based on action and redirect to the queue interface."""
        token = request.env['token.token'].sudo().browse(token_id)
        if not token.exists():
            return request.redirect('/empty/token')

        token_state = post.get('token_state')
        customer_query = post.get('customer_query')
        feedback = post.get('feedback')
        if token_state == 'recall':
            token.write({'state': 'recall'})
        elif token_state == 'done':
            request.env['queue.process'].sudo().create({
                'counter_id': counter_id,
                'user_id': request.env.uid,
                'department_id': token.department_id.id,
                'customer_name': token.customer_name,
                'customer_query': customer_query,
                'feedback': feedback,
                'processed_datetime': fields.Datetime.now(),
                'state': 'done',
            })
            token.write({'state': 'done'})
        elif token_state == 'cancelled':
            token.write({'state': 'cancelled'})
        return request.redirect(
            '/queue/counter/%s/%s'
            % (token.department_id.id, counter_id)
        )

    @http.route('/action/print/<model("token.token"):token>', type='http',
                auth="user", website=True)
    def action_print_report(self, token):
        """Generate and download the token PDF report."""
        if not token.exists():
            return request.redirect('/generate/token')

        return self._show_report(
            model=token,
            report_type='pdf',
            report_ref='odoo_queue_manager.action_token_report',
            download=True
        )
