/** @odoo-module **/

var ajax = require('web.ajax');
var core = require('web.core');
import { url } from "@web/core/utils/urls";
import { patch } from "@web/core/utils/patch";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
const { useListener } = require('web.custom_hooks');
import { WebClient } from "@web/webclient/webclient";
import { hasTouch } from "@web/core/browser/feature_detection";
import * as web_extends from "@web_enterprise/webclient/webclient";
import { HomeMenu } from "@web_enterprise/webclient/home_menu/home_menu";
var Notification = require('common_connector_library.InAppNotificationWidget');
import { EnterpriseNavBar } from "@web_enterprise/webclient/navbar/navbar";
const { hooks } = owl;

var QWeb = core.qweb;

patch(HomeMenu.prototype, "common_connector_library.InAppEnterprise", {

    _openMenu: async function (ev) {
            await this._super.apply(this, arguments);
            this.openNotification(ev);
        },

    openNotification: function (ev) {
        var menu_id = this._getMenuId(ev);
        ajax.jsonRpc('/app_notification/get_module/', 'call', {
            menu_id: menu_id,
        }).then(function(details){
            self.details = details;
            var updates = details.updates;
            var notification = new Notification(this, true, details);
            if ((typeof updates === 'object') && updates.length > 0){
                notification.do_show();
            }else {
                notification.do_hide();
            }
        });
    },

    _getMenuId: function (ev) {
        var menu_id = false;
        if (ev && ev.id) {
            menu_id = ev.id;
        } else if (ev.data && ev.data.menu_id){
            menu_id = ev.data.menu_id;
        }
        return menu_id;
    },

    mounted: function () {
        this._super.apply(this, arguments);
        if ($("#notify_ept").length > 0) {
            $("#notify_ept").css({"display": "none"});
        }
    },
});


function _onClickHideEpt(ev) {
    $("#notify_ept").fadeOut(500);
    $(".hide_notification").fadeIn(500);
}

function _onClickToggle() {
    $("#notify_ept").fadeIn(500);
    $(".hide_notification").fadeOut(500);
}

function _upgradeRedirect(ev) {
    _onClickHideEpt();
    console.log(self.details.update_url)
    if (self.details && self.details.update_url) {
        var win = window.open(self.details.update_url, '_blank');
        if (!win) {
            console.error("Popup Blocked!!!, You Need to Allow Popup for this Website.");
        }
    }
}

function _onClickCloseEpt(ev) {
    $("#notify_ept").css({'display': 'none'});
    ajax.jsonRpc('/app_notification/deny_update/', 'call', {
        is_notify: false,
        url: this._current_state,
        module_name: self.details && self.details.module_name
    }).then(function(){
        return true;
    });
}

function _onClickReadMore(ev) {
    if (this.action_manager && this.action_manager.actions) {
        var is_current = false;
        var action_id = "common_connector_library.emipro_app_version_detail_action";
        var actions = this.action_manager.actions;
        for (var action in actions) {
            if (actions[action].xml_id == action_id) {
                is_current = true;
                break;
            }
        }
        if (!is_current) {
            this._callAction(action_id);
        }
        this._onClickHideEpt();
    }
}

function _callAction(action_name) {
    this.do_action({
        name: 'Emipro Apps Updates',
        res_model: 'emipro.app.version.details',
        domain: [['module_id', '=', self.details.module_id]],
        context: {'search_default_group_by_module_id': 1},
        views: [[false, 'list'], [false, 'form']],
        type: 'ir.actions.act_window',
        view_mode: "list"
    });
}

registry
//    .category("user_menuitems")
    .add("on_click_hide_ept", _onClickHideEpt)
    .add("on_click_toggle", _onClickToggle)
    .add("upgrade_redirect", _upgradeRedirect)
    .add("on_click_close_ept", _onClickCloseEpt)
    .add("on_click_read_more", _onClickReadMore)
    .add("call_action", _callAction)

//debugger;
web_extends.WebClientEnterprise = class WebClientEnterprise extends WebClient{
    constructor() {
        super(...arguments);
        // trigger to close this screen (from being shown as tempScreen)
        useListener('click #hide_popup', () => { console.log('clicked!!!'); });

    }

    setup() {
        super.setup();
        this.hm = useService("home_menu");
        useService("enterprise_legacy_service_provider");
        hooks.onMounted(() => {
            this.env.bus.on("HOME-MENU:TOGGLED", this, () => {
                if (!this.el) {
                    return;
                }
                this._updateClassList();
            });
            this._updateClassList();
            this.el.classList.toggle("o_touch_device", hasTouch());

            $('#hide_popup').click(function(){
                return _onClickHideEpt();
            });

            $('#close_popup').click(function(){
                return _onClickCloseEpt();
            });

            $('.hide_notification').click(function(){
                return _onClickToggle();
            });

            $('button.update_button').click(function(){
                return _upgradeRedirect();
            });

            $('button.read_more').click(function(){
                return _onClickReadMore(this);
            });
        });
    }
    _updateClassList() {
        this.el.classList.toggle("o_home_menu_background", this.hm.hasHomeMenu);
        this.el.classList.toggle("o_has_home_menu", this.hm.hasHomeMenu);
    }
    _loadDefaultApp() {
        return this.hm.toggle(true);
    }
};
web_extends.WebClientEnterprise.components = { ...WebClient.components, NavBar: EnterpriseNavBar };


