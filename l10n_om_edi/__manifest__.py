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
{
    'name': 'Fawtara Oman - E-invoicing',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Localizations/EDI',
    'summary': "Fawtara,Fawtara Odoo, Oman odoo, Oman E-Invoicing, e-invoice,PINT OM e-invoice generation and ASP submission for the Oman Tax Authority's Fawtara program",
    'description': """
    Fawtara Oman - E-invoicing
    ==========================

    Generates the PINT OM e-invoice format (Peppol International Model, Oman specialization) and
    submits it to the Oman Tax Authority through an Accredited Service Provider (ASP):

    * PINT OM XML generation/import (5-corner Peppol model, Corners 1-4) - usable standalone for
      manual ASP submission, with no network calls of its own.
    * A per-company choice of Accredited Service Provider (ASP) - businesses in Oman's 5-corner Peppol
      model must route through one of several OTA-accredited providers, there is no direct connection
      and no Odoo-hosted access point for Oman.
    * A submission-tracking model (l10n.om.edi.document) recording the generated invoice XML, the
      separate Tax Data Document (TDD) sent to the Oman Tax Authority, and the ASP's acknowledgement.
    * A QR-code helper for invoices.

    IMPORTANT: the ASP Provider list here is exactly the Oman Tax Authority's own published
    Accredited Service Provider list (verified 2026-07-30 - see
    https://fawtara.taxoman.gov.om/accredited-service-providers). Only Flick Network has a real,
    confirmed connector (working authentication and a real connectivity check) - the other 11
    providers still appear in the dropdown, since they genuinely are OTA-accredited, but have no
    connector implementation yet; selecting one surfaces a clear "not configured" error rather than
    a stub. This is deliberate, deferred work, not an oversight (no ASP account/production
    credentials were available for the others at the time of writing).
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['l10n_om', 'account_edi_ubl_cii', 'base_vat', 'certificate'],
    'data': [
        'security/ir.model.access.csv',
        'security/l10n_om_edi_security.xml',
        'data/ir_cron.xml',
        'views/l10n_om_edi_document_views.xml',
        'views/account_move_view.xml',
        'views/res_company_view.xml',
        'views/res_partner_view.xml',
        'views/res_config_settings_view.xml',
        'views/report_invoice.xml',
        'wizard/l10n_om_edi_cancel_wizard_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
