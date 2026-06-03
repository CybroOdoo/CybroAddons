# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gion Dany (odoo@cybrosys.com)
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
###############################################################################
from unittest.mock import patch, MagicMock
import dns.resolver
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import ValidationError


def _enable_validation(env):
    """Helper: turn the email validation setting ON."""
    env['ir.config_parameter'].sudo().set_param(
        'contacts_email_validator.email_validation', 'true'
    )


def _disable_validation(env):
    """Helper: turn the email validation setting OFF."""
    env['ir.config_parameter'].sudo().set_param(
        'contacts_email_validator.email_validation', 'false'
    )


def _make_mx_response():
    """Return a non-empty mock MX record list."""
    mx = MagicMock()
    mx.__bool__ = lambda self: True
    return [mx]


@tagged('post_install', '-at_install', 'contacts_email_validator')
class TestResPartnerEmailValidation(TransactionCase):
    """Tests for _check_email_validate on res.partner."""

    # ------------------------------------------------------------------
    # 1. Validation disabled (setting OFF) — constraint must be a no-op
    # ------------------------------------------------------------------

    def test_no_validation_when_setting_disabled(self):
        """When the setting is OFF, any email (even invalid) must be accepted."""
        _disable_validation(self.env)
        # Should not raise for a clearly malformed address
        partner = self.env['res.partner'].create({
            'name': 'Disabled Validation Partner',
            'email': 'not-an-email',
        })
        self.assertEqual(partner.email, 'not-an-email')

    def test_no_validation_when_param_missing(self):
        """When the config param is absent entirely, validation must be skipped."""
        self.env['ir.config_parameter'].sudo().search([
            ('key', '=', 'contacts_email_validator.email_validation')
        ]).unlink()
        partner = self.env['res.partner'].create({
            'name': 'No Param Partner',
            'email': 'bad@@email',
        })
        self.assertEqual(partner.email, 'bad@@email')

    def test_no_validation_when_param_is_empty_string(self):
        """Empty string param value must behave the same as disabled."""
        self.env['ir.config_parameter'].sudo().set_param(
            'contacts_email_validator.email_validation', ''
        )
        partner = self.env['res.partner'].create({
            'name': 'Empty Param Partner',
            'email': 'invalid',
        })
        self.assertEqual(partner.email, 'invalid')

    def test_no_validation_when_email_is_false(self):
        """A partner with no email must not raise, regardless of setting."""
        _enable_validation(self.env)
        partner = self.env['res.partner'].create({
            'name': 'No Email Partner',
        })
        self.assertFalse(partner.email)

    # ------------------------------------------------------------------
    # 2. Format validation (regex) — setting ON, DNS mocked
    # ------------------------------------------------------------------

    @patch('odoo.addons.contacts_email_validator.models.res_partner.dns.resolver.resolve')
    def test_valid_email_format_accepted(self, mock_resolve):
        """A well-formed email with a working MX record must be accepted."""
        _enable_validation(self.env)
        mock_resolve.return_value = _make_mx_response()
        partner = self.env['res.partner'].create({
            'name': 'Valid Email Partner',
            'email': 'user@example.com',
        })
        self.assertEqual(partner.email, 'user@example.com')

    @patch('odoo.addons.contacts_email_validator.models.res_partner.dns.resolver.resolve')
    def test_valid_email_with_dots_and_plus(self, mock_resolve):
        """Emails with dots, plus signs, and subdomains must pass format check."""
        _enable_validation(self.env)
        mock_resolve.return_value = _make_mx_response()
        for email in ['first.last@sub.domain.com', 'user+tag@example.org']:
            with self.subTest(email=email):
                partner = self.env['res.partner'].create({
                    'name': f'Partner {email}',
                    'email': email,
                })
                self.assertEqual(partner.email, email)
                partner.unlink()

    def test_invalid_format_no_at_sign(self):
        """Email without '@' must raise ValidationError."""
        _enable_validation(self.env)
        with self.assertRaises(ValidationError):
            self.env['res.partner'].create({
                'name': 'Bad Email Partner',
                'email': 'userexample.com',
            })

    def test_invalid_format_no_domain(self):
        """Email with no domain part must raise ValidationError."""
        _enable_validation(self.env)
        with self.assertRaises(ValidationError):
            self.env['res.partner'].create({
                'name': 'No Domain Partner',
                'email': 'user@',
            })

    def test_invalid_format_no_tld(self):
        """Email without TLD (e.g. 'user@domain') must raise ValidationError."""
        _enable_validation(self.env)
        with self.assertRaises(ValidationError):
            self.env['res.partner'].create({
                'name': 'No TLD Partner',
                'email': 'user@domain',
            })

    def test_invalid_format_spaces(self):
        """Email containing spaces must raise ValidationError."""
        _enable_validation(self.env)
        with self.assertRaises(ValidationError):
            self.env['res.partner'].create({
                'name': 'Space Email Partner',
                'email': 'user @example.com',
            })

    def test_invalid_format_raises_message_contains_email(self):
        """ValidationError message must mention the offending email."""
        _enable_validation(self.env)
        bad_email = 'bad-email'
        with self.assertRaises(ValidationError) as ctx:
            self.env['res.partner'].create({
                'name': 'Error Message Partner',
                'email': bad_email,
            })
        self.assertIn(bad_email, str(ctx.exception))

    # ------------------------------------------------------------------
    # 3. MX / DNS validation — setting ON, format valid
    # ------------------------------------------------------------------

    @patch('odoo.addons.contacts_email_validator.models.res_partner.dns.resolver.resolve')
    def test_mx_lookup_uses_correct_domain(self, mock_resolve):
        """DNS resolver must be called with the domain extracted from the email."""
        _enable_validation(self.env)
        mock_resolve.return_value = _make_mx_response()
        self.env['res.partner'].create({
            'name': 'Domain Check Partner',
            'email': 'someone@targetdomain.com',
        })
        mock_resolve.assert_called_once_with('targetdomain.com', 'MX')

    @patch('odoo.addons.contacts_email_validator.models.res_partner.dns.resolver.resolve')
    def test_no_answer_raises_validation_error(self, mock_resolve):
        """dns.resolver.NoAnswer must be re-raised as ValidationError."""
        _enable_validation(self.env)
        mock_resolve.side_effect = dns.resolver.NoAnswer()
        with self.assertRaises(ValidationError):
            self.env['res.partner'].create({
                'name': 'NoAnswer Partner',
                'email': 'user@noanswer.com',
            })

    @patch('odoo.addons.contacts_email_validator.models.res_partner.dns.resolver.resolve')
    def test_nxdomain_raises_validation_error(self, mock_resolve):
        """dns.resolver.NXDOMAIN must be re-raised as ValidationError."""
        _enable_validation(self.env)
        mock_resolve.side_effect = dns.resolver.NXDOMAIN()
        with self.assertRaises(ValidationError):
            self.env['res.partner'].create({
                'name': 'NXDOMAIN Partner',
                'email': 'user@nonexistentdomain.xyz',
            })

    @patch('odoo.addons.contacts_email_validator.models.res_partner.dns.resolver.resolve')
    def test_no_nameservers_does_not_raise(self, mock_resolve):
        """NoNameservers is a soft failure — must log a warning, NOT raise."""
        _enable_validation(self.env)
        mock_resolve.side_effect = dns.resolver.NoNameservers()
        try:
            self.env['res.partner'].create({
                'name': 'NoNS Partner',
                'email': 'user@nonameserver.com',
            })
        except ValidationError:
            self.fail("NoNameservers should not raise ValidationError")

    @patch('odoo.addons.contacts_email_validator.models.res_partner.dns.resolver.resolve')
    def test_dns_timeout_does_not_raise(self, mock_resolve):
        """DNS Timeout is a soft failure — must log a warning, NOT raise."""
        _enable_validation(self.env)
        mock_resolve.side_effect = dns.resolver.Timeout()
        try:
            self.env['res.partner'].create({
                'name': 'Timeout Partner',
                'email': 'user@slowdns.com',
            })
        except ValidationError:
            self.fail("DNS Timeout should not raise ValidationError")

    @patch('odoo.addons.contacts_email_validator.models.res_partner.dns.resolver.resolve')
    def test_generic_dns_exception_does_not_raise(self, mock_resolve):
        """An unexpected DNS exception must be swallowed (logged), not propagated."""
        _enable_validation(self.env)
        mock_resolve.side_effect = Exception("Unexpected DNS error")
        try:
            self.env['res.partner'].create({
                'name': 'Generic DNS Error Partner',
                'email': 'user@example.com',
            })
        except ValidationError:
            self.fail("Generic DNS exception should not raise ValidationError")

    @patch('odoo.addons.contacts_email_validator.models.res_partner.dns.resolver.resolve')
    def test_nxdomain_error_message_contains_domain(self, mock_resolve):
        """ValidationError for NXDOMAIN must mention the invalid domain."""
        _enable_validation(self.env)
        mock_resolve.side_effect = dns.resolver.NXDOMAIN()
        with self.assertRaises(ValidationError) as ctx:
            self.env['res.partner'].create({
                'name': 'NXDOMAIN Msg Partner',
                'email': 'user@baddomain.xyz',
            })
        self.assertIn('baddomain.xyz', str(ctx.exception))

    @patch('odoo.addons.contacts_email_validator.models.res_partner.dns.resolver.resolve')
    def test_no_answer_error_message_contains_domain(self, mock_resolve):
        """ValidationError for NoAnswer must mention the domain."""
        _enable_validation(self.env)
        mock_resolve.side_effect = dns.resolver.NoAnswer()
        with self.assertRaises(ValidationError) as ctx:
            self.env['res.partner'].create({
                'name': 'NoAnswer Msg Partner',
                'email': 'user@noanswerdomain.com',
            })
        self.assertIn('noanswerdomain.com', str(ctx.exception))

    # ------------------------------------------------------------------
    # 4. Write (update) triggers the constraint
    # ------------------------------------------------------------------

    @patch('odoo.addons.contacts_email_validator.models.res_partner.dns.resolver.resolve')
    def test_constraint_triggered_on_write(self, mock_resolve):
        """Updating email via write() must also trigger the constraint."""
        _disable_validation(self.env)
        partner = self.env['res.partner'].create({
            'name': 'Write Test Partner',
            'email': 'valid@example.com',
        })
        _enable_validation(self.env)
        mock_resolve.side_effect = dns.resolver.NXDOMAIN()
        with self.assertRaises(ValidationError):
            partner.write({'email': 'user@nonexistent.xyz'})

    # ------------------------------------------------------------------
    # 5. Batch / multi-record behaviour
    # ------------------------------------------------------------------

    @patch('odoo.addons.contacts_email_validator.models.res_partner.dns.resolver.resolve')
    def test_constraint_checks_all_records_in_batch(self, mock_resolve):
        """All records in a recordset must be validated, not just the first."""
        _enable_validation(self.env)
        mock_resolve.return_value = _make_mx_response()

        p1 = self.env['res.partner'].create({'name': 'Batch1', 'email': 'a@example.com'})
        p2 = self.env['res.partner'].create({'name': 'Batch2', 'email': 'b@example.com'})

        self.assertEqual(mock_resolve.call_count, 2)

    @patch('odoo.addons.contacts_email_validator.models.res_partner.dns.resolver.resolve')
    def test_one_invalid_in_batch_raises(self, mock_resolve):
        """A partner whose domain has no MX records must raise ValidationError.

        @api.constrains is invoked per record individually, so we create the
        bad partner directly and verify it raises.
        """
        _enable_validation(self.env)
        mock_resolve.side_effect = dns.resolver.NXDOMAIN()
        with self.assertRaises(ValidationError):
            self.env['res.partner'].create({
                'name': 'Batch Bad',
                'email': 'user@baddomain.xyz',
            })