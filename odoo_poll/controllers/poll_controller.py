# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import _, http
from odoo.http import request


class PollController(http.Controller):
    """Controller for poll RPC endpoints"""

    @http.route('/discuss/poll/create', type='jsonrpc', auth='user')
    def create_poll(self, thread_id, thread_model, question, options,
                    is_multiple_choice=False, company_id=None):
        """Create a new poll in a discuss thread"""
        Poll = request.env['discuss.poll']
        PollOption = request.env['poll.option']

        # Determine target company securely
        if company_id and company_id in request.env.companies.ids:
            target_company_id = company_id
        else:
            target_company_id = request.env.company.id

        poll = Poll.create({
            'question': question,
            'is_multiple_choice': is_multiple_choice,
            'company_id': target_company_id,
        })

        for idx, option_text in enumerate(options):
            if option_text and option_text.strip():
                PollOption.create({
                    'name': option_text.strip(),
                    'poll_id': poll.id,
                    'sequence': idx + 1,
                })

        thread = request.env[thread_model].browse(thread_id)
        message = thread.message_post(
            body=(
                f'<div class="o_poll_message_container" '
                f'data-poll-id="{poll.id}"></div>'
            ),
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
        )

        poll.write({'message_id': message.id})
        message.sudo().write({'poll_id': poll.id})

        return {
            'poll_id': poll.id,
            'message_id': message.id,
            'poll_data': poll.get_results(),
        }

    @http.route('/discuss/poll/vote', type='jsonrpc', auth='user')
    def vote(self, poll_id, option_ids, **kwargs):
        """Submit vote(s) for a poll"""
        if kwargs.get('context'):
            request.update_context(**kwargs.get('context'))

        poll = request.env['discuss.poll'].browse(poll_id)
        if not poll.exists():
            return {'error': _('Poll not found')}

        if poll.company_id and poll.company_id not in request.env.companies:
            return {'error': _('Access Denied')}

        if poll.is_closed:
            return {'error': _('Poll is closed')}

        # Verify that all option_ids belong to this poll
        valid_options = poll.option_ids.filtered(lambda o: o.id in option_ids)
        if len(valid_options) != len(option_ids):
            return {'error': _('Invalid option selected')}

        Vote = request.env['poll.vote']
        partner_id = request.env.user.partner_id.id

        existing_votes = Vote.search([
            ('poll_id', '=', poll.id),
            ('voter_id', '=', partner_id),
        ])
        existing_option_ids = set(existing_votes.mapped('option_id.id'))
        target_option_ids = set(valid_options.ids)

        # Remove votes that are no longer selected
        to_remove = existing_votes.filtered(
            lambda v: v.option_id.id not in target_option_ids
        )
        to_remove.unlink()

        # Create votes for newly selected options only
        to_add = target_option_ids - existing_option_ids
        for option_id in to_add:
            Vote.create({
                'poll_id': poll.id,
                'option_id': option_id,
                'voter_id': partner_id,
            })

        return poll.get_results()

    @http.route('/discuss/poll/results', type='jsonrpc', auth='user')
    def get_results(self, poll_id, **kwargs):
        """Get poll results"""
        if kwargs.get('context'):
            request.update_context(**kwargs.get('context'))

        poll = request.env['discuss.poll'].browse(poll_id)
        if not poll.exists():
            return {'error': _('Poll not found')}

        if poll.company_id and poll.company_id not in request.env.companies:
            return {'error': _('Access Denied')}

        return poll.get_results()

    @http.route('/discuss/poll/close', type='jsonrpc', auth='user')
    def close_poll(self, poll_id, **kwargs):
        """Close a poll (only author or manager can close)"""
        if kwargs.get('context'):
            request.update_context(**kwargs.get('context'))

        poll = request.env['discuss.poll'].browse(poll_id)
        if not poll.exists():
            return {'error': _('Poll not found')}

        if poll.company_id and poll.company_id not in request.env.companies:
            return {'error': _('Access Denied')}

        is_author = (poll.author_id == request.env.user.partner_id)
        is_manager = (
            request.env.user.has_group('odoo_poll.group_odoo_poll_manager')
            or request.env.user._is_admin()
        )

        if not (is_author or is_manager):
            return {'error': _('Only poll author or manager can close the poll')}

        poll.action_close()
        return {'success': True, 'poll_data': poll.get_results()}

    @http.route('/discuss/poll/remove_votes', type='jsonrpc', auth='user')
    def remove_votes(self, poll_id, **kwargs):
        """Remove current user's votes from poll"""
        if kwargs.get('context'):
            request.update_context(**kwargs.get('context'))

        poll = request.env['discuss.poll'].browse(poll_id)
        if not poll.exists():
            return {'error': _('Poll not found')}

        if poll.company_id and poll.company_id not in request.env.companies:
            return {'error': _('Access Denied')}

        if poll.is_closed:
            return {'error': _('Poll is closed')}

        Vote = request.env['poll.vote']
        votes = Vote.search([
            ('poll_id', '=', poll.id),
            ('voter_id', '=', request.env.user.partner_id.id),
        ])
        votes.unlink()

        return poll.get_results()