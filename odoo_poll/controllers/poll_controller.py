# -*- coding: utf-8 -*-
################################################################################
#
#   Cybrosys Technologies Pvt. Ltd.
#
#   Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#   Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#   This program is free software: you can modify
#   it under the terms of the GNU Affero General Public License (AGPL) as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError


class PollController(http.Controller):
    """Controller for poll RPC endpoints"""

    @http.route('/discuss/poll/create', type='jsonrpc', auth='user')
    def create_poll(self, thread_id, thread_model, question, options, is_multiple_choice=False, company_id=None):
        """Create a new poll in a discuss thread"""
        import logging
        _logger = logging.getLogger(__name__)
        _logger.info("DEBUG CREATE POLL:")
        _logger.info("  Param company_id: %s", company_id)
        _logger.info("  Request env company: %s (%s)", request.env.company.name, request.env.company.id)
        _logger.info("  Request env companies: %s", request.env.companies)
        _logger.info("  Request context: %s", request.env.context)

        Poll = request.env['discuss.poll']
        PollOption = request.env['poll.option']

        # Determine target company
        _logger.info("DEBUG CREATE POLL: Param company_id=%s, Env company=%s, Env companies=%s", company_id, request.env.company.id, request.env.companies.ids)
        target_company_id = company_id or request.env.company.id

        # Create poll - use sudo to bypass strict company rule during creation
        poll = Poll.sudo().create({
            'question': question,
            'is_multiple_choice': is_multiple_choice,
            'company_id': target_company_id,
        })
        _logger.info("DEBUG CREATE POLL: Created Poll %s in Company %s", poll.id, poll.sudo().company_id.id)

        # Create options - use sudo
        for idx, option_text in enumerate(options):
            if option_text and option_text.strip():
                PollOption.sudo().create({
                    'name': option_text.strip(),
                    'poll_id': poll.id,
                    'sequence': idx + 1,
                })

        # Post message to thread
        thread = request.env[thread_model].browse(thread_id)
        message = thread.message_post(
            body=f'<div class="o_poll_message_container" data-poll-id="{poll.id}"></div>',
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
        )

        # Link poll to message - use sudo to ensure linking works across companies
        poll.sudo().write({'message_id': message.id})
        message.sudo().write({'poll_id': poll.id})

        # Try to get results - use sudo to ensure the creator sees the poll they just made
        poll_data = None
        try:
            poll_data = poll.sudo().get_results()
        except Exception:
            poll_data = {'id': poll.id, 'question': question, 'error': 'Access Restricted'}

        return {
            'poll_id': poll.id,
            'message_id': message.id,
            'poll_data': poll_data,
        }

    @http.route('/discuss/poll/vote', type='jsonrpc', auth='user')
    def vote(self, poll_id, option_ids, **kwargs):
        """Submit vote(s) for a poll"""
        import logging
        _logger = logging.getLogger(__name__)

        if kwargs.get('context'):
            request.update_context(**kwargs.get('context'))

        poll = request.env['discuss.poll'].sudo().browse(poll_id)

        if not poll.exists():
            return {'error': 'Poll not found'}

        # Strict isolation check
        if poll.company_id and poll.company_id.id != request.env.company.id:
            _logger.warning("Access denied to poll %s for voting: Company Mismatch", poll_id)
            return {'error': 'Access Denied'}

        try:
            # Force record rule check (as current user)
            poll.with_env(request.env).check_access_rule('read')
        except Exception as e:
            _logger.warning("Access denied to poll %s for voting: %s", poll_id, e)
            return {'error': 'Access Denied'}

        if poll.is_closed:
            return {'error': 'Poll is closed'}

        Vote = request.env['poll.vote']

        # Remove previous votes if single choice
        if not poll.is_multiple_choice:
            existing_votes = Vote.search([
                ('poll_id', '=', poll_id),
                ('voter_id', '=', request.env.user.partner_id.id)
            ])
            existing_votes.unlink()

        # Create new votes
        for option_id in option_ids:
            try:
                Vote.create({
                    'poll_id': poll_id,
                    'option_id': option_id,
                    'voter_id': request.env.user.partner_id.id,
                })
            except Exception as e:
                # Skip if already voted for this option
                continue

        return poll.get_results()

    @http.route('/discuss/poll/results', type='jsonrpc', auth='user')
    def get_results(self, poll_id, **kwargs):
        """Get poll results"""
        import logging
        _logger = logging.getLogger(__name__)

        # Apply context if passed to ensure correct company environment
        if kwargs.get('context'):
            request.update_context(**kwargs.get('context'))

        poll = request.env['discuss.poll'].sudo().browse(poll_id)

        if not poll.exists():
            return {'error': 'Poll not found'}

        # STRICT ISOLATION: Must match the current ACTIVE company
        active_company_id = request.env.company.id
        
        _logger.info("POLL ISOLATION CHECK (Strict):")
        _logger.info("  Poll ID: %s", poll_id)
        _logger.info("  Poll Company ID: %s", poll.company_id.id)
        _logger.info("  Active Env Company ID: %s", active_company_id)

        if poll.company_id and poll.company_id.id != active_company_id:
             _logger.info("  ISOLATION: Denied (Company Mismatch)")
             return {'error': 'Access Denied'}
            
        _logger.info("  ISOLATION: Allowed")

        # Use sudo here to calculate results. We've already verified company access above.
        return poll.sudo().get_results()

    @http.route('/discuss/poll/close', type='jsonrpc', auth='user')
    def close_poll(self, poll_id, **kwargs):
        """Close a poll (only author can close)"""
        import logging
        _logger = logging.getLogger(__name__)

        if kwargs.get('context'):
            request.update_context(**kwargs.get('context'))

        poll = request.env['discuss.poll'].sudo().browse(poll_id)

        if not poll.exists():
            return {'error': 'Poll not found'}

        # Isolation check: Must match the current ACTIVE company
        if poll.company_id and poll.company_id.id != request.env.company.id:
            _logger.warning("Access denied to close poll %s: Company Mismatch", poll_id)
            return {'error': 'Access Denied'}

        try:
            # Force record rule check (as current user)
            poll.with_env(request.env).check_access_rule('write')
        except Exception as e:
            _logger.warning("Access denied to close poll %s: %s", poll_id, e)
            return {'error': 'Access Denied'}

        if poll.author_id != request.env.user.partner_id:
            return {'error': 'Only poll author can close the poll'}

        poll.action_close()
        return {'success': True, 'poll_data': poll.get_results()}

    @http.route('/discuss/poll/remove_votes', type='jsonrpc', auth='user')
    def remove_votes(self, poll_id, **kwargs):
        """Remove current user's votes from poll"""
        import logging
        _logger = logging.getLogger(__name__)

        if kwargs.get('context'):
            request.update_context(**kwargs.get('context'))

        poll = request.env['discuss.poll'].sudo().browse(poll_id)
        if not poll.exists():
            return {'error': 'Poll not found'}

        if poll.company_id and poll.company_id.id != request.env.company.id:
            _logger.warning("Access denied to remove votes from poll %s: Company Mismatch", poll_id)
            return {'error': 'Access Denied'}

        try:
            poll.with_env(request.env).check_access_rule('read')
        except Exception as e:
            _logger.warning("Access denied to remove votes from poll %s: %s", poll_id, e)
            return {'error': 'Access Denied'}

        Vote = request.env['poll.vote']

        votes = Vote.search([
            ('poll_id', '=', poll_id),
            ('voter_id', '=', request.env.user.partner_id.id)
        ])
        votes.unlink()

        return poll.get_results()