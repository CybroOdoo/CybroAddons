## Module <base_accounting_kit>

#### 17.09.2026
#### Version 20.0.1.0.0
#### ADD
- Initial commit for Odoo 20 Full Accounting Kit for Community.

#### 13.10.2026
#### Version 20.0.1.1.0
#### FIX
- Owl 3 compatibility, bank reconciliation errors and report date validation.

#### 15.10.2026
#### Version 20.0.2.1.0
#### ADD
- Bank reconciliation: quick actions, smart matching, multi-invoice reconciliation.
- German translations updated; 19+ new languages.

#### 16.11.2026
#### Version 20.0.2.6.0
#### REMOVE
- Automatic currency rate updates removed; use manual rates or another module (FX revaluation not affected).
- After upgrading from 20.0.2.1.0 or earlier, archive the old currency-rate scheduled action manually.
#### FIX
- XLSX export: CSRF protection, allowed models only, access rights checked.
- Bank reconciliation "Match Existing" list: no HTML injection from journal item data.
- Balance Sheet / Profit and Loss: correct structure, signs, Equity section and comparison.
- Cash Flow report no longer crashes.
- Tax Report: correct signs, sales / purchases sections with totals, 0% and archived taxes listed.
- General Ledger, Trial Balance, Partner Ledger: opening balances per fiscal year and Result Brought Forward.
- Day Book, Cash Book, Bank Book and Aged Partner Balance fixed.
- Reports print the right company, currency and branches.
- Assets: depreciation posted when due with its amount; disposal, grouped entries and Modify fixed.
- Follow-up report: correct open invoices, totals in company currency, overdue rows in red.
- Bank statement import: one statement per file, correct balances, duplicate check, QIF fixed.
- FX revaluation: partner on receivable / payable lines, foreign-currency bank accounts revalued.
- Reconciliation: taxes, analytic and all reconcile model lines applied.
- Access rights: invoice copies printable by all users; Accountants can manage assets.
#### CHANGE
- Chief Accountant no longer implies Administrator (the upgrade log lists affected users).
- Stylesheet limited to the kit's own screens.
- Translations cleaned; new template i18n/base_accounting_kit.pot.

#### 26.11.2026
#### Version 20.0.3.0.0
#### ADD
- All 12 accounting reports are interactive screens with filters, comparison, unfold, search and drill-down.
- Export menu on every report: PDF, Excel, CSV and Print, matching the screen.
- Saved filters (Favorites) per user and report.
- Columns by quarter or month in Profit and Loss, Balance Sheet and Trial Balance.
- Amount units (as is, no decimals, K, M) and optional currency symbol in amounts.
- Bank Reconciliation report (Reporting > Audit Reports).
- Print Journal Entry PDF on the company letterhead.
- New bank reconciliation screen: Sure match / Please confirm / Needs you, Accept all sure, suggestions drawer.
- Open items matching for invoices, bills, payments and credit notes without a bank line.
- Statement import: CAMT.052 / .053 / .054, MT940, saved CSV / XLSX formats, several files at once, email alias.
- Accounting > Closing: Lock Dates (all five), Lock Exceptions, Currency Revaluation.
- Fiscal Years: custom-length years used by reports and entry numbering.
- Year-end Closing: checks, closing entry to Retained Earnings, Reopen.
- Month-end Closing: automatic checks, closing tasks, optional month lock.
- Tax Report: taxes based on payment counted when paid; Withholding section with core's withholding module.
#### CHANGE
- Reporting menu follows Odoo's folders (Statement, Audit, Partner, Taxes, Daily, Management).
- Review > To Review menu; Assets and Budgets under Accounting > Management.
- Profit and Loss, Balance Sheet and Cash Flow read as statements, result on the last line.
- An account line opens its General Ledger; a click anywhere on a line unfolds or opens it.
- PDF and Excel restyled as statements: heading panel, subtotal lines, double line under the total, page footer.
- Negative amounts in red; zeros in light grey in PDF and Excel.
- Accounting roles: read-only users see all reports; Chief Accountants can set lock dates.
- "Odoo20 Dynamic Accounting Reports" (dynamic_accounts_report) is no longer needed: uninstall it.
- Follow-up screens redesigned: reminder plan with editable steps; statuses Reminder due / Overdue, waiting / Up to date.
- Translation files updated in all languages (new texts in English until translated).
#### FIX
- Balance Sheet balances after a Year-end Closing.
- Bank Book and Cash Book show the period's debit and credit.
- Tax Report: groups of taxes listed with their child taxes and bases.
- Partner Ledger and Day Book show account names, not raw translation text.
- Asset history messages formatted (old ones fixed on upgrade).
- CSV export: no -0.00 amounts.
- Button icons on Month-end Closing, Fiscal Years and Lock Exceptions.
#### REMOVE
- Report wizards and old report PDF templates (menus open the screens directly).
- Old reconciliation kanban.
