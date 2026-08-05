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
from .base import L10nOmEdiConnector, CONNECTOR_REGISTRY

# Importing each vendor module registers its connector class into CONNECTOR_REGISTRY (see base.py's
# @register_connector decorator). Add a new ASP by creating one file here + a matching Selection
# option on res.company.l10n_om_edi_asp_provider (see models/res_company.py). Only Flick Network has
# a real, confirmed connector currently; the other 11 OTA-accredited providers still appear in the
# Settings dropdown (see ASP_PROVIDER_SELECTION in models/res_company.py) but have no connector class
# registered here - selecting one surfaces a clear "not configured" error rather than a stub file.
from . import flick


def get_connector_class(provider_code):
    """ Return the connector class registered for the given ASP provider code, or None. """
    return CONNECTOR_REGISTRY.get(provider_code)
