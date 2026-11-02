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
from unittest.mock import MagicMock, PropertyMock, patch

from odoo import fields
from odoo.exceptions import AccessError
from odoo.fields import Domain
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user
from odoo.addons.chat_favourites_in_systray.controllers import (
    chat_favourites_in_systray as ctrl_module,
)
from odoo.addons.chat_favourites_in_systray.controllers.chat_favourites_in_systray import (
    ChatFavourite,
    FavouriteMessagingMenuController,
)

CONTROLLER_PATH = (
    'odoo.addons.chat_favourites_in_systray.controllers'
    '.chat_favourites_in_systray'
)


@tagged('post_install', '-at_install')
class TestChatFavouritesControllers(TransactionCase):
    """Test suite covering ChatFavourite and FavouriteMessagingMenuController."""

    @classmethod
    def setUpClass(cls):
        """Set up test users and channels for controller tests."""
        super().setUpClass()
        cls.test_user = new_test_user(
            cls.env,
            login='favourite_user_1',
            name='Favourite User 1',
            groups='base.group_user',
        )
        cls.test_user_2 = new_test_user(
            cls.env,
            login='favourite_user_2',
            name='Favourite User 2',
            groups='base.group_user',
        )
        cls.channel_1 = cls.env['discuss.channel'].create({
            'name': 'General Discussion Channel 1',
            'channel_type': 'channel',
            'channel_member_ids': [
                fields.Command.create({'partner_id': cls.test_user.partner_id.id}),
            ],
        })

        cls.channel_2 = cls.env['discuss.channel'].create({
            'name': 'Project Sync Channel 2',
            'channel_type': 'channel',
            'channel_member_ids': [
                fields.Command.create({'partner_id': cls.test_user.partner_id.id}),
                fields.Command.create({'partner_id': cls.test_user_2.partner_id.id}),
            ],
        })

        cls.channel_3 = cls.env['discuss.channel'].create({
            'name': 'External Channel 3',
            'channel_type': 'channel',
        })
        cls.controller = ChatFavourite()
        cls.menu_controller = FavouriteMessagingMenuController()

    def setUp(self):
        """Set up per-test environment and bind ChatFavourite.env to active request."""
        super().setUp()
        patch_prop = PropertyMock(
            side_effect=lambda: ctrl_module.request.env if ctrl_module.request else self.env(user=self.test_user)
        )
        patcher = patch.object(ChatFavourite, 'env', new_callable=lambda: patch_prop)
        patcher.start()
        self.addCleanup(patcher.stop)

    # -------------------------------------------------------------------------
    # ChatFavourite Controller Tests
    # -------------------------------------------------------------------------

    def test_enable_favourite_current_user(self):
        """Test enabling favourite for logged in user adds channel to favourites."""
        mock_req = MagicMock()
        mock_req.env = self.env(user=self.test_user)

        with patch(f'{CONTROLLER_PATH}.request', mock_req):
            # Test without specifying user_id (uses current user)
            response = self.controller.enable_favourite(active_id=self.channel_1.id)
            self.assertEqual(response, self.channel_1.id)

            self.assertIn(
                self.channel_1,
                self.test_user.mail_channel_ids,
                "Channel 1 should be linked to test_user.mail_channel_ids.",
            )
            member = self.channel_1.channel_member_ids.filtered(
                lambda m: m.partner_id == self.test_user.partner_id
            )
            self.assertTrue(member, "Channel member record should exist.")
            self.assertTrue(member.is_favorite, "Member is_favorite should be True.")

            # Test with explicit user_id matching current user
            response2 = self.controller.enable_favourite(
                active_id=self.channel_2.id,
                user_id=self.test_user.id,
            )
            self.assertEqual(response2, self.channel_2.id)
            self.assertIn(self.channel_2, self.test_user.mail_channel_ids)

    def test_enable_favourite_string_active_id_and_user_id(self):
        """Test enable_favourite accepts string representations of IDs."""
        mock_req = MagicMock()
        mock_req.env = self.env(user=self.test_user)

        with patch(f'{CONTROLLER_PATH}.request', mock_req):
            response = self.controller.enable_favourite(
                active_id=str(self.channel_1.id),
                user_id=str(self.test_user.id),
            )
            self.assertEqual(response, str(self.channel_1.id))
            self.assertIn(self.channel_1, self.test_user.mail_channel_ids)

    def test_enable_favourite_cross_user_denied(self):
        """Test enabling favourite specifying another user's id is blocked with AccessError."""
        mock_req = MagicMock()
        mock_req.env = self.env(user=self.test_user)

        with patch(f'{CONTROLLER_PATH}.request', mock_req):
            with self.assertRaises(AccessError):
                self.controller.enable_favourite(
                    active_id=self.channel_2.id,
                    user_id=self.test_user_2.id,
                )

            self.assertNotIn(
                self.channel_2,
                self.test_user_2.mail_channel_ids,
                "Channel 2 should not be linked to test_user_2 by another user.",
            )

    def test_enable_favourite_user_not_member(self):
        """Test enabling favourite when user is not a member of the channel."""
        mock_req = MagicMock()
        mock_req.env = self.env(user=self.test_user)

        with patch(f'{CONTROLLER_PATH}.request', mock_req):
            response = self.controller.enable_favourite(active_id=self.channel_3.id)
            self.assertEqual(response, self.channel_3.id)
            self.assertIn(
                self.channel_3,
                self.test_user.mail_channel_ids,
                "Channel 3 should still be added to user's mail_channel_ids without member error.",
            )

    def test_enable_favourite_channel_not_exists(self):
        """Test enable_favourite with a non-existent channel ID handles gracefully."""
        mock_req = MagicMock()
        mock_req.env = self.env(user=self.test_user)

        with patch(f'{CONTROLLER_PATH}.request', mock_req):
            non_existent_channel_id = 99999999
            response = self.controller.enable_favourite(active_id=non_existent_channel_id)
            self.assertEqual(response, non_existent_channel_id)

    def test_enable_favourite_idempotent(self):
        """Test enabling an already favourite channel preserves status idempotently."""
        mock_req = MagicMock()
        mock_req.env = self.env(user=self.test_user)

        with patch(f'{CONTROLLER_PATH}.request', mock_req):
            self.controller.enable_favourite(active_id=self.channel_1.id)
            count_before = len(self.test_user.mail_channel_ids)

            # Enable again
            self.controller.enable_favourite(active_id=self.channel_1.id)
            count_after = len(self.test_user.mail_channel_ids)

            self.assertEqual(count_before, count_after)
            self.assertIn(self.channel_1, self.test_user.mail_channel_ids)

    def test_enable_favourite_invalid_and_missing_inputs(self):
        """Test enable_favourite with non-matching user or missing/falsy active_id."""
        mock_req = MagicMock()
        mock_req.env = self.env(user=self.test_user)

        with patch(f'{CONTROLLER_PATH}.request', mock_req):
            # Missing active_id
            response_none = self.controller.enable_favourite()
            self.assertIsNone(response_none)

            # Falsy active_id
            response_false = self.controller.enable_favourite(active_id=False)
            self.assertFalse(response_false)

            # Cross-user / invalid user ID raises AccessError
            with self.assertRaises(AccessError):
                self.controller.enable_favourite(
                    active_id=self.channel_1.id,
                    user_id=99999999,
                )

    def test_disable_favourite_current_user(self):
        """Test disabling favourite removes channel from favourites."""
        self.test_user.write({
            'mail_channel_ids': [
                fields.Command.link(self.channel_1.id),
                fields.Command.link(self.channel_2.id),
            ],
        })
        member = self.channel_1.channel_member_ids.filtered(
            lambda m: m.partner_id == self.test_user.partner_id
        )
        member.sudo().is_favorite = True

        mock_req = MagicMock()
        mock_req.env = self.env(user=self.test_user)

        with patch(f'{CONTROLLER_PATH}.request', mock_req):
            # Test without specifying user_id
            response = self.controller.disable_favourite(active_id=self.channel_1.id)
            self.assertEqual(response, self.channel_1.id)

            self.assertNotIn(
                self.channel_1,
                self.test_user.mail_channel_ids,
                "Channel 1 should be unlinked from test_user.mail_channel_ids.",
            )
            self.assertFalse(member.is_favorite, "Member is_favorite should be False.")

            # Test with explicit user_id matching current user
            response2 = self.controller.disable_favourite(
                active_id=self.channel_2.id,
                user_id=self.test_user.id,
            )
            self.assertEqual(response2, self.channel_2.id)
            self.assertNotIn(self.channel_2, self.test_user.mail_channel_ids)

    def test_disable_favourite_string_active_id_and_user_id(self):
        """Test disable_favourite accepts string representations of IDs."""
        self.test_user.write({
            'mail_channel_ids': [fields.Command.link(self.channel_1.id)],
        })
        mock_req = MagicMock()
        mock_req.env = self.env(user=self.test_user)

        with patch(f'{CONTROLLER_PATH}.request', mock_req):
            response = self.controller.disable_favourite(
                active_id=str(self.channel_1.id),
                user_id=str(self.test_user.id),
            )
            self.assertEqual(response, str(self.channel_1.id))
            self.assertNotIn(self.channel_1, self.test_user.mail_channel_ids)

    def test_disable_favourite_cross_user_denied(self):
        """Test disabling favourite specifying another user's id is blocked with AccessError."""
        self.test_user_2.write({
            'mail_channel_ids': [fields.Command.link(self.channel_2.id)],
        })
        member = self.channel_2.channel_member_ids.filtered(
            lambda m: m.partner_id == self.test_user_2.partner_id
        )
        member.sudo().is_favorite = True

        mock_req = MagicMock()
        mock_req.env = self.env(user=self.test_user)

        with patch(f'{CONTROLLER_PATH}.request', mock_req):
            with self.assertRaises(AccessError):
                self.controller.disable_favourite(
                    active_id=self.channel_2.id,
                    user_id=self.test_user_2.id,
                )

            self.assertIn(
                self.channel_2,
                self.test_user_2.mail_channel_ids,
                "Channel 2 should remain in test_user_2.mail_channel_ids.",
            )
            self.assertTrue(member.is_favorite, "Member is_favorite should remain True for user 2.")

    def test_disable_favourite_user_not_member(self):
        """Test disabling favourite when user is not a member of the channel."""
        self.test_user.write({
            'mail_channel_ids': [fields.Command.link(self.channel_3.id)],
        })
        mock_req = MagicMock()
        mock_req.env = self.env(user=self.test_user)

        with patch(f'{CONTROLLER_PATH}.request', mock_req):
            response = self.controller.disable_favourite(active_id=self.channel_3.id)
            self.assertEqual(response, self.channel_3.id)
            self.assertNotIn(
                self.channel_3,
                self.test_user.mail_channel_ids,
                "Channel 3 should be unlinked from mail_channel_ids without error.",
            )

    def test_disable_favourite_channel_not_exists(self):
        """Test disable_favourite with non-existent channel ID handles safely."""
        mock_req = MagicMock()
        mock_req.env = self.env(user=self.test_user)

        with patch(f'{CONTROLLER_PATH}.request', mock_req):
            non_existent_channel_id = 99999999
            response = self.controller.disable_favourite(active_id=non_existent_channel_id)
            self.assertEqual(response, non_existent_channel_id)

    def test_disable_favourite_not_in_favourites(self):
        """Test disabling favourite for a channel that is not in user favourites."""
        self.test_user.mail_channel_ids = [fields.Command.clear()]
        mock_req = MagicMock()
        mock_req.env = self.env(user=self.test_user)

        with patch(f'{CONTROLLER_PATH}.request', mock_req):
            response = self.controller.disable_favourite(active_id=self.channel_1.id)
            self.assertEqual(response, self.channel_1.id)
            self.assertNotIn(self.channel_1, self.test_user.mail_channel_ids)

    def test_disable_favourite_invalid_and_missing_inputs(self):
        """Test disable_favourite with non-matching user or missing/falsy active_id."""
        mock_req = MagicMock()
        mock_req.env = self.env(user=self.test_user)

        with patch(f'{CONTROLLER_PATH}.request', mock_req):
            # Missing active_id
            response_none = self.controller.disable_favourite()
            self.assertIsNone(response_none)

            # Falsy active_id
            response_false = self.controller.disable_favourite(active_id=False)
            self.assertFalse(response_false)

            # Cross-user / invalid user ID raises AccessError
            with self.assertRaises(AccessError):
                self.controller.disable_favourite(
                    active_id=self.channel_1.id,
                    user_id=99999999,
                )

    # -------------------------------------------------------------------------
    # FavouriteMessagingMenuController Unit Tests
    # -------------------------------------------------------------------------

    def test_get_menu_tab_domain(self):
        """Test _get_menu_tab_domain for 'favourite' and other tabs."""
        patch_prop = PropertyMock(return_value=self.env(user=self.test_user))
        with patch.object(FavouriteMessagingMenuController, 'env', new_callable=lambda: patch_prop):
            # When user has no favourites
            self.test_user.mail_channel_ids = [fields.Command.clear()]
            favourite_domain = self.menu_controller._get_menu_tab_domain("favourite")
            self.assertEqual(
                favourite_domain,
                Domain([("id", "in", [])]),
                "Should return domain with empty ids when user has no favourite channels.",
            )

            # When user has favourites
            self.test_user.mail_channel_ids = [
                fields.Command.link(self.channel_1.id),
                fields.Command.link(self.channel_2.id),
            ]
            favourite_domain = self.menu_controller._get_menu_tab_domain("favourite")
            self.assertEqual(
                favourite_domain,
                Domain([("id", "in", self.test_user.mail_channel_ids.ids)]),
                "Should return domain restricting ids to user.mail_channel_ids.",
            )

            # Tab not 'favourite' (e.g. 'chat', 'channel', 'meeting', 'notification') should delegate to super
            chat_domain = self.menu_controller._get_menu_tab_domain("chat")
            self.assertEqual(
                chat_domain,
                Domain([
                    ("channel_type", "in", ["chat", "group"]),
                    ("default_display_mode", "!=", "video_full_screen"),
                    ("self_member_id.is_pinned", "=", True),
                ]),
                "Tab 'chat' should delegate to super and return chat domain.",
            )

            channel_domain = self.menu_controller._get_menu_tab_domain("channel")
            self.assertTrue(channel_domain)

            meeting_domain = self.menu_controller._get_menu_tab_domain("meeting")
            self.assertTrue(meeting_domain)

            notification_domain = self.menu_controller._get_menu_tab_domain("notification")
            self.assertTrue(notification_domain)

            # Unknown tab should delegate to super
            unknown_domain = self.menu_controller._get_menu_tab_domain("unknown_tab")
            self.assertIsNotNone(unknown_domain)

    def test_get_menu_tab_filter_domain(self):
        """Test _get_menu_tab_filter_domain for favourite tab and other tab/filter combinations."""
        patch_prop = PropertyMock(return_value=self.env(user=self.test_user))
        with patch.object(FavouriteMessagingMenuController, 'env', new_callable=lambda: patch_prop):
            # When tab is 'favourite' and filter is 'favourite_unread'
            unread_domain = self.menu_controller._get_menu_tab_filter_domain(
                "favourite", "favourite_unread"
            )
            self.assertEqual(
                unread_domain,
                Domain("self_member_id.is_unread", "=", True),
                "Should return domain matching unread self_member_id.",
            )

            # When tab is 'favourite' but filter is NOT 'favourite_unread' (delegates to super)
            fallback_fav_domain = self.menu_controller._get_menu_tab_filter_domain(
                "favourite", "other_filter"
            )
            self.assertEqual(
                fallback_fav_domain,
                Domain.FALSE,
                "Tab 'favourite' with unknown filter should fall through to super.",
            )

            # When tab is 'chat' and filter is 'chat_unread'
            chat_unread_domain = self.menu_controller._get_menu_tab_filter_domain(
                "chat", "chat_unread"
            )
            self.assertEqual(
                chat_unread_domain,
                Domain("self_member_id.is_unread", "=", True),
                "Tab 'chat' filter 'chat_unread' should delegate to super.",
            )

            # When tab is 'chat' and filter is 'chat_group'
            chat_group_domain = self.menu_controller._get_menu_tab_filter_domain(
                "chat", "chat_group"
            )
            self.assertEqual(
                chat_group_domain,
                Domain("channel_type", "=", "group"),
                "Tab 'chat' filter 'chat_group' should delegate to super.",
            )

            # When tab is 'channel' and filter is 'channel_unread'
            channel_unread_domain = self.menu_controller._get_menu_tab_filter_domain(
                "channel", "channel_unread"
            )
            self.assertEqual(
                channel_unread_domain,
                Domain("self_member_id.is_unread", "=", True),
                "Tab 'channel' filter 'channel_unread' should delegate to super.",
            )

            # When tab is 'channel' and filter is 'channel_thread'
            channel_thread_domain = self.menu_controller._get_menu_tab_filter_domain(
                "channel", "channel_thread"
            )
            self.assertEqual(
                channel_thread_domain,
                Domain("parent_channel_id", "!=", False),
                "Tab 'channel' filter 'channel_thread' should delegate to super.",
            )

            # When tab is 'meeting' and filter is 'meeting_unread'
            meeting_unread_domain = self.menu_controller._get_menu_tab_filter_domain(
                "meeting", "meeting_unread"
            )
            self.assertEqual(
                meeting_unread_domain,
                Domain("self_member_id.is_unread", "=", True),
                "Tab 'meeting' filter 'meeting_unread' should delegate to super.",
            )

            # When tab is 'meeting' and filter is 'meeting_thread'
            meeting_thread_domain = self.menu_controller._get_menu_tab_filter_domain(
                "meeting", "meeting_thread"
            )
            self.assertEqual(
                meeting_thread_domain,
                Domain("parent_channel_id", "!=", False),
                "Tab 'meeting' filter 'meeting_thread' should delegate to super.",
            )

    def test_get_menu_tab_priority_domain(self):
        """Test _get_menu_tab_priority_domain for 'favourite' tab and other tabs."""
        patch_prop = PropertyMock(return_value=self.env(user=self.test_user))
        with patch.object(FavouriteMessagingMenuController, 'env', new_callable=lambda: patch_prop):
            # When tab is 'favourite' with favourites
            self.test_user.mail_channel_ids = [fields.Command.link(self.channel_1.id)]
            priority_domain = self.menu_controller._get_menu_tab_priority_domain("favourite")
            self.assertEqual(
                priority_domain,
                Domain([("id", "in", self.test_user.mail_channel_ids.ids)]),
                "Should return domain restricting ids to user.mail_channel_ids.",
            )

            # When tab is 'favourite' with empty favourites
            self.test_user.mail_channel_ids = [fields.Command.clear()]
            empty_priority_domain = self.menu_controller._get_menu_tab_priority_domain("favourite")
            self.assertEqual(
                empty_priority_domain,
                Domain([("id", "in", [])]),
                "Should return domain restricting ids to empty list when no favourites exist.",
            )

            # When tab is 'meeting'
            meeting_priority_domain = self.menu_controller._get_menu_tab_priority_domain("meeting")
            self.assertEqual(
                meeting_priority_domain,
                self.env["discuss.channel"]._get_meeting_ongoing_domain(),
                "Meeting tab should delegate to super priority domain.",
            )

            # When tab is other tab with no priority domain (e.g. 'chat', 'channel', 'custom')
            chat_priority_domain = self.menu_controller._get_menu_tab_priority_domain("chat")
            self.assertIsNone(
                chat_priority_domain,
                "Other tabs without priority domain should return None from super.",
            )

            channel_priority_domain = self.menu_controller._get_menu_tab_priority_domain("channel")
            self.assertIsNone(
                channel_priority_domain,
                "Channel tab without priority domain should return None from super.",
            )
