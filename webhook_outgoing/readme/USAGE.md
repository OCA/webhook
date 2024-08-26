## Example 1: Send Slack Notification on New Sale Order

1. Go to **Settings > Technical > Automation > Automated Actions**
2. Click **Create** and configure:
   - **Name**: "Notify Slack on New Sale"
   - **Model**: Sale Order
   - **Trigger**: On Creation
   - **Action To Do**: Custom Webhook

3. Configure the webhook:
   - **Endpoint**: `https://hooks.slack.com/services/YOUR/WEBHOOK/URL`
   - **Request Method**: POST
   - **Request Type**: Slack
   - **Headers**:
     ```json
     {
         "Content-Type": "application/json"
     }
     ```
   - **Body Template**:
     ```jinja
     {
         "text": "New sale order created!",
         "attachments": [{
             "color": "good",
             "fields": [
                 {
                     "title": "Order Number",
                     "value": "{{ record.name }}",
                     "short": true
                 },
                 {
                     "title": "Customer",
                     "value": "{{ record.partner_id.name }}",
                     "short": true
                 },
                 {
                     "title": "Amount",
                     "value": "${{ record.amount_total }}",
                     "short": true
                 }
             ]
         }]
     }
     ```

## Example 2: POST to External API

Configure a webhook to send contact data to an external CRM:

- **Endpoint**: `https://api.example.com/contacts`
- **Request Method**: POST
- **Request Type**: HTTP Request
- **Headers**:
  ```json
  {
      "Content-Type": "application/json",
      "Authorization": "Bearer YOUR_API_TOKEN"
  }
  ```
- **Body Template**:
  ```jinja
  {
      "external_id": {{ record.id }},
      "first_name": "{{ record.name }}",
      "email": "{{ record.email }}",
      "phone": "{{ record.phone }}",
      "company": "{{ record.company_id.name if record.company_id else '' }}"
  }
  ```

## Example 3: GraphQL Query

Send a GraphQL mutation when a product is updated:

- **Endpoint**: `https://api.example.com/graphql`
- **Request Method**: POST
- **Request Type**: GraphQL
- **Body Template**:
  ```jinja
  mutation {
      updateProduct(input: {
          id: {{ record.id }}
          name: {{ record.name | escape }}
          price: {{ record.list_price }}
      }) {
          id
          statusCode
      }
  }
  ```

## Using Jinja2 Templates

**Available Variables**

- `record`: The current record triggering the action
- Access related fields using dot notation: `record.partner_id.name`

**Common Jinja2 Filters**

```jinja
{# String manipulation #}
{{ record.name | upper }}
{{ record.description | truncate(100) }}

{# Default values #}
{{ record.email | default('no-email@example.com') }}

{# Conditional rendering #}
{% if record.state == 'sale' %}
    "status": "confirmed"
{% else %}
    "status": "draft"
{% endif %}

{# Escaping for GraphQL #}
{{ record.name | escape }}
```