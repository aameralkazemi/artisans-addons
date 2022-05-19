/** @odoo-module **/

import { browser } from "@web/core/browser/browser";
import { ConnectionLostError } from "@web/core/network/rpc_service";
import { registry } from "@web/core/registry";
// import rpc from "web.rpc";

/*
* Implemented based on standard Odoo calendar notifications
*/
export const baCalendarNotification = {
    dependencies: ["action", "notification", "rpc"],

    start(env, { action, notification, rpc }) {
        let calendarNotifbaTimeouts = {};
        let nextbaCalendarNotifTimeout = null;
        const displayedbaNotifications = new Set();
        /*
         * Event caught when UI has been loaded => declarare notification & timer to update 
        */
        env.bus.on("WEB_CLIENT_READY", null, async () => {
            const legacyEnv = owl.Component.env;
            legacyEnv.services.bus_service.onNotification(this, (notifications) => {
                for (const { payload, type } of notifications) {
                    if (type === "alarm.task") {
                        displaybaCalendarNotification(payload);
                    }
                }
            });
            legacyEnv.services.bus_service.startPolling();
            getNextCalendarNotif();
        });
        /*
         * Declare each notification and timeouts to show 
        */
        function displaybaCalendarNotification(notifications) {
            let lastNotifTimer = 0;
            browser.clearTimeout(nextbaCalendarNotifTimeout);
            Object.values(calendarNotifbaTimeouts).forEach((notif) => browser.clearTimeout(notif));
            calendarNotifbaTimeouts = {};
            notifications.forEach(function (notif) {
                const key = notif.event_id + "," + notif.alarm_id;
                if (displayedbaNotifications.has(key)) {
                    return;
                }
                calendarNotifbaTimeouts[key] = browser.setTimeout(function () {
                    const notificationRemove = notification.add(notif.message, {
                        title: notif.title,
                        type: "warning",
                        sticky: true,
                        onClose: () => {
                            displayedbaNotifications.delete(key);
                        },
                        buttons: [
                            {
                                name: env._t("OK"),
                                primary: true,
                                onClick: async () => {
                                    await rpc(
                                        "business/appointment/alarm/delete",
                                        {"alarm_id": notif.alarm_id}, { silent: true }
                                    );
                                    notificationRemove();
                                },
                            },
                            {
                                name: env._t("Details"),
                                onClick: async () => {
                                    await rpc(
                                        "business/appointment/alarm/delete",
                                        {"alarm_id": notif.alarm_id}, { silent: true }
                                    );
                                    const action_id = await rpc(
                                        "business/appointment/get/action",
                                        {"event_id": notif.event_id}, { silent: true }
                                    )
                                    await action.doAction(action_id);
                                    notificationRemove();
                                },
                            },
                            {
                                name: env._t("Snooze"),
                                onClick: () => {
                                    notificationRemove();
                                },
                            },
                        ],
                    });
                    displayedbaNotifications.add(key);
                }, notif.timer * 1000);
                lastNotifTimer = Math.max(lastNotifTimer, notif.timer);
            });

            if (lastNotifTimer > 0) {
                nextbaCalendarNotifTimeout = browser.setTimeout(
                    getNextCalendarNotif,
                    lastNotifTimer * 1000
                );
            }
        }
        /*
         * Get new notifications (triggered by the timer)
        */ 
        async function getNextCalendarNotif() {
            try {
                const result = await rpc("/business/appointment/popup/notify", {}, { silent: true });
                displaybaCalendarNotification(result);
            } catch (error) {
                if (!(error instanceof ConnectionLostError)) {
                    throw error;
                }
            }
        }
    },
};

registry.category("services").add("baCalendarNotification", baCalendarNotification);
