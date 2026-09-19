# Subscription API Guide

## Overview
Newsletter subscription API with two endpoints:
- **Public:** POST only - Subscribe to newsletter (no auth required)
- **Admin:** GET only - View all subscriptions (auth required)

---

## Public API - Subscribe

### Endpoint
```
POST /api/v1/subscription/
```

**Authentication:** None (public endpoint)

### Request

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "email": "customer@example.com"
}
```

### Response

**Success (201 Created):**
```json
{
  "success": true,
  "message": "Successfully subscribed to newsletter.",
  "data": {
    "id": "uuid",
    "email": "customer@example.com",
    "is_active": true,
    "subscribed_at": "2024-01-15T10:30:00Z",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

**Error - Already Subscribed (400 Bad Request):**
```json
{
  "success": false,
  "message": "Validation error.",
  "errors": {
    "email": ["This email is already subscribed."]
  }
}
```

**Error - Invalid Email (400 Bad Request):**
```json
{
  "success": false,
  "message": "Validation error.",
  "errors": {
    "email": ["Enter a valid email address."]
  }
}
```

### Behavior

1. **New Subscription:** Creates new subscription record
2. **Reactivation:** If email exists but inactive, reactivates it
3. **Duplicate Prevention:** Returns error if email already active
4. **Email Validation:** Django's built-in email validation

---

## Admin API - List Subscriptions

### Endpoint
```
GET /api/v1/admin/subscriptions/
```

**Authentication:** Required (Admin only)

### Request

**Headers:**
```
Authorization: Bearer YOUR_JWT_TOKEN
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `is_active` | boolean | Filter by active status (true/false) |

### Response

**Success (200 OK):**
```json
{
  "success": true,
  "message": "Subscriptions retrieved successfully.",
  "data": [
    {
      "id": "uuid-1",
      "email": "customer1@example.com",
      "is_active": true,
      "subscribed_at": "2024-01-15T10:30:00Z",
      "created_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": "uuid-2",
      "email": "customer2@example.com",
      "is_active": true,
      "subscribed_at": "2024-01-14T09:20:00Z",
      "created_at": "2024-01-14T09:20:00Z"
    },
    {
      "id": "uuid-3",
      "email": "inactive@example.com",
      "is_active": false,
      "subscribed_at": "2024-01-10T15:45:00Z",
      "created_at": "2024-01-10T15:45:00Z"
    }
  ]
}
```

**Filter by Active:**
```
GET /api/v1/admin/subscriptions/?is_active=true
```

Returns only active subscriptions.

---

## Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `id` | uuid | Unique subscription ID |
| `email` | string | Subscriber email (unique) |
| `is_active` | boolean | Subscription status |
| `subscribed_at` | datetime | When they subscribed |
| `created_at` | datetime | Record creation time |

---

## Frontend Examples

### 1. Newsletter Signup Form (Public)

```jsx
import { useState } from 'react';

function NewsletterSignup() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      const response = await fetch('/api/v1/subscription/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();

      if (response.ok) {
        setMessage('Thank you for subscribing!');
        setEmail(''); // Clear form
      } else {
        // Handle validation errors
        const errorMessage = data.errors?.email?.[0] || 'Subscription failed';
        setMessage(errorMessage);
      }
    } catch (error) {
      setMessage('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="email"
        placeholder="Enter your email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
      />
      <button type="submit" disabled={loading}>
        {loading ? 'Subscribing...' : 'Subscribe'}
      </button>
      {message && <p>{message}</p>}
    </form>
  );
}
```

### 2. Admin - View Subscriptions

```jsx
import { useEffect, useState } from 'react';

function SubscriptionsList() {
  const [subscriptions, setSubscriptions] = useState([]);
  const [filter, setFilter] = useState('all'); // 'all', 'active', 'inactive'
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSubscriptions();
  }, [filter]);

  const fetchSubscriptions = async () => {
    setLoading(true);
    
    let url = '/api/v1/admin/subscriptions/';
    if (filter === 'active') {
      url += '?is_active=true';
    } else if (filter === 'inactive') {
      url += '?is_active=false';
    }

    try {
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      const data = await response.json();
      setSubscriptions(data.data);
    } catch (error) {
      console.error('Failed to fetch subscriptions:', error);
    } finally {
      setLoading(false);
    }
  };

  const exportToCSV = () => {
    const csv = subscriptions
      .map(sub => `${sub.email},${sub.subscribed_at}`)
      .join('\n');
    
    const blob = new Blob([`Email,Subscribed At\n${csv}`], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'subscriptions.csv';
    a.click();
  };

  return (
    <div>
      <h2>Newsletter Subscriptions ({subscriptions.length})</h2>
      
      <div>
        <button onClick={() => setFilter('all')}>All</button>
        <button onClick={() => setFilter('active')}>Active</button>
        <button onClick={() => setFilter('inactive')}>Inactive</button>
        <button onClick={exportToCSV}>Export CSV</button>
      </div>

      {loading ? (
        <p>Loading...</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Email</th>
              <th>Status</th>
              <th>Subscribed At</th>
            </tr>
          </thead>
          <tbody>
            {subscriptions.map(sub => (
              <tr key={sub.id}>
                <td>{sub.email}</td>
                <td>{sub.is_active ? 'Active' : 'Inactive'}</td>
                <td>{new Date(sub.subscribed_at).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
```

### 3. Simple Footer Newsletter Form

```html
<!-- HTML -->
<footer>
  <form id="newsletter-form">
    <h3>Subscribe to Our Newsletter</h3>
    <input 
      type="email" 
      id="newsletter-email" 
      placeholder="Your email" 
      required 
    />
    <button type="submit">Subscribe</button>
    <p id="newsletter-message"></p>
  </form>
</footer>

<script>
document.getElementById('newsletter-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const email = document.getElementById('newsletter-email').value;
  const messageEl = document.getElementById('newsletter-message');
  
  try {
    const response = await fetch('/api/v1/subscription/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });
    
    const data = await response.json();
    
    if (response.ok) {
      messageEl.textContent = 'Thanks for subscribing!';
      messageEl.style.color = 'green';
      document.getElementById('newsletter-email').value = '';
    } else {
      messageEl.textContent = data.errors?.email?.[0] || 'Error subscribing';
      messageEl.style.color = 'red';
    }
  } catch (error) {
    messageEl.textContent = 'Network error. Please try again.';
    messageEl.style.color = 'red';
  }
});
</script>
```

---

## Django Admin

Subscriptions can also be managed via Django admin at:
```
/admin/cms/subscription/
```

**Features:**
- View all subscriptions
- Filter by active/inactive
- Search by email
- Export to CSV (using Django admin actions)
- Manually activate/deactivate subscriptions

---

## Database Schema

```sql
CREATE TABLE cms_subscription (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    subscribed_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_subscription_active ON cms_subscription(is_active);
CREATE INDEX idx_subscription_subscribed_at ON cms_subscription(subscribed_at DESC);
```

---

## Use Cases

### 1. Newsletter Signup
- Add form to footer
- Collect emails for marketing
- No account required

### 2. Email Marketing
- Export subscriber list
- Import to email marketing tool (Mailchimp, SendGrid, etc.)
- Send newsletters

### 3. Subscriber Management
- View all subscribers
- Filter active/inactive
- Track subscription dates
- Reactivate unsubscribed users

### 4. Analytics
- Count total subscribers
- Track subscription growth
- Monitor inactive subscriptions

---

## Security Notes

✅ **Email validation** - Django's built-in email validator  
✅ **Duplicate prevention** - Unique constraint on email  
✅ **No auth required** - Public can subscribe  
✅ **Admin only viewing** - Only admins can see subscriber list  
✅ **No personal data** - Only email stored  
✅ **GDPR ready** - Easy to delete/export data  

---

## Future Enhancements

Optional features you could add:

1. **Unsubscribe endpoint** - `POST /api/v1/subscription/unsubscribe/`
2. **Email verification** - Send confirmation email
3. **Preferences** - Store newsletter preferences
4. **Double opt-in** - Require email confirmation
5. **Export functionality** - Add export endpoint for admin
6. **Webhook integration** - Notify external services on new subscription

---

## Summary

### Endpoints
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/subscription/` | None | Subscribe to newsletter |
| GET | `/api/v1/admin/subscriptions/` | Admin | List all subscriptions |

### Key Features
✅ Simple email-only subscription  
✅ Duplicate prevention  
✅ Reactivation support  
✅ Admin list with filtering  
✅ No authentication for public  
✅ Ready for email marketing integration  

Perfect for newsletter signups! 🎉
