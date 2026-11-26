# Partner Ledger with Partner Filter

Generate a partner ledger from selected contacts in Odoo 17. This module extends
Full Accounting Kit and adds partner selection and opening and closing balances.

## Features

- Open the Partner Ledger wizard from the Action menu on one or more contacts.
- Select included partners in the report wizard.
- Use the inherited date, journal, customer/supplier, posted-entry, reconciliation,
  and currency options.
- Enable **Include Initial & Closing Balance** and set a start date to show
  opening balances, running balances, and closing totals for each partner.

## Requirements and installation

Requires Odoo 17 and `base_accounting_kit`. That addon also requires
`base_account_budget` and its declared Odoo core dependencies. Install these
addons in the same Odoo environment before installing this module. Direct
models and actions used here are supplied by `base_accounting_kit`; transitive
dependencies remain declared by their owning addons.

Add the addon directories to `addons_path`, update the Apps list, and install
**Partner Ledger with Partner Filter**. Use a user with accounting report access.
No additional configuration, controller, demo data, or scheduled task is needed.

## Usage

1. Open Contacts and select one or more partners.
2. Choose **Action > Partner Ledger**.
3. Check Included Partners, set the date range and journal filters, and choose
   customer, supplier, or both account types.
4. To include opening and closing balances, enable the balance option and set
   Date From. Opening balances use entries strictly before Date From; period
   entries use the selected date range. Closing balances add both amounts.
5. Print the report. With the balance option disabled, the standard period
   ledger is displayed. Leave Included Partners empty to discover partners with
   matching period entries.

Opening balances follow the selected account types, journals, move states,
reconciliation option, and the user's company access. Without Date From, the
legacy cutoff is Date To; use an explicit start date for a period ledger.

## Testing and release notes

See [TESTING.md](TESTING.md) for commands and
[CHANGELOG.md](CHANGELOG.md) for release notes. Tests create real journal entries,
check partner and account filtering, verify report actions, and render the HTML
report. The app description is [static/description/index.html](static/description/index.html).

## License and support

GNU Affero General Public License v3 (`AGPL-3`).
Author and maintainer: Cybrosys Techno Solutions.
Developer: Mruthul Raj. Contact: <odoo@cybrosys.com>.
Website: <https://www.cybrosys.com>.
