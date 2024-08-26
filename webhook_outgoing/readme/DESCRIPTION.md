This module allows creating automations that send webhook/HTTP requests to external systems.

## Key Features

* **Integration with Automated Actions**: Extends Odoo's automated actions with webhook capabilities
* **Jinja Template Support**: Render request bodies dynamically using Jinja2 templating engine
* **Queue Job Support**: Execute webhooks asynchronously using queue_job for better performance
* **Multiple Request Types**: Support for standard HTTP, GraphQL, and Slack webhooks
* **Flexible Configuration**: Customize endpoints, headers, body templates, and request methods
* **Request Logging**: Optional logging of webhook calls for debugging and troubleshooting

## Use Cases

* Send notifications to Slack, Discord, or other chat platforms when records are created/updated
* Trigger external API calls when business events occur in Odoo
* Integrate with third-party services without custom code
* Synchronize data with external systems in real-time
