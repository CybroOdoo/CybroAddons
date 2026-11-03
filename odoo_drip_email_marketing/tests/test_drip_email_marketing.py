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
from datetime import timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.fields import Command
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestDripEmailMarketing(TransactionCase):
    """Test the mail on subscription and the drip mass mailing."""

    @classmethod
    def setUpClass(cls):
        """Create a mail server, drip templates and a drip mailing list."""
        super().setUpClass()
        cls.server = cls.env['ir.mail_server'].create({
            'name': 'Drip Server', 'smtp_host': 'localhost'})
        template = cls.env['drip.template']
        cls.welcome = template.create({
            'name': 'Welcome to the list', 'mail_body': '<p>Welcome</p>'})
        cls.day_one = template.create({
            'name': 'Day one tips', 'mail_body': '<p>Day one</p>'})
        cls.day_two = template.create({
            'name': 'Day two offer', 'mail_body': '<p>Day two</p>'})
        cls.today = fields.Date.context_today(cls.env['mailing.list'])
        cls.mailing_list = cls.env['mailing.list'].create({
            'name': 'Drip List',
            'server_id': cls.server.id,
            'mass_mailing_enable': True,
            'start_date': cls.today - timedelta(days=2),
            'end_date': cls.today + timedelta(days=10),
            'template_ids': [
                Command.create({'name': 'Tips', 'days_after': 1,
                                'template_id': cls.day_one.id}),
                Command.create({'name': 'Offer', 'days_after': 2,
                                'template_id': cls.day_two.id}),
            ],
        })

    def _mails(self, template):
        """Return the mails queued for a drip template."""
        return self.env['mail.mail'].search(
            [('subject', '=', template.name)])

    def _contact(self, name, mailing_lists, **values):
        """Create a contact subscribed to the given lists."""
        return self.env['mailing.contact'].create({
            'name': name, 'email': f'{name.lower()}@example.com',
            'list_ids': [Command.set(mailing_lists.ids)], **values})

    def test_01_list_without_drip(self):
        """A mailing list without drip configuration can be created."""
        mailing_list = self.env['mailing.list'].create({'name': 'Plain'})
        self.assertFalse(mailing_list.template_id)
        self.assertEqual(mailing_list.drip_count, 0)

    def test_02_mail_on_subscription(self):
        """The welcome template of a list is sent to its new contacts only,
        through the server of the list."""
        self.mailing_list.write({
            'mail_contact': True, 'template_id': self.welcome.id})
        other = self.env['mailing.list'].create({
            'name': 'Other', 'mail_contact': True,
            'template_id': self.day_one.id})
        contact = self._contact('Anna', self.mailing_list)
        mail = self._mails(self.welcome)
        self.assertEqual(len(mail), 1)
        self.assertIn(contact.email, mail.email_to)
        self.assertEqual(mail.mail_server_id, self.server)
        self.assertFalse(self._mails(self.day_one),
                         "Lists the contact did not join send nothing")
        contact.list_ids = [Command.link(other.id)]
        self.assertEqual(len(self._mails(self.day_one)), 1,
                         "Joining another list later sends its template")

    def test_02b_mail_on_subscription_other_paths(self):
        """The welcome mail is sent once whichever way the contact joins:
        subscription lines or the contacts of the list."""
        self.mailing_list.write({
            'mail_contact': True, 'template_id': self.welcome.id})
        self.env['mailing.contact'].create({
            'name': 'Gina', 'email': 'gina@example.com',
            'subscription_ids': [Command.create({
                'list_id': self.mailing_list.id})]})
        self.assertEqual(len(self._mails(self.welcome)), 1)
        contact = self._contact('Hugo', self.env['mailing.list'])
        self.mailing_list.contact_ids = [Command.link(contact.id)]
        self.assertEqual(sorted(self._mails(self.welcome).mapped('email_to')), [
            '"Gina" <gina@example.com>', '"Hugo" <hugo@example.com>'])

    def test_03_no_mail_on_subscription_when_opted_out(self):
        """Opted out and blacklisted contacts get no welcome mail."""
        self.mailing_list.write({
            'mail_contact': True, 'template_id': self.welcome.id})
        self.env['mail.blacklist'].create({'email': 'bob@example.com'})
        self._contact('Bob', self.mailing_list)
        contact = self._contact('Carl', self.env['mailing.list'])
        self.env['mailing.subscription'].create({
            'contact_id': contact.id, 'list_id': self.mailing_list.id,
            'opt_out': True})
        self.assertFalse(self._mails(self.welcome))

    def test_04_drip_mass_mailing(self):
        """The drip due today is sent once, one mail per contact, to the
        contacts who did not opt out, and logged in the drip history."""
        anna = self._contact('Anna', self.mailing_list)
        dave = self._contact('Dave', self.mailing_list)
        erin = self._contact('Erin', self.mailing_list)
        erin.subscription_ids.opt_out = True
        self.env['mail.blacklist'].create({'email': 'fred@example.com'})
        self._contact('Fred', self.mailing_list)
        self.env['mailing.list']._action_drip_mass_mailing()
        mails = self._mails(self.day_two)
        self.assertEqual(len(mails), 2)
        self.assertEqual(sorted(mails.mapped('email_to')), [
            '"Anna" <anna@example.com>', '"Dave" <dave@example.com>'])
        self.assertEqual(mails.mail_server_id, self.server)
        self.assertFalse(self._mails(self.day_one),
                         "The drip of yesterday is not sent today")
        self.assertEqual(self.mailing_list.drip_count, 2)
        self.assertEqual(anna.drip_count, 1)
        self.assertEqual(dave.drip_history_ids.template_id, self.day_two)
        self.env['mailing.list']._action_drip_mass_mailing()
        self.assertEqual(len(self._mails(self.day_two)), 2,
                         "Running the scheduled action again sends nothing")

    def test_05_drip_outside_dates(self):
        """No drip is sent after the end date of the list."""
        self._contact('Anna', self.mailing_list)
        self.mailing_list.write({
            'start_date': self.today - timedelta(days=20),
            'end_date': self.today - timedelta(days=18)})
        self.env['mailing.list']._action_drip_mass_mailing()
        self.assertFalse(self.env['drip.mailing.history'].search(
            [('mailing_id', '=', self.mailing_list.id)]))

    def test_06_end_before_start(self):
        """The end date cannot be before the start date."""
        with self.assertRaises(ValidationError):
            self.mailing_list.end_date = self.today - timedelta(days=5)

    def test_07_history_action(self):
        """The smart buttons open the drip history of the list and of the
        contact."""
        contact = self._contact('Anna', self.mailing_list)
        for record, field in ((self.mailing_list, 'mailing_id'),
                              (contact, 'contact_id')):
            action = record.get_drip_history()
            self.assertEqual(action['res_model'], 'drip.mailing.history')
            self.assertEqual(action['domain'], [(field, '=', record.id)])

    def test_08_email_marketing_user(self):
        """An Email Marketing user, without the Settings access, sets up a
        drip list, and its contacts get the welcome and the drip mails."""
        user = new_test_user(
            self.env, login='drip_marketer',
            groups='base.group_user,mass_mailing.group_mass_mailing_user')
        env = self.env(user=user)
        welcome = env['drip.template'].create({
            'name': 'Hello from marketing', 'mail_body': '<p>Hello</p>'})
        drip = env['drip.template'].create({
            'name': 'Marketing drip', 'mail_body': '<p>Drip</p>'})
        mailing_list = env['mailing.list'].create({
            'name': 'Marketing List',
            'server_id': self.server.id,
            'mail_contact': True,
            'template_id': welcome.id,
            'mass_mailing_enable': True,
            'start_date': self.today,
            'end_date': self.today + timedelta(days=5),
            'template_ids': [Command.create({
                'name': 'Same day', 'days_after': 0,
                'template_id': drip.id})],
        })
        contact = env['mailing.contact'].create({
            'name': 'Ivy', 'email': 'ivy@example.com',
            'list_ids': [Command.set(mailing_list.ids)]})
        self.assertEqual(len(self._mails(welcome)), 1)
        self.env['mailing.list']._action_drip_mass_mailing()
        self.assertEqual(len(self._mails(drip)), 1)
        self.assertEqual(mailing_list.drip_count, 1)
        action = contact.get_drip_history()
        history = env[action['res_model']].search(action['domain'])
        self.assertEqual(history.template_id, drip)
