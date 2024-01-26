/** @odoo-module **/

import * as web_extends from "@web/webclient/webclient";
import { NavBar } from "@web/webclient/navbar/navbar";
import { useTooltip } from "@web/core/tooltip/tooltip_hook";
import { useBus, useEffect, useService } from "@web/core/utils/hooks";
import { ActionContainer } from "@web/webclient/actions/action_container";
var Notification = require('common_connector_library.InAppNotificationWidget');
import { NotUpdatable } from "@web/core/utils/components";
import { MainComponentsContainer } from '@web/core/main_components_container';
import { useOwnDebugContext } from "@web/core/debug/debug_context";
import { registry } from "@web/core/registry";
import { DebugMenu } from "@web/core/debug/debug_menu";
import { localization } from "@web/core/l10n/localization";
const { Component, hooks } = owl;
const { useExternalListener } = hooks;
var ajax = require('web.ajax');
var core = require('web.core');

function _onClickHideEpt(ev) {
    $("#notify_ept").fadeOut(500);
    $(".hide_notification").fadeIn(500);
}

function _onClickToggle() {
    $("#notify_ept").fadeIn(500);
    $(".hide_notification").fadeOut(500);
}

function _upgradeRedirect(ev) {
    _onClickHideEpt(ev);
    if (self.details && self.details.update_url) {
        var win = window.open(self.details.update_url, '_blank');
        if (!win) {
            console.error("Popup Blocked!!!, You Need to Allow Popup for this Website.");
        }
    }
}

function _onClickCloseEpt(ev,current_url) {
    $("#notify_ept").css({'display': 'none'});
    ajax.jsonRpc('/app_notification/deny_update/', 'call', {
        is_notify: false,
        url: current_url,
        module_name: self.details && self.details.module_name
    }).then(function(){
        return true;
    });
}

function _callAction(actionService) {
        self.odoo.info['is_hide'] = true;
        actionService.doAction({
            name: 'Emipro Apps Updates',
            res_model: 'emipro.app.version.details',
            domain: [['module_name', 'in', [self.details.technical_name,'common_connector_library']]],
            context: {'search_default_group_by_module_id': 1},
            views: [[false, 'list'], [false, 'form']],
            type: 'ir.actions.act_window',
            view_mode: "list"
        });
    }

web_extends.WebClient = class WebClient extends Component {
    setup() {
        this.menuService = useService("menu");
        this.actionService = useService("action");
        this.title = useService("title");
        this.router = useService("router");
        this.user = useService("user");
        useService("legacy_service_provider");
        useOwnDebugContext({ categories: ["default"] });
        if (this.env.debug) {
            registry.category("systray").add(
                "web.debug_mode_menu",
                {
                    Component: DebugMenu,
                },
                { sequence: 100 }
            );
        }
        this.localization = localization;
        this.title.setParts({ zopenerp: "Odoo" }); // zopenerp is easy to grep
        useBus(this.env.bus, "ROUTE_CHANGE", this.loadRouterState);
        useBus(this.env.bus, "ACTION_MANAGER:UI-UPDATED", (mode) => {
            if (mode !== "new") {
                this.openNotification(this.env);
                this.el.classList.toggle("o_fullscreen", mode === "fullscreen");
            }
            if ($("#notify_ept").length > 0) {
                $("#notify_ept").css({"display": "none"});
                $(".hide_notification").css({"display": "none"});
            }
        });
        useEffect(
            () => {
                this.loadRouterState();
            },
            () => []
        );
        useExternalListener(window, "click", this.onGlobalClick, { capture: true });
        useTooltip();
    }

    mounted() {
        // the chat window and dialog services listen to 'web_client_ready' event in
        // order to initialize themselves:
        this.env.bus.trigger("WEB_CLIENT_READY");
    }

    async loadRouterState() {
        let stateLoaded = await this.actionService.loadState();
        let menuId = Number(this.router.current.hash.menu_id || 0);

        if (!stateLoaded && menuId) {
            // Determines the current actionId based on the current menu
            const menu = this.menuService.getAll().find((m) => menuId === m.id);
            const actionId = menu && menu.actionID;
            if (actionId) {
                await this.actionService.doAction(actionId, { clearBreadcrumbs: true });
                stateLoaded = true;
            }
        }

        if (stateLoaded && !menuId) {
            // Determines the current menu based on the current action
            const currentController = this.actionService.currentController;
            const actionId = currentController && currentController.action.id;
            const menu = this.menuService.getAll().find((m) => m.actionID === actionId);
            menuId = menu && menu.appID;
        }

        if (menuId) {
            // Sets the menu according to the current action
            this.menuService.setCurrentMenu(menuId);
        }

        if (!stateLoaded) {
            // If no action => falls back to the default app
            await this._loadDefaultApp();
        }
    }

    _loadDefaultApp() {
        // Selects the first root menu if any
        const root = this.menuService.getMenu("root");
        const firstApp = root.children[0];
        if (firstApp) {
            return this.menuService.selectMenu(firstApp);
        }
    }

    openNotification(ev) {
        var $target = $(ev.currentTarget);
        var menuID = this._getMenuId(ev);
        if (menuID){
            ajax.jsonRpc('/app_notification/get_module/', 'call', {
                menu_id: menuID,
            }).then(function(details){
                self.details = details;
                var updates = details.updates;
                var notification = new Notification(this, true, details);
                if ((typeof updates === 'object') && updates.length > 0 && document.location.href.match('menu_id')){
                    notification.do_show();
                } else {
                    notification.do_hide();
                }
            });
        }
    }

    _getMenuId(ev) {
        var menu_id = false;
        const currentController = this.actionService.currentController;
        const actionId = currentController && currentController.action.id;
        const menu = this.menuService.getAll().find((m) => m.actionID === actionId);
        menu_id = menu && menu.appID;
        if (!menu_id) {
          if (this.router.current.hash.menu_id){
             return this.router.current.hash.menu_id
          }else if (this.router.current.hash.ev){
            let node_list  = this.router.current.hash.ev.split('&')
            for (let obj in node_list){
                if(node_list[obj] && node_list[obj].split('=')[0] == 'action_id'){
                    let menu = this.menuService.getAll().find((m) => m.actionID === parseInt(node_list[obj].split('=')[1]));
                    menu_id = menu && menu.appID;
                }
            }
          }else{
              let root = this.menuService.getMenu("root").childrenTree;
              if(ev.target && ev.target.parentNode.href){
                  let node_list  = ev.target.parentNode.href.split('&')
                  for (let menu in root)
                  {
                    for (let obj in node_list)
                    {
                        if(node_list[obj] && node_list[obj].split('=' || '&' || '?' || '#').includes(String(root[menu].id))){
                            menu_id = root[menu].id
//                            this.router.current.hash['menu_id'] = menu_id
                              this.router.current.hash['ev'] = ev.target.parentNode.href
                            return menu_id;
                        }
                    }
                  }
              }
          }
        }
        return menu_id;
    }

    _getActionController(ev) {
      if (this.actionService && this.actionService.currentController) {
        const currentController = this.actionService.currentController.action;
        const ActionService = this.actionService;
        return { currentController, ActionService };
      } else {
        // Handle the case when either this.actionService or this.actionService.currentController is null
        // You can return a default value or throw an error, depending on your requirements
        return { currentController: null, ActionService: null };
      }
    }

    /**
     * @param {MouseEvent} ev
     */
    onGlobalClick(ev) {
        // When a ctrl-click occurs inside an <a href/> element
        // we let the browser do the default behavior and
        // we do not want any other listener to execute.
        if (
            ev.ctrlKey &&
            ((ev.target instanceof HTMLAnchorElement && ev.target.href) ||
                (ev.target instanceof HTMLElement && ev.target.closest("a[href]:not([href=''])")))
        ) {
            ev.stopImmediatePropagation();
            return;
        }

        var menuId = this._getMenuId(ev);
        const {currentController,ActionService} = this._getActionController(ev);

        $('#hide_popup').click(function(ev){
            self.odoo.info['is_hide'] = true;
            return _onClickHideEpt(ev);
        });

        const url = currentController && currentController.context ? currentController.context.params : null;
        $('#close_popup').click(function(){
            return _onClickCloseEpt(url);
        });

        $('.hide_notification').click(function(){
            self.odoo.info['is_hide'] = false;
            return _onClickToggle();
        });

        $('button.update_button').click(function(ev){
            return _upgradeRedirect(ev);
        });

        $('button.read_more').click(function(){
            var is_current = false;
            var action_id = "common_connector_library.emipro_app_version_detail_action";
            if(menuId){
                if (currentController.xml_id == action_id) {
                    is_current = true;
                }
                if (!is_current) {
                    _callAction(ActionService);
                }
                _onClickHideEpt();
            }
        });
    }
}
web_extends.WebClient.components = {
    ActionContainer,
    NavBar,
    NotUpdatable,
    MainComponentsContainer,
};
web_extends.WebClient.template = "web.WebClient";