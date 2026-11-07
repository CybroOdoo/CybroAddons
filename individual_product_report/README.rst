.. |license| image:: https://img.shields.io/badge/license-LGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3

.. |odoo| image:: https://img.shields.io/badge/Odoo-20.0-875A7B.svg
    :target: https://www.odoo.com
    :alt: Odoo 20.0

.. |maintainer| image:: https://img.shields.io/badge/maintainer-Cybrosys-875A7B.svg
    :target: https://cybrosys.com
    :alt: Maintainer: Cybrosys Techno Solutions

|license| |odoo| |maintainer|

Product Sale Report Graph View
==============================

The **Product Sale Report Graph View** module empowers sales teams, product managers, and business owners to analyze the commercial performance of individual products directly from their records. Instead of navigating away to generic reporting menus and manually configuring complex multi-level filters, users can instantly inspect dedicated graphical analytics with a single click.

A dedicated **Sales Report** smart button is seamlessly embedded into both **Product Template** and **Product Variant** form views. Clicking this smart button opens an interactive graph report focused specifically on the selected product's confirmed sales history, providing actionable insights into volume trends, customer demand patterns, and quantity distributions.

Module Overview & Functionality
-------------------------------

1. **Direct Smart Button Access**:
   A prominent "Sales Report" stat button with a signal graph icon is added to the top stat button container on product template and variant forms.

2. **Intelligent Visibility Logic**:
   The smart button is dynamically displayed only when:
   - The product is marked as saleable (``Can be Sold`` / ``sale_ok = True``).
   - The product has recorded at least one confirmed sale (``sales_count > 0``).
   This keeps form interfaces clean and uncluttered for non-saleable or newly created items.

3. **Multi-Format Interactive Visualizations**:
   The report supports instant switching between three major chart types:
   - **Line Chart**: Tracks historical sales velocity, demand trends, and seasonal fluctuations across dates.
   - **Bar Chart**: Enables straightforward volume comparisons across days, weeks, months, or years.
   - **Pie Chart**: Visualizes the proportional share and contribution of sales quantities.

4. **Product Template vs. Variant Isolation**:
   - **Product Template View**: Consolidates and aggregates sales metrics across all associated variants of the product template.
   - **Product Variant View**: Isolates metrics exclusively for the selected product variant (specific size, color, or configuration).

5. **Automated Date Grouping & Quantity Measurement**:
   The action pre-configures Odoo's reporting context to filter confirmed sales orders (``Orders`` filter), group data by order date (``group_by: date:day``), and automatically restrict the historical window to the last 365 days measuring ordered product quantities (``product_uom_qty``).

6. **Native Search & Filter Integration**:
   Users can apply Odoo's native search bar filters and group-by criteria (such as Customer, Salesperson, Sales Team, or custom date intervals) directly on the product's sales graph.

7. **Role-Based Security & Access Control**:
   Access to the action and underlying sales reporting data is restricted to authorized sales personnel holding ``Sales / User: Own Documents Only``, ``Sales / User: All Documents``, or ``Sales / Administrator`` permissions.

Key Features
------------

* **Dedicated Sales Report Smart Button**: Added to both product template and variant forms.
* **Instant Visual Analytics**: One-click direct access to graphical sales analysis without manual filter configuration.
* **Interactive Line Chart**: Analyze continuous sales velocity, growth trajectories, and demand trends.
* **High-Contrast Bar Chart**: Easily compare sales volumes across discrete time periods.
* **Proportional Pie Chart**: Understand sales volume proportions and distributions at a glance.
* **Template-Level Aggregation**: View cumulative sales performance for all variants under a template.
* **Variant-Level Granularity**: Drill down into specific product variants for isolated performance analysis.
* **Automated Context Configuration**: Pre-grouped by date with 365-day time filtering and quantity measurement.
* **Clean Interface Rules**: Smart button remains hidden until a saleable product has actual sales records.
* **Full Search & Group Flexibility**: Compatible with all standard Odoo search, filter, and grouping mechanisms.
* **Enterprise & Community Support**: Fully compatible with Odoo 20 Community and Enterprise editions.
* **Role-Based Security**: Strictly enforces user group permissions and access rights.

How It Works / Usage
--------------------

Follow these simple steps to utilize the module:

1. **Navigate to Products**:
   Go to **Sales** -> **Products** -> **Products** (or **Inventory** -> **Products** -> **Products**).

2. **Open a Product Record**:
   Click on any product template to open its form view. If working with variants, open the specific variant record from **Sales** -> **Products** -> **Product Variants**.

3. **Locate the Smart Button**:
   In the stat button bar at the top of the form, locate the **Sales Report** button (identified by a signal chart icon).
   *(Note: The button will be visible only if "Can be Sold" is checked and at least one confirmed sale exists).*

4. **Launch Graphical Analysis**:
   Click the **Sales Report** smart button. The system opens the **Sales Analysis** graph view pre-filtered to the chosen product or variant.

5. **Interact with Visualizations**:
   - By default, view the **Line Chart** displaying daily sales trends over the last 365 days.
   - Use the view switch buttons in the upper-right area to toggle to **Bar Chart** or **Pie Chart**.
   - Use the search bar to group by Customer, Salesperson, or custom time periods (Day, Week, Month, Quarter, Year).

Security & Access Rights
------------------------

This module integrates with Odoo's role-based access management:

* **Sales / User (Salesman)**: Granted read access to view the smart button and product sales analysis graphs.
* **Sales / Administrator (Manager)**: Granted full access to view, configure, and analyze sales reports.
* **Non-Sales Users**: The smart button is hidden and backend action access is restricted.

Installation
------------

1. Place the ``individual_product_report`` folder inside your custom Odoo addons directory.
2. Update the apps list in Odoo Developer Mode.
3. Search for ``Product Sale Report Graph View`` and click **Install**.
4. No external Python libraries are required.

Configuration
=============

No additional configuration is required. The smart button and graph views are available immediately upon installation for all products meeting the sales criteria.

Company
-------

* `Cybrosys Techno Solutions <https://cybrosys.com/>`__

Credits
-------

* Cybrosys Techno Solutions (<https://cybrosys.com>)

Contacts
--------

* Mail Contact : odoo@cybrosys.com
* Website : https://cybrosys.com

License
-------

Lesser General Public License, Version 3 (LGPL v3).
(http://www.gnu.org/licenses/lgpl-3.0-standalone.html)

Maintainer
==========

.. image:: https://cybrosys.com/images/logo.png
   :target: https://cybrosys.com

This module is maintained by Cybrosys Technologies.

For support and more information, please visit `Our Website <https://cybrosys.com/>`__
