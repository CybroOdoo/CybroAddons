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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import logging
from datetime import datetime
from json import JSONDecodeError

import requests

from odoo import _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Registered by each odoo/addons/l10n_om_edi/lib/connectors/<vendor>.py module via @register_connector.
# Keyed by the same string used in res.company.l10n_om_edi_asp_provider's Selection value.
CONNECTOR_REGISTRY = {}

CONFIG_STATUS_SELECTION = [
    ('confirmed', "Confirmed from vendor documentation"),
    ('partial', "Partially confirmed - some details unverified"),
    ('unconfirmed', "Unknown / To Be Confirmed"),
]

# The Oman Tax Authority's own published list of Accredited Service Providers - the source of truth
# for "is this vendor legally usable for Oman e-invoicing at all", independent of CONFIG_STATUS above
# (which only tracks how well the API happens to be documented).
OTA_ACCREDITED_LIST_URL = "https://fawtara.taxoman.gov.om/accredited-service-providers"


def register_connector(provider_code):
    """ Class decorator registering a connector implementation for a given ASP provider code. """
    def decorator(cls):
        """ Register `cls` under `provider_code` and return it unchanged. """
        CONNECTOR_REGISTRY[provider_code] = cls
        return cls
    return decorator


class L10nOmEdiConnector:
    """ Abstract base class for an Oman e-invoicing Accredited Service Provider (ASP) connector.

    Oman's "Fawtara" e-invoicing program requires businesses to route through one of several
    OTA-accredited service providers (there is no direct network connection, and no Odoo-hosted
    access point for Oman). Each accredited provider exposes its own API; a concrete subclass
    implements the methods below against one specific vendor's API.

    None of the concrete subclasses shipped in this module are backed by a real, confirmed API
    integration at the time of writing - they exist so the l10n.om.edi.document state machine and
    UI have a stable interface to call, and so that wiring in a real provider later is a small,
    isolated change (implement the 3 methods below for that vendor) rather than a redesign.
    """

    # Human-readable vendor name, overridden by each subclass.
    display_name = "Unconfigured"

    # Whether this provider is on the OTA's own published accredited-provider list (see
    # OTA_ACCREDITED_LIST_URL) - independent of how well-documented its API is.
    OTA_ACCREDITED = False

    # Generic credential "slots" (see the Settings view rows keyed by these same strings) that this
    # provider's Settings block should show, populated from that vendor's own documentation (see
    # CONFIG_SOURCE/CONFIG_NOTES). Empty when nothing could be confirmed from an official source.
    REQUIRED_CONFIG = []

    # 'confirmed' / 'partial' / 'unconfirmed' - see CONFIG_STATUS_SELECTION. Surfaced in the Settings UI
    # so an administrator sees explicitly how much to trust the shown fields, rather than assuming
    # every provider here is equally verified.
    CONFIG_STATUS = 'unconfirmed'

    # URL of the official vendor documentation page(s) actually read to determine REQUIRED_CONFIG.
    CONFIG_SOURCE = None

    # {'test': url, 'production': url} - pre-fills the Settings "API Base URL" field when a vendor's
    # API lives at one fixed, documented host. Left {} when no such host is known/confirmed.
    DEFAULT_BASE_URL = {}

    # Short human-readable caveat shown alongside the Settings block for this provider.
    CONFIG_NOTES = ("No official API authentication documentation could be located for this provider. "
                     "Confirm directly with the vendor before configuring credentials.")

    def __init__(self, base_url=None, client_id=None, client_secret=None, api_key=None,
                 username=None, password=None, certificate_id=None, account_id=None,
                 redirect_url=None, environment='test', timeout_limit=None):
        """ Store the company's configured ASP credentials and open an HTTP session for this
        connector instance. Every parameter is a generic credential "slot" - a concrete subclass
        only reads the ones its REQUIRED_CONFIG declares. """
        self.base_url = base_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_key = api_key
        self.username = username
        self.password = password
        # a certificate.certificate record, or None
        self.certificate_id = certificate_id
        # e.g. Pagero's `companyId` - a sub-account/tenant identifier some ASPs require alongside
        # client_id/client_secret
        self.account_id = account_id
        # required by OAuth2 authorization_code-style flows (e.g. Pagero)
        self.redirect_url = redirect_url
        self.environment = environment
        self.timeout_limit = min(timeout_limit or 10, 30)
        self._session = requests.Session()
        self._session.headers.update({'Accept': 'application/json'})

    def __enter__(self):
        """ Support using a connector as a context manager, e.g. `with company._l10n_om_edi_get_connector() as c`. """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """ Close the underlying HTTP session on exiting the `with` block. """
        self._session.close()

    # -------------------------------------------------------------------------
    # Interface - implement in a concrete vendor subclass
    # -------------------------------------------------------------------------

    def submit_invoice(self, invoice_xml, tdd_xml, document):
        """ Submit a PINT OM invoice/credit-note XML together with its Tax Data Document (TDD) XML.

        :param bytes invoice_xml: the PINT OM Invoice/CreditNote XML (Corners 1-4, Peppol network).
        :param bytes tdd_xml: the Tax Data Document XML (Corner 5, sent to the Oman Tax Authority).
        :param l10n.om.edi.document document: the submission-tracking record itself (its `move_id`
            gives the invoice, `l10n_om_edi_uuid` the supplier-generated UUID) - passed alongside the
            generated XML because not every ASP's documented API actually wants that XML on the wire:
            some (Flick Network) accept it, others (Fynamics) only document a proprietary JSON schema
            built from the same underlying data. `invoice_xml`/`tdd_xml` are still always generated and
            kept as attachments regardless of what a given connector actually transmits (Oman's 10-year
            self-archival requirement needs that XML to exist either way).
        :return: an ASP-assigned reference string identifying this submission.
        :rtype: str
        """
        raise self._not_configured_error()

    def get_status(self, asp_reference):
        """ Poll the ASP for the current status of a previously submitted document.

        :param str asp_reference: the reference returned by a prior `submit_invoice` call.
        :return: one of 'in_progress', 'accepted', 'rejected', 'error'.
        :rtype: str
        """
        raise self._not_configured_error()

    def cancel(self, asp_reference, reason):
        """ Request cancellation of a previously submitted document, if the ASP/OTA rules allow it.

        :param str asp_reference: the reference returned by a prior `submit_invoice` call.
        :param str reason: a human-readable cancellation reason.
        :return: whether the cancellation was accepted by the ASP.
        :rtype: bool
        """
        raise self._not_configured_error()

    def test_connection(self, country_code):
        """ Optional: verify the configured credentials actually authenticate against the ASP, without
        submitting any invoice data. Not every connector implements this (only worth adding once a
        vendor's real auth flow AND a genuinely side-effect-free endpoint are both confirmed) - the
        base implementation is intentionally unimplemented rather than a copy of _not_configured_error,
        so callers can tell "no ASP selected" apart from "this ASP's connector doesn't offer a test
        connection method yet".

        :param str country_code: ISO country code to check, e.g. 'OM'.
        :rtype: dict
        """
        raise NotImplementedError(f"{self.display_name} connector does not implement test_connection().")

    # -------------------------------------------------------------------------
    # Shared HTTP helpers, available to concrete subclasses
    # -------------------------------------------------------------------------

    def _not_configured_error(self):
        """ Return (not raise) a UserError explaining this ASP has no working integration yet. """
        return UserError(_(
            "No working Accredited Service Provider (ASP) integration is configured for %(provider)s yet. "
            "Select and contract an ASP via the Fawtara Portal, then complete this connector's API "
            "integration once that provider's API documentation/sandbox is available. In the meantime, "
            "the generated PINT OM invoice and Tax Data Document XML can be submitted to your ASP "
            "manually (see Settings > Accounting > Oman E-Invoicing).",
            provider=self.display_name,
        ))

    def _request(self, method, endpoint, params=None, json=None, data=None, headers=None,
                 files=None, handle_response=True):
        """ Perform one HTTP call against `self.base_url + endpoint`, logging the response body on
        failure, and either return the parsed/validated response (`handle_response=True`) or the raw
        `requests.Response` for a caller that needs custom handling. """
        start = datetime.utcnow()
        url = f"{self.base_url}{endpoint}"

        try:
            response = self._session.request(
                method, url,
                timeout=self.timeout_limit,
                params=params,
                json=json,
                data=data,
                headers=headers,
                files=files,
            )
        except requests.exceptions.RequestException as e:
            _logger.info("Network error calling %s: %s", self.display_name, e)
            raise UserError(_("Network connectivity issue while contacting %(provider)s. Please check your "
                               "internet connection and try again.", provider=self.display_name))

        duration = (datetime.utcnow() - start).total_seconds()
        # Response body is logged on failure to help debug real-world auth/schema mismatches - safe to
        # log since it's the ASP's own response, not anything we sent (credentials aren't in it).
        if response.status_code >= 400:
            _logger.info('"%s %s" %s %.3fs - response body: %s', method, url, response.status_code,
                         duration, response.text[:2000])
        else:
            _logger.info('"%s %s" %s %.3fs', method, url, response.status_code, duration)

        if handle_response:
            return self._handle_response(response)
        return response

    def _handle_response(self, response):
        """ Raise a clear UserError for auth/transport/JSON failures, otherwise return the parsed
        JSON body. """
        if response.status_code in (401, 403):
            raise UserError(_("Authentication with %(provider)s failed. Please check the API credentials "
                               "configured in Settings > Accounting > Oman E-Invoicing.", provider=self.display_name))
        if 403 < response.status_code < 600:
            raise UserError(_("%(provider)s could not process this request (%(status)s - %(reason)s). "
                               "Please try again later.", provider=self.display_name,
                               status=response.status_code, reason=response.reason))
        try:
            return response.json()
        except JSONDecodeError:
            _logger.exception("Invalid JSON response from %s: %s", self.display_name, response.text)
            raise UserError(_("An error occurred while reading the response from %(provider)s. Please try "
                               "again later.", provider=self.display_name))
