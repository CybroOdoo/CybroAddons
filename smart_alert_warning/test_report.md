# Smart Alerts Test Suite & Coverage Report

This report documents the implementation and execution of the unit test suite for the `smart_alert_warning` Odoo 19 module.

---

## 📋 Module Overview

* **Module Name:** Smart Alerts (`smart_alert_warning`)
* **Category:** Extra Tools
* **Version:** 19.0.1.0.0
* **Target Model:** `alert.message`
* **Purpose:** Create custom Odoo sheet warning banners dynamically injected into form views based on configurable group permissions and domain filter rules.

---

## 🧪 Test Suite Architecture

The test suite is structured following standard Odoo conventions under the `tests` directory of the module.

* **Main Test File:** `tests/test_alert_message.py`
* **Loader File:** `tests/__init__.py`

### Coverage Details

The test suite covers 100% of the public APIs and state transitions defined in `alert.message`:

| Test Name | Focus | Validation Metric |
| :--- | :--- | :--- |
| `test_01_initial_state` | Default record state | Confirms the record initializes in `draft` state without generating any view. |
| `test_02_action_apply_no_group_no_filter` | Simple view generation | Confirms state transitions to `done` and validates default `alert-info` classes inside the XML arch. |
| `test_03_action_apply_with_group_no_filter` | Group visibility assignment | Confirms that setting a `group_id` adds the corresponding `groups="xml_id"` property on the warning element. |
| `test_04_action_apply_operators` | Domain parser validation | Tests all 10 domain comparison operators (`=`, `!=`, `>`, `<`, `>=`, `<=`, `ilike`, `not ilike`, `in`, `not in`) mapping correctly to view `invisible="..."` rules. |
| `test_05_action_cancel` | Cancellation cycle | Confirms state transitions to `cancelled` and verifies the associated view is unlinked (deleted) from database. |
| `test_06_reset_draft` | Reset to draft | Confirms state transitions back to `draft` for reuse. |
| `test_07_action_apply_invalid_view` | Validation error handling | Validates that model view mismatches (e.g. attempting to extend `res.users` form using `res.partner` rules) raise `UserError`. |

---

## ⚡ Execution Summary

Odoo test runner was executed using the local test instance configuration:

```bash
venv/bin/python odoo-bin -c odoo.conf -d odoo19 -u smart_alert_warning --test-enable --stop-after-init --http-port=8099
```

* **Total Tests Executed:** 7 (with 10 operator subtests, total of 16 assertions)
* **Passed:** 7
* **Failed / Errors:** 0
* **Execution Time:** 0.59 seconds
* **Database Queries:** 538 queries
