## Prerequisites

This module requires the following dependencies:

* `queue_job` - For asynchronous webhook execution. Please configure `queue_job` properly
before installation.
* Python `jinja2` library - For template rendering

## Installation Steps

1. Install the `queue_job` module from OCA/queue if you want to use asynchronous execution:
   - Available at: https://github.com/OCA/queue

3. If you haven't installed `queue_job` before installing this module, you will need to
restart the server to have `queue_job` loaded.

## Post-Installation

After installation, the module adds a new "Custom Webhook" action type to Automated Actions.
No additional configuration is required to start using the module.
