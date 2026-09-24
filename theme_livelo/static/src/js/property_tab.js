/** @odoo-module **/
import publicWidget from '@web/legacy/js/public/public_widget';

publicWidget.registry.PropertiesTab = publicWidget.Widget.extend({
    selector: '.main_section_levelo, .section-discover-homelego',
    events: {
        'click .nav-link[data-bs-toggle="tab"]': '_onTabClick',
        'click .nav-tabs a': '_onTabClick',
        'click .nav a': '_onTabClick',
    },
    start: function () {
        var res = this._super.apply(this, arguments);
        return res;
    },
    _onTabClick: function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        var $target = $(ev.currentTarget);
        var targetSelector = $target.attr('data-bs-target') || $target.attr('href');
        if (!targetSelector) {
            return;
        }
        // Deactivate all nav links in this snippet
        this.$('.nav-link, .nav-tabs a').removeClass('active').attr('aria-selected', 'false');
        // Activate clicked link
        $target.addClass('active').attr('aria-selected', 'true');
        // Deactivate all tab panes in this snippet
        this.$('.tab-pane').removeClass('show active');
        // Activate target tab pane within this snippet
        var $targetPane = this.$(targetSelector);
        if ($targetPane.length) {
            $targetPane.addClass('show active');
        }
    },
});
