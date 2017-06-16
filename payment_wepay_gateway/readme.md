# Wepay Payment Gateway

Wepay Payment Acquirer act as a new payment method in odoo e-commerce and easy checkout functionality with two steps.

  - We have two modes test & production
  - Test Url - https://stage.wepay.com/
  - Production mode - https://www.wepay.com/
  - Follow here to create test account https://stage.wepay.com/register/
  - Follow here to create Production account https://www.wepay.com/register/

  - expected one of currencies 'CAD', 'GBP', 'USD'

### Depends
Ecommerce, Website, Payment modules in odoo

### Tech
* [Python] - Models,Controllers
* [XML] - Odoo website templates, views

### Installation
- www.odoo.com/documentation/9.0/setup/install.html
- Install our custom addon, which also installs its depends [website, website_sale, payment]
 
### Usage
> Provide Wepay test or active account credentials.
> Account id, access_tocken, client id will be get after creating a client account on wepay.
> Follow https://support.wepay.com/hc/en-us/articles/203609673-How-do-I-set-up-my-WePay-account- for account creation.
> Wepay Support https://support.wepay.com/hc/en-us/articles/203609503-WePay-FAQ
> Publish wepay acquirer for odoo e-commerce.
> redirect and the callback_uri must be a full URL and must not include localhost or wepay.com.

### References
https://developer.wepay.com/
https://www.wepay.com/developer
https://www.wepay.com/developer/register
https://stage-go.wepay.com/
https://go.wepay.com/

License
----
GNU LESSER GENERAL PUBLIC LICENSE, Version 3 (LGPLv3)
(http://www.gnu.org/licenses/agpl.html)



