import json
from unittest import mock

import requests

import odoo.tests
from odoo.tests.common import TransactionCase
from odoo.tools import ustr


@odoo.tests.tagged("post_install", "-at_install")
class TestOutgoingWebhook(TransactionCase):
    def test_01_trigger_webhook(self):
        test_automation = self.env["base.automation"].create(
            {
                "name": "Test outgoing webhook on updated partner",
                "model_id": self.env.ref("base.model_res_partner").id,
                "type": "ir.actions.server",
                "trigger": "on_create_or_write",
                "trigger_field_ids": [
                    (6, 0, [self.env.ref("base.field_res_partner__name").id])
                ],
                "state": "custom_webhook",
                "endpoint": "https://httpbin.org/post",
                "request_method": "post",
                "request_type": "request",
                "log_webhook_calls": True,
                "body_template": '{"name": "{{record.name}}", "email": "{{record.email}}"}',
            }
        )
        test_partner_1 = self.env["res.partner"].create(
            {"name": "Test Partner 1", "email": "test.partner1@test.example.com"}
        )
        log = self.env["webhook.logging"].search(
            [("webhook", "ilike", "Test outgoing webhook on updated partner")], limit=1
        )
        self.assertTrue(log)
        self.assertEqual(
            log.body,
            ustr(
                '{"name": "Test Partner 1", "email": "test.partner1@test.example.com"}'
            ),
        )

        test_partner_1.name = "Test Partner 1-1"
        log = self.env["webhook.logging"].search(
            [("webhook", "ilike", "Test outgoing webhook on updated partner")], limit=1
        )
        self.assertEqual(
            log.body,
            ustr(
                '{"name": "Test Partner 1-1", "email": "test.partner1@test.example.com"}'
            ),
        )

        test_automation.unlink()
        self.env["webhook.logging"].search([]).unlink()

    def test_02_render_request_body(self):
        test_automation = self.env["base.automation"].create(
            {
                "name": "Test outgoing webhook",
                "model_id": self.env.ref("base.model_res_partner").id,
                "type": "ir.actions.server",
                "trigger": "on_create_or_write",
                "trigger_field_ids": [
                    (6, 0, [self.env.ref("base.field_res_partner__name").id])
                ],
                "state": "custom_webhook",
                "endpoint": "https://httpbin.org/post",
                "request_method": "post",
                "request_type": "request",
                "log_webhook_calls": False,
                "active": True,
                "body_template": '{"name": "{{record.name}}", "email": "{{record.email}}"}',
            }
        )
        webhook_action = test_automation.action_server_id
        test_partner_2 = self.env["res.partner"].create(
            {"name": "Test Partner 2", "email": "test.partner2@test.example.com"}
        )
        body_string = webhook_action._prepare_data_for_post_request(test_partner_2, {})
        self.assertEqual(
            body_string,
            (b'{"name": "Test Partner 2", "email": "test.partner2@test.example.com"}'),
        )
        test_automation.unlink()

    def test_03_timeout_error_handling(self):
        """Test that timeout errors are properly logged"""
        test_automation = self.env["base.automation"].create(
            {
                "name": "Test timeout webhook",
                "model_id": self.env.ref("base.model_res_partner").id,
                "type": "ir.actions.server",
                "trigger": "on_create_or_write",
                "trigger_field_ids": [
                    (6, 0, [self.env.ref("base.field_res_partner__name").id])
                ],
                "state": "custom_webhook",
                "endpoint": "https://httpbin.org/delay/10",
                "request_method": "post",
                "request_type": "request",
                "log_webhook_calls": True,
                "body_template": '{"name": "{{record.name}}"}',
            }
        )

        # Mock requests.post to raise a Timeout exception
        # Also mock the logger to suppress ERROR logs during test
        with mock.patch(
            "odoo.addons.webhook_outgoing.models.ir_action_server.requests.post"
        ) as mock_post, mock.patch(
            "odoo.addons.webhook_outgoing.models.ir_action_server._logger"
        ):
            mock_post.side_effect = requests.exceptions.Timeout("Connection timeout")

            # Create a partner to trigger the webhook
            self.env["res.partner"].create(
                {"name": "Test Timeout Partner", "email": "timeout@test.example.com"}
            )

            # Verify that the webhook log was created with timeout error
            log = self.env["webhook.logging"].search(
                [("webhook", "ilike", "Test timeout webhook")], limit=1
            )
            self.assertTrue(log)
            self.assertIn("timeout", log.response.lower())
            self.assertFalse(log.status)

        test_automation.unlink()
        self.env["webhook.logging"].search([]).unlink()

    def test_04_connection_error_handling(self):
        """Test that connection errors are properly logged"""
        test_automation = self.env["base.automation"].create(
            {
                "name": "Test connection error webhook",
                "model_id": self.env.ref("base.model_res_partner").id,
                "type": "ir.actions.server",
                "trigger": "on_create_or_write",
                "trigger_field_ids": [
                    (6, 0, [self.env.ref("base.field_res_partner__name").id])
                ],
                "state": "custom_webhook",
                "endpoint": "https://invalid-domain-that-does-not-exist.com/webhook",
                "request_method": "post",
                "request_type": "request",
                "log_webhook_calls": True,
                "body_template": '{"name": "{{record.name}}"}',
            }
        )

        # Mock requests.post to raise a ConnectionError
        # Also mock the logger to suppress ERROR logs during test
        with mock.patch(
            "odoo.addons.webhook_outgoing.models.ir_action_server.requests.post"
        ) as mock_post, mock.patch(
            "odoo.addons.webhook_outgoing.models.ir_action_server._logger"
        ):
            mock_post.side_effect = requests.exceptions.ConnectionError(
                "Connection failed"
            )

            # Create a partner to trigger the webhook
            self.env["res.partner"].create(
                {
                    "name": "Test Connection Partner",
                    "email": "connection@test.example.com",
                }
            )

            # Verify that the webhook log was created with connection error
            log = self.env["webhook.logging"].search(
                [("webhook", "ilike", "Test connection error webhook")], limit=1
            )
            self.assertTrue(log)
            self.assertIn("Connection", log.response)
            self.assertFalse(log.status)

        test_automation.unlink()
        self.env["webhook.logging"].search([]).unlink()

    def test_05_http_error_handling(self):
        """Test that HTTP errors (4xx, 5xx) are properly logged"""
        test_automation = self.env["base.automation"].create(
            {
                "name": "Test HTTP error webhook",
                "model_id": self.env.ref("base.model_res_partner").id,
                "type": "ir.actions.server",
                "trigger": "on_create_or_write",
                "trigger_field_ids": [
                    (6, 0, [self.env.ref("base.field_res_partner__name").id])
                ],
                "state": "custom_webhook",
                "endpoint": "https://httpbin.org/status/500",
                "request_method": "post",
                "request_type": "request",
                "log_webhook_calls": True,
                "body_template": '{"name": "{{record.name}}"}',
            }
        )

        # Mock requests.post to return a 500 error
        mock_response = mock.Mock()
        mock_response.status_code = 500
        mock_response.content = b"Internal Server Error"
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "500 Server Error"
        )

        # Mock the logger to suppress ERROR logs during test
        with mock.patch(
            "odoo.addons.webhook_outgoing.models.ir_action_server.requests.post",
            return_value=mock_response,
        ), mock.patch("odoo.addons.webhook_outgoing.models.ir_action_server._logger"):
            # Create a partner to trigger the webhook
            self.env["res.partner"].create(
                {
                    "name": "Test HTTP Error Partner",
                    "email": "httperror@test.example.com",
                }
            )

            # Verify that the webhook log was created with HTTP error
            log = self.env["webhook.logging"].search(
                [("webhook", "ilike", "Test HTTP error webhook")], limit=1
            )
            self.assertTrue(log)
            self.assertEqual(log.status, 500)

        test_automation.unlink()
        self.env["webhook.logging"].search([]).unlink()

    def test_06_get_request(self):
        """Test GET request webhook"""
        test_automation = self.env["base.automation"].create(
            {
                "name": "Test GET webhook",
                "model_id": self.env.ref("base.model_res_partner").id,
                "type": "ir.actions.server",
                "trigger": "on_create_or_write",
                "trigger_field_ids": [
                    (6, 0, [self.env.ref("base.field_res_partner__name").id])
                ],
                "state": "custom_webhook",
                "endpoint": "https://httpbin.org/get",
                "request_method": "get",
                "request_type": "request",
                "log_webhook_calls": True,
                "body_template": '{"name": "{{record.name}}"}',
            }
        )

        # Mock requests.get to return a 200 response
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.content = b'{"success": true}'
        mock_response.raise_for_status.return_value = None

        with mock.patch(
            "odoo.addons.webhook_outgoing.models.ir_action_server.requests.get",
            return_value=mock_response,
        ):
            # Create a partner to trigger the webhook
            self.env["res.partner"].create(
                {"name": "Test GET Partner", "email": "get@test.example.com"}
            )

            # Verify that the webhook log was created
            log = self.env["webhook.logging"].search(
                [("webhook", "ilike", "Test GET webhook")], limit=1
            )
            self.assertTrue(log)
            self.assertEqual(log.status, 200)

        test_automation.unlink()
        self.env["webhook.logging"].search([]).unlink()

    def test_07_graphql_request(self):
        """Test GraphQL request webhook"""
        test_automation = self.env["base.automation"].create(
            {
                "name": "Test GraphQL webhook",
                "model_id": self.env.ref("base.model_res_partner").id,
                "type": "ir.actions.server",
                "trigger": "on_create_or_write",
                "trigger_field_ids": [
                    (6, 0, [self.env.ref("base.field_res_partner__name").id])
                ],
                "state": "custom_webhook",
                "endpoint": "https://httpbin.org/post",
                "request_method": "post",
                "request_type": "graphql",
                "log_webhook_calls": True,
                "body_template": """query {
                    partner(id: {{record.id}}) {
                        name
                    }
                }""",
            }
        )

        webhook_action = test_automation.action_server_id
        test_partner = self.env["res.partner"].create(
            {"name": "Test Partner GraphQL", "email": "test.graphql@example.com"}
        )

        # Verify the GraphQL payload is properly formatted
        body = webhook_action._prepare_data_for_post_graphql(test_partner, {})
        self.assertIn('"query":', body)
        self.assertIn("partner", body)

        test_automation.unlink()
        self.env["webhook.logging"].search([]).unlink()

    def test_08_custom_headers(self):
        """Test webhook with custom headers - JSON format"""
        headers = {
            "Authorization": "Bearer test-token",
            "Content-Type": "application/json",
        }
        test_automation = self.env["base.automation"].create(
            {
                "name": "Test custom headers webhook",
                "model_id": self.env.ref("base.model_res_partner").id,
                "type": "ir.actions.server",
                "trigger": "on_create_or_write",
                "trigger_field_ids": [
                    (6, 0, [self.env.ref("base.field_res_partner__name").id])
                ],
                "state": "custom_webhook",
                "endpoint": "https://httpbin.org/post",
                "request_method": "post",
                "request_type": "request",
                "log_webhook_calls": True,
                "headers": json.dumps(headers),
                "body_template": '{"name": "{{record.name}}"}',
            }
        )

        webhook_action = test_automation.action_server_id
        headers_dict = webhook_action._get_webhook_headers()
        self.assertIsInstance(headers_dict, dict)
        self.assertEqual(headers_dict.get("Authorization"), "Bearer test-token")
        self.assertEqual(headers_dict.get("Content-Type"), "application/json")

        test_automation.unlink()

    def test_09_headers_python_dict_format(self):
        """Test webhook headers with Python dict literal (single quotes)"""
        webhook_action = self.env["ir.actions.server"].create(
            {
                "name": "Test Python dict headers",
                "model_id": self.env.ref("base.model_res_partner").id,
                "state": "custom_webhook",
                "endpoint": "https://httpbin.org/post",
                "headers": "{'Authorization': 'Bearer token', 'X-Custom': 'value'}",
            }
        )

        headers_dict = webhook_action._get_webhook_headers()
        self.assertIsInstance(headers_dict, dict)
        self.assertEqual(headers_dict.get("Authorization"), "Bearer token")
        self.assertEqual(headers_dict.get("X-Custom"), "value")

    def test_10_headers_empty_cases(self):
        """Test webhook headers with empty/whitespace values"""
        # Test with empty string
        webhook_action = self.env["ir.actions.server"].create(
            {
                "name": "Test empty headers",
                "model_id": self.env.ref("base.model_res_partner").id,
                "state": "custom_webhook",
                "endpoint": "https://httpbin.org/post",
                "headers": "",
            }
        )
        headers_dict = webhook_action._get_webhook_headers()
        self.assertEqual(headers_dict, {})

        # Test with whitespace only
        webhook_action.headers = "   "
        headers_dict = webhook_action._get_webhook_headers()
        self.assertEqual(headers_dict, {})

        # Test with default value
        webhook_action.headers = "{}"
        headers_dict = webhook_action._get_webhook_headers()
        self.assertEqual(headers_dict, {})

    def test_11_headers_invalid_format(self):
        """Test webhook headers with invalid format returns empty dict"""
        webhook_action = self.env["ir.actions.server"].create(
            {
                "name": "Test invalid headers",
                "model_id": self.env.ref("base.model_res_partner").id,
                "state": "custom_webhook",
                "endpoint": "https://httpbin.org/post",
                "headers": "not a valid dict or json",
            }
        )

        # Should return empty dict and log error
        headers_dict = webhook_action._get_webhook_headers()
        self.assertEqual(headers_dict, {})

    def test_12_headers_non_dict_value(self):
        """Test webhook headers with non-dict value returns empty dict"""
        webhook_action = self.env["ir.actions.server"].create(
            {
                "name": "Test non-dict headers",
                "model_id": self.env.ref("base.model_res_partner").id,
                "state": "custom_webhook",
                "endpoint": "https://httpbin.org/post",
                "headers": "['list', 'not', 'dict']",
            }
        )

        # Should return empty dict and log warning
        headers_dict = webhook_action._get_webhook_headers()
        self.assertEqual(headers_dict, {})
