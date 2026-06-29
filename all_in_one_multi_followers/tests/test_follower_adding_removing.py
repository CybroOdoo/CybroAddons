# -*- coding: utf-8 -*-
from unittest.mock import patch
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestFollowerAddingRemoving(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create two test partners - one will be the follower
        cls.partner_a = cls.env['res.partner'].create({'name': 'Follower Partner A',
                                                       'email': 'a@test.com'})
        cls.partner_b = cls.env['res.partner'].create({'name': 'Follower Partner B',
                                                       'email': 'b@test.com'})
        # Use res.partner as the target model (it inherits mail.thread)
        cls.target_record = cls.env['res.partner'].create({'name': 'Target Record'})

    def _make_wizard(self, action_type='add', send_mail=False):
        """Helper: create a wizard with context pointing at target_record."""
        return self.env['follower.adding.removing'].with_context(
            active_model='res.partner',
            active_ids=[self.target_record.id],
        ).create({
            'type': action_type,
            'partner_ids': [(6, 0, [self.partner_a.id, self.partner_b.id])],
            'send_mail': send_mail,
            'message': '',
        })

    # -------------------------------------------------------------------------
    # action_submit: add followers
    # -------------------------------------------------------------------------

    def test_action_submit_add_followers(self):
        """Test that action_submit with type='add' subscribes partners."""
        wizard = self._make_wizard(action_type='add')
        wizard.action_submit()

        followers = self.target_record.message_follower_ids.mapped('partner_id')
        self.assertIn(self.partner_a, followers,
                      "Partner A should be subscribed after add action.")
        self.assertIn(self.partner_b, followers,
                      "Partner B should be subscribed after add action.")

    # -------------------------------------------------------------------------
    # action_submit: remove followers
    # -------------------------------------------------------------------------

    def test_action_submit_remove_followers(self):
        """Test that action_submit with type='remove' unsubscribes partners."""
        # First, subscribe them
        self.target_record.message_subscribe(
            partner_ids=[self.partner_a.id, self.partner_b.id])

        wizard = self._make_wizard(action_type='remove')
        wizard.action_submit()

        followers = self.target_record.message_follower_ids.mapped('partner_id')
        self.assertNotIn(self.partner_a, followers,
                         "Partner A should be unsubscribed after remove action.")
        self.assertNotIn(self.partner_b, followers,
                         "Partner B should be unsubscribed after remove action.")

    # -------------------------------------------------------------------------
    # action_submit: send_mail path
    # -------------------------------------------------------------------------

    def test_action_submit_sends_mail_when_flagged(self):
        """Test that a mail.mail record is created when send_mail=True and message is set."""
        wizard = self._make_wizard(action_type='add', send_mail=True)
        wizard.message = '<div><p>Hello,</p><p>You are added.</p></div>'

        mail_count_before = self.env['mail.mail'].search_count([])
        with patch.object(type(self.env['mail.mail']), 'send', return_value=None):
            wizard.action_submit()
        mail_count_after = self.env['mail.mail'].search_count([])

        self.assertGreater(mail_count_after, mail_count_before,
                           "A mail.mail record should be created when send_mail is True.")

    # -------------------------------------------------------------------------
    # _onchange_type
    # -------------------------------------------------------------------------

    def test_onchange_type_add_sets_message(self):
        """Test _onchange_type sets message correctly for 'add' type."""
        wizard = self.env['follower.adding.removing'].with_context(
            active_model='res.partner',
            active_ids=[self.target_record.id],
        ).new({'type': 'add'})
        wizard._onchange_type()
        self.assertTrue(wizard.message, "Message should be set after onchange.")
        self.assertIn('invited', wizard.message,
                      "Message should mention 'invited' for add type.")

    def test_onchange_type_remove_sets_message(self):
        """Test _onchange_type sets message correctly for 'remove' type."""
        wizard = self.env['follower.adding.removing'].with_context(
            active_model='res.partner',
            active_ids=[self.target_record.id],
        ).new({'type': 'remove'})
        wizard._onchange_type()
        self.assertTrue(wizard.message, "Message should be set after onchange.")
        self.assertIn('removed', wizard.message,
                      "Message should mention 'removed' for remove type.")

    # -------------------------------------------------------------------------
    # _prepare_message_values
    # -------------------------------------------------------------------------

    def test_prepare_message_values_structure(self):
        """Test _prepare_message_values returns a well-formed dict."""
        wizard = self._make_wizard(action_type='add')
        wizard.message = '<div><p>Hello</p></div>'
        values = wizard._prepare_message_values(
            title=['Target Record'],
            model_name='Contact',
            email_from='admin@test.com',
            new_partners=self.partner_a | self.partner_b,
        )

        self.assertIn('subject', values)
        self.assertIn('body_html', values)
        self.assertIn('email_from', values)
        self.assertIn('email_to', values)
        self.assertEqual(values['email_from'], 'admin@test.com')
        self.assertIn('a@test.com', values['email_to'])
        self.assertIn('b@test.com', values['email_to'])
        self.assertTrue(values['reply_to_force_new'])
        self.assertTrue(values['email_add_signature'])
