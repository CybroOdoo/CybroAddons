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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import fields, http
from odoo.exceptions import AccessError
from odoo.fields import Domain
from odoo.http import request
from odoo.addons.mail.controllers.messaging_menu import MessagingMenuController
from odoo.addons.mail.controllers.discuss.messaging_menu import DiscussMessagingMenuController


class ChatFavourite(http.Controller):
    """Controller to handle toggling favourite chat channels."""

    @http.route('/enable_favourite', type='jsonrpc', auth='user')
    def enable_favourite(self, **kwargs):
        """Enable favourite status for the specified chat channel."""
        active_id = kwargs.get('active_id')
        user = request.env.user
        user_id = kwargs.get('user_id')
        if user_id and int(user_id) != user.id:
            raise AccessError(self.env._("You cannot alter another user's favourites."))
        if active_id and user.exists():
            channel_id = int(active_id)
            channel = request.env['discuss.channel'].browse(channel_id)
            if channel.exists():
                user.sudo().mail_channel_ids = [fields.Command.link(channel_id)]
                member = channel.channel_member_ids.filtered(
                    lambda m: m.partner_id == user.partner_id
                )
                if member:
                    member.sudo().is_favorite = True
        return active_id

    @http.route('/disable_favourite', type='jsonrpc', auth='user')
    def disable_favourite(self, **kwargs):
        """Disable favourite status for the specified chat channel."""
        active_id = kwargs.get('active_id')
        user = request.env.user
        user_id = kwargs.get('user_id')
        if user_id and int(user_id) != user.id:
            raise AccessError(self.env._("You cannot alter another user's favourites."))
        if active_id and user.exists():
            channel_id = int(active_id)
            channel = request.env['discuss.channel'].browse(channel_id)
            if channel.exists():
                user.sudo().mail_channel_ids = [fields.Command.unlink(channel_id)]
                member = channel.channel_member_ids.filtered(
                    lambda m: m.partner_id == user.partner_id
                )
                if member:
                    member.sudo().is_favorite = False
        return active_id


class FavouriteMessagingMenuController(DiscussMessagingMenuController, MessagingMenuController):
    """Messaging menu controller to support the Favourites tab domain and filtering."""

    def _get_menu_tab_domain(self, tab_id):
        if tab_id == "favourite":
            return Domain([("id", "in", self.env.user.mail_channel_ids.ids)])
        return super()._get_menu_tab_domain(tab_id)

    def _get_menu_tab_filter_domain(self, tab_id, filter_id):
        if tab_id == "favourite" and filter_id == "favourite_unread":
            return Domain("self_member_id.is_unread", "=", True)
        return super()._get_menu_tab_filter_domain(tab_id, filter_id)

    def _get_menu_tab_priority_domain(self, tab_id):
        if tab_id == "favourite":
            return Domain([("id", "in", self.env.user.mail_channel_ids.ids)])
        return super()._get_menu_tab_priority_domain(tab_id)
