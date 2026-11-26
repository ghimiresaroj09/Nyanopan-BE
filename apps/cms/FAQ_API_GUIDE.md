# FAQ API

## Public endpoints

These endpoints are read-only and do not require authentication.

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/v1/faq-categories/` | List categories with their FAQs |
| GET | `/api/v1/faq-categories/{id}/` | Retrieve a category with its FAQs |
| GET | `/api/v1/faqs/` | List all FAQs |
| GET | `/api/v1/faqs/{id}/` | Retrieve one FAQ |
| GET | `/api/v1/faqs/?category={category_id}` | Filter FAQs by category |

Category response data contains its ID, name, and nested questions:

```json
{
  "success": true,
  "message": "FAQ categories retrieved successfully.",
  "data": [
    {
      "id": "category-uuid",
      "name": "Orders",
      "faqs": [
        {
          "id": "faq-uuid",
          "question": "How can I place an order?",
          "answer": "Add your items to the cart and complete checkout."
        }
      ]
    }
  ]
}
```

## Admin endpoints

All admin endpoints require staff authentication and support create, list,
retrieve, update, partial update, and delete operations.

| Method | Endpoint | Description |
| --- | --- | --- |
| GET, POST | `/api/v1/admin/faq-categories/` | List or create categories |
| GET, PUT, PATCH, DELETE | `/api/v1/admin/faq-categories/{id}/` | Manage a category |
| GET, POST | `/api/v1/admin/faqs/` | List or create FAQs |
| GET, PUT, PATCH, DELETE | `/api/v1/admin/faqs/{id}/` | Manage an FAQ |
| GET | `/api/v1/admin/faqs/?category={category_id}` | Filter FAQs by category |

Create a category:

```json
{ "name": "Orders" }
```

Create an FAQ using the category UUID:

```json
{
  "category": "category-uuid",
  "question": "How can I place an order?",
  "answer": "Add your items to the cart and complete checkout."
}
```
