Navigate to **Settings > Technical > Automation > Automated Actions** to configure webhook automations.

## Basic Configuration

1. **Create a New Automated Action**
   - Click "Create"
   - Set the **Model** (e.g., Sale Order, Contact, etc.)
   - Define the **Trigger** (On Creation, On Update, etc.)
   - Set **Action To Do** to "Custom Webhook"

2. **Configure Webhook Details**

   **Endpoint**
   - Enter the full URL of the webhook endpoint
   - Example: `https://hooks.slack.com/services/YOUR/WEBHOOK/URL`

   **Request Method**
   - Choose between GET or POST
   - Most webhooks use POST

   **Request Type**
   - **HTTP Request**: Standard REST API calls
   - **GraphQL**: For GraphQL APIs
   - **Slack**: Optimized for Slack webhooks

3. **Headers Configuration**

   Add any required headers in JSON format:
   ```json
   {
       "Content-Type": "application/json",
       "Authorization": "Bearer YOUR_TOKEN"
   }
   ```

4. **Body Template**

   Use Jinja2 syntax to create dynamic payloads:
   ```jinja
   {
       "id": {{ record.id }},
       "name": "{{ record.name }}",
       "email": "{{ record.email }}",
       "created_date": "{{ record.create_date }}"
   }
   ```

   Available variables:
   - `record`: The record that triggered the action
   - Any field from the record model

## Asynchronous Execution

Enable **Delay Execution** to run webhooks in the background using queue jobs:
- Check "Delay Execution"
- Set **Delay ETA (s)** to specify how many seconds to wait before execution

## Webhook Logging

Enable **Log Calls** to track all webhook requests and responses for debugging:
- Check "Log Calls"
- View logs in **Settings > Technical > Webhook Logging**

## Domain Filters

Use the **Apply on** field to filter which records trigger the webhook based on domain conditions.

## Security Considerations

* Use HTTPS endpoints for secure communication
* Regularly review webhook logs for suspicious activity
