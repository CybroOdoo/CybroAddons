# Theme Converza

Modern, fully responsive website theme for digital marketing agencies on Odoo 17.

## Features

- Ready-made pages: Home, Services, Results, Case Studies, Pricing, About Us, Contact Us and Blog.
- Eleven drag-and-drop snippets for the website builder.
- Custom header (sticky, responsive offcanvas menu) and footer.
- Animated counters, monthly/annual pricing switch, and case study and blog filters.
- Self-contained: the Iconify script is bundled in `static/lib`.

## Installation

1. Copy the `theme_converza` folder into your Odoo 17 addons path.
2. Restart Odoo and update the apps list.
3. Install **Theme Converza** from Apps (this also installs Website, Blog and Mass Mailing).
4. Open **Website → Configuration → Settings** (or the website builder) and choose **Theme Converza**.

## Configuration

Menu entries are created from `data/menu_data.xml` when the theme is applied to a website and are removed
again when the website switches to another theme.

## Third-party libraries

| Library | Version | License | Location |
|---|---|---|---|
| iconify-icon | 1.0.8 | MIT | `static/lib/iconify` |

Icon artwork is loaded on demand from the public Iconify API, so visitors need internet access to see icons.

## Testing

```
odoo-bin -d <db> -i theme_converza --test-tags /theme_converza --stop-after-init
```

## Credits

Author and maintainer: Cybrosys Techno Solutions (https://www.cybrosys.com)

License: LGPL-3
