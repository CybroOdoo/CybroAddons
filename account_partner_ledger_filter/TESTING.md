Validation on Odoo 17 (2026-11-16)
================================

Installed with dependencies into a new database, without demo data.
All 8 module tests ran post-install: 0 failures, 0 errors.
The balance test also renders HTML with the balance option on and off,
checks opening 100 / closing 200, period lines, and excluded partners.
Statement coverage: models/ 100%, report/ 100%, wizard/ 100%.

The module depends on base_accounting_kit, which requires base_account_budget.
Both must be available as separate addons in the review project, along with
Odoo 17 core addons. They are present under custom/ in this workspace.

Reproduce from the Odoo repository root (use a NEW database name):

```sh
python -m coverage run --source=custom/account_partner_ledger_filter odoo-bin \
  -c odoo.conf -d partner_ledger_check_NEW -i account_partner_ledger_filter \
  --test-enable --test-tags /account_partner_ledger_filter --stop-after-init \
  --http-port=18079 --without-demo=all --data-dir=/tmp/partner_ledger_check
python -m coverage report --include='*/account_partner_ledger_filter/models/*'
python -m ruff check --isolated --select E4,E7,E9,F custom/account_partner_ledger_filter
python -m pylint --load-plugins=pylint_odoo --disable=all --enable=odoolint \
  --valid-odoo-versions=17.0 \
  --manifest-required-authors='Cybrosys Techno Solutions' \
  custom/account_partner_ledger_filter
```

Ruff and pylint-odoo completed without diagnostics. The author setting checks
this vendor's actual author rather than pylint-odoo's default OCA author.
Tools used: coverage 7.17.3, Ruff 0.17.5, pylint-odoo 10.0.12.
The install emitted upstream dependency warnings (including duplicate field
labels and description formatting); no module install or test errors occurred.

Distribution ZIP must have the module folder at its root, excluding caches,
bytecode, VCS files, editor files and symlinks. Upload a newly built ZIP for
each review attempt; the review service's duplicate-upload rule cannot be
verified locally.
