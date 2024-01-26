odoo.define('common_connector_library.InAppNotificationWidget', function (require) {
    "use strict";

    var Widget = require('web.Widget');
    const widgetRegistry = require('web.widget_registry');
    var core = require('web.core');
    var QWeb = core.qweb;

    var InAppEpt = Widget.extend({
        xmlDependencies: ['/common_connector_library/static/src/xml/in_app_notification.xml'],
        template: 'emipro_in_app_notify',

        init: function (parent, show, details) {
            this.show = show;
            this.updates = details.updates;
            this.template_data = '';
            if (this.updates && this.updates.length > 0) {
                if (!('emipro_in_app_notify' in QWeb.templates)) {
                    new Promise(async resolve => {
                        QWeb.add_template("/common_connector_library/static/src/xml/in_app_notification.xml")
                    });
                    this.template_data = $(QWeb.render(this.template, {
                        module_name: details.module_name,
                        updates: this.updates,
                        update_url: details.update_url
                    }).trim());
                }
            }
        },

        start: function () {
            return this._super.apply(this, arguments);
        },

        do_show: function (target='.o_action_manager') {
            if (this.show && this.updates.length > 0) {
                this.template_data = $(QWeb.render(this.template, {
                    module_name: details.module_name,
                    updates: this.updates,
                    update_url: details.update_url
                }).trim());
                $("#notify_ept").remove();
                $("div.hide_notification").remove();
                if ($("#notify_ept") && $("#notify_ept").length == 0) {
                    this.template_data.appendTo(target);
                    if (details.update_url == '' || details.update_url == undefined) {
                        $("button.update_button").hide();
                    }
                }
                if(self.odoo.info.is_hide == true){
                    $("#notify_ept").fadeOut(10);
                    $(".hide_notification").fadeIn(10);
                }else{
                    $("#notify_ept").fadeIn(1000);
                }
            }
        },

        do_hide: function () {
            if (this.show) {
                this.show = false;
                $("#notify_ept").remove();
                $("div.hide_notification").remove();
            }
        },
    });
    widgetRegistry.add('emipro_in_app_notify', InAppEpt);
    return InAppEpt;
});

