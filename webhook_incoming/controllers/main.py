# Copyright 2024 Hoang Tran <thhoang.tr@gmail.com>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo.http import Controller, request, route


def get_webhook_request_payload():
    if not request:
        return None
    try:
        payload = request.get_json_data()
    except ValueError:
        payload = {**request.httprequest.args}
    return payload


class BaseAutomationController(Controller):
    @route(
        ["/web/hook/<string:rule_uuid>"],
        type="http",
        auth="public",
        methods=["GET", "POST"],
        csrf=False,
        save_session=False,
    )
    def call_webhook_http(self, rule_uuid, **kwargs):
        """Execute an automation webhook"""
        rule = (
            request.env["base.automation"]
            .sudo()
            .search([("webhook_uuid", "=", rule_uuid)])
        )
        if not rule:
            return request.make_json_response({"status": "error"}, status=404)

        data = get_webhook_request_payload()
        try:
            rule._execute_webhook(data)
        except Exception:  # noqa: BLE001
            return request.make_json_response({"status": "error"}, status=500)
        return request.make_json_response({"status": "ok"}, status=200)
