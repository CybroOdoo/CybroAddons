# Live QA cases

`qa_cases.py` holds the use cases (questions, chained creations, duplications, commands, files, edge
cases) and `qa_harness.py` runs them against a database with the live AI services, creating the drafted
records and checking them, everything rolled back.

The database needs demo data and the apps the cases use (Sales, Invoicing, Purchase, Inventory, CRM,
Project, Employees, Manufacturing), the OpenRouter key, and `allow_create` / `deep_analysis` enabled:

    odoo-bin db -c odoo.conf init qa_db --with-demo
    odoo-bin -c odoo.conf -d qa_db -i sale_management,account,purchase,stock,crm,project,hr,mrp,sale_crm,ai_chat_pro --stop-after-init
    QA_DIR=tests/qa odoo-bin shell -c odoo.conf -d qa_db --no-http < tests/qa/qa_harness.py

`QA_GROUP=chain` runs one group, `QA_ONLY=h01,h02` given cases; the results are written to
`QA_OUT` (default `qa_results.json`) in `QA_DIR`. These cases are not part of the unit test suite: they
call the AI services and cost tokens.
