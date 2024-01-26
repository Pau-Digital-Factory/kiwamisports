odoo.define('common_connector_library.InAppDomReady', function (require) {
    var session = require('web.session');
    var flavour = session.server_version_info;
    var core = require('web.core');
    var hash = this.location.hash;
    var Notification = require('common_connector_library.InAppNotificationWidget');
    var ajax = require('web.ajax');
    require('web.dom_ready');
    if (hash.length > 0 && hash.match('menu')) {
        var param_string = hash.replace('#', '');
        var params = JSON.parse('{"' + decodeURI(param_string).replace(/"/g, '\\"').replace(/&/g, '","').replace(/=/g,'":"').replace(/\s/g,'') + '"}');
        var menuID = parseInt(params.menu_id)
        ajax.jsonRpc('/app_notification/get_module/', 'call', {
            menu_id: menuID,
        }).then(function(details){
            self.details = details;
            var updates = details.updates;
            var notification = new Notification(this, true, details);
            if ((typeof updates === 'object') && updates.length > 0){
                notification.do_show(target='body');
            }else {
                notification.do_hide();
            }
        });
    }
});