# Contact Us API Guide

## Overview
Contact form API with separate public and admin endpoints:
- **Public:** POST only - Submit contact form (no auth required)
- **Admin:** GET/PATCH - View and manage messages (auth required)

---

## Public API - Submit Contact Form

### Endpoint
```
POST /api/v1/contact-us/
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
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+977-9812345678",
  "subject": "Product Inquiry",
  "message": "I'm interested in your wool slippers. Do you ship internationally?"
}
```

**Field Requirements:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Full name |
| `email` | string | Yes | Valid email address |
| `phone` | string | No | Phone number (optional) |
| `subject` | string | Yes | Message subject |
| `message` | text | Yes | Message content (min 10 chars) |

### Response

**Success (201 Created):**
```json
{
  "success": true,
  "message": "Thank you for contacting us. We'll get back to you soon.",
  "data": {
    "id": "uuid",
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+977-9812345678",
    "subject": "Product Inquiry",
    "message": "I'm interested in your wool slippers...",
    "status": "NEW",
    "admin_notes": "",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

**Error - Validation (400 Bad Request):**
```json
{
  "success": false,
  "message": "Validation error.",
  "errors": {
    "email": ["Enter a valid email address."],
    "message": ["Message must be at least 10 characters long."]
  }
}
```

---

## Admin API - List Messages

### Endpoint
```
GET /api/v1/admin/contact-messages/
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
| `status` | string | Filter by status (NEW, IN_PROGRESS, RESOLVED, CLOSED) |

### Response

**Success (200 OK):**
```json
{
  "success": true,
  "message": "Contact messages retrieved successfully.",
  "data": [
    {
      "id": "uuid-1",
      "name": "John Doe",
      "email": "john@example.com",
      "phone": "+977-9812345678",
      "subject": "Product Inquiry",
      "message": "I'm interested in your wool slippers...",
      "status": "NEW",
      "admin_notes": "",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": "uuid-2",
      "name": "Jane Smith",
      "email": "jane@example.com",
      "phone": "",
      "subject": "Shipping Question",
      "message": "How long does shipping take to the US?",
      "status": "RESOLVED",
      "admin_notes": "Responded via email on 2024-01-14",
      "created_at": "2024-01-14T09:20:00Z",
      "updated_at": "2024-01-14T15:45:00Z"
    }
  ]
}
```

**Filter by Status:**
```
GET /api/v1/admin/contact-messages/?status=NEW
```

Returns only messages with NEW status.

---

## Admin API - View/Update Message

### Endpoint
```
GET    /api/v1/admin/contact-messages/{id}/
PATCH  /api/v1/admin/contact-messages/{id}/
PUT    /api/v1/admin/contact-messages/{id}/
```

**Authentication:** Required (Admin only)

### GET - View Single Message

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Contact message retrieved successfully.",
  "data": {
    "id": "uuid",
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+977-9812345678",
    "subject": "Product Inquiry",
    "message": "Full message content here...",
    "status": "NEW",
    "admin_notes": "",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

### PATCH - Update Status/Notes

**Request:**
```json
{
  "status": "IN_PROGRESS",
  "admin_notes": "Following up with customer via email"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Contact message updated successfully.",
  "data": {
    "id": "uuid",
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+977-9812345678",
    "subject": "Product Inquiry",
    "message": "Full message content here...",
    "status": "IN_PROGRESS",
    "admin_notes": "Following up with customer via email",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T11:00:00Z"
  }
}
```

---

## Status Types

| Status | Description |
|--------|-------------|
| `NEW` | New message (default) |
| `IN_PROGRESS` | Being handled |
| `RESOLVED` | Issue resolved |
| `CLOSED` | Conversation closed |

---

## Frontend Examples

### 1. Contact Form (Public)

```jsx
import { useState } from 'react';

function ContactForm() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    subject: '',
    message: ''
  });
  const [status, setStatus] = useState('idle'); // idle, loading, success, error
  const [message, setMessage] = useState('');

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus('loading');
    setMessage('');

    try {
      const response = await fetch('/api/v1/contact-us/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (response.ok) {
        setStatus('success');
        setMessage(data.message);
        // Reset form
        setFormData({
          name: '',
          email: '',
          phone: '',
          subject: '',
          message: ''
        });
      } else {
        setStatus('error');
        // Display validation errors
        const errors = Object.values(data.errors || {}).flat();
        setMessage(errors.join(', '));
      }
    } catch (error) {
      setStatus('error');
      setMessage('Network error. Please try again.');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Contact Us</h2>
      
      <input
        type="text"
        name="name"
        placeholder="Your Name *"
        value={formData.name}
        onChange={handleChange}
        required
      />
      
      <input
        type="email"
        name="email"
        placeholder="Your Email *"
        value={formData.email}
        onChange={handleChange}
        required
      />
      
      <input
        type="tel"
        name="phone"
        placeholder="Phone Number (optional)"
        value={formData.phone}
        onChange={handleChange}
      />
      
      <input
        type="text"
        name="subject"
        placeholder="Subject *"
        value={formData.subject}
        onChange={handleChange}
        required
      />
      
      <textarea
        name="message"
        placeholder="Your Message * (min 10 characters)"
        value={formData.message}
        onChange={handleChange}
        rows="5"
        required
        minLength="10"
      />
      
      <button type="submit" disabled={status === 'loading'}>
        {status === 'loading' ? 'Sending...' : 'Send Message'}
      </button>
      
      {status === 'success' && (
        <div className="success-message">{message}</div>
      )}
      
      {status === 'error' && (
        <div className="error-message">{message}</div>
      )}
    </form>
  );
}
```

### 2. Admin - Message List

```jsx
import { useEffect, useState } from 'react';

function ContactMessagesList() {
  const [messages, setMessages] = useState([]);
  const [filter, setFilter] = useState('all'); // all, NEW, IN_PROGRESS, RESOLVED, CLOSED
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMessages();
  }, [filter]);

  const fetchMessages = async () => {
    setLoading(true);
    
    let url = '/api/v1/admin/contact-messages/';
    if (filter !== 'all') {
      url += `?status=${filter}`;
    }

    try {
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      const data = await response.json();
      setMessages(data.data);
    } catch (error) {
      console.error('Failed to fetch messages:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      'NEW': 'red',
      'IN_PROGRESS': 'orange',
      'RESOLVED': 'green',
      'CLOSED': 'gray'
    };
    return colors[status] || 'black';
  };

  return (
    <div>
      <h2>Contact Messages ({messages.length})</h2>
      
      <div className="filters">
        <button onClick={() => setFilter('all')}>All</button>
        <button onClick={() => setFilter('NEW')}>New</button>
        <button onClick={() => setFilter('IN_PROGRESS')}>In Progress</button>
        <button onClick={() => setFilter('RESOLVED')}>Resolved</button>
        <button onClick={() => setFilter('CLOSED')}>Closed</button>
      </div>

      {loading ? (
        <p>Loading...</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Subject</th>
              <th>Status</th>
              <th>Date</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {messages.map(msg => (
              <tr key={msg.id}>
                <td>{msg.name}</td>
                <td>{msg.email}</td>
                <td>{msg.subject}</td>
                <td style={{ color: getStatusColor(msg.status) }}>
                  {msg.status}
                </td>
                <td>{new Date(msg.created_at).toLocaleDateString()}</td>
                <td>
                  <button onClick={() => viewMessage(msg.id)}>View</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
```

### 3. Admin - Update Message Status

```jsx
function MessageDetail({ messageId }) {
  const [message, setMessage] = useState(null);
  const [status, setStatus] = useState('');
  const [adminNotes, setAdminNotes] = useState('');

  useEffect(() => {
    fetchMessage();
  }, [messageId]);

  const fetchMessage = async () => {
    const response = await fetch(
      `/api/v1/admin/contact-messages/${messageId}/`,
      {
        headers: { 'Authorization': `Bearer ${token}` }
      }
    );
    const data = await response.json();
    setMessage(data.data);
    setStatus(data.data.status);
    setAdminNotes(data.data.admin_notes);
  };

  const handleUpdate = async () => {
    const response = await fetch(
      `/api/v1/admin/contact-messages/${messageId}/`,
      {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status, admin_notes: adminNotes })
      }
    );

    if (response.ok) {
      alert('Message updated successfully');
      fetchMessage();
    }
  };

  if (!message) return <div>Loading...</div>;

  return (
    <div>
      <h2>Contact Message Details</h2>
      
      <div>
        <strong>From:</strong> {message.name} ({message.email})
      </div>
      {message.phone && (
        <div><strong>Phone:</strong> {message.phone}</div>
      )}
      <div><strong>Subject:</strong> {message.subject}</div>
      <div><strong>Date:</strong> {new Date(message.created_at).toLocaleString()}</div>
      
      <div>
        <strong>Message:</strong>
        <p>{message.message}</p>
      </div>
      
      <hr />
      
      <div>
        <label>
          Status:
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="NEW">New</option>
            <option value="IN_PROGRESS">In Progress</option>
            <option value="RESOLVED">Resolved</option>
            <option value="CLOSED">Closed</option>
          </select>
        </label>
      </div>
      
      <div>
        <label>
          Admin Notes:
          <textarea
            value={adminNotes}
            onChange={(e) => setAdminNotes(e.target.value)}
            rows="4"
            placeholder="Internal notes..."
          />
        </label>
      </div>
      
      <button onClick={handleUpdate}>Update Message</button>
    </div>
  );
}
```

---

## Django Admin

Messages can also be managed via Django admin at:
```
/admin/cms/contactmessage/
```

**Features:**
- View all messages
- Filter by status and date
- Search by name, email, subject, message
- Update status and add admin notes
- Read-only contact info (can't edit submitted data)
- Can't manually create (only via API)

---

## Use Cases

### 1. Customer Support
- Receive inquiries from website
- Track message status
- Add internal notes
- Follow up with customers

### 2. Sales Inquiries
- Product questions
- Bulk order requests
- Custom order inquiries
- Partnership requests

### 3. General Contact
- Feedback
- Complaints
- Suggestions
- Questions

### 4. Issue Tracking
- Mark messages as IN_PROGRESS
- Add notes about actions taken
- Mark as RESOLVED when complete
- Close old conversations

---

## Email Integration (Optional Future Enhancement)

You could add email notifications:

1. **Send confirmation email** to customer after submission
2. **Notify admin** when new message arrives
3. **Track email conversations** linked to message ID

---

## Database Schema

```sql
CREATE TABLE cms_contact_message (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    subject VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'NEW',
    admin_notes TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_contact_message_status ON cms_contact_message(status);
CREATE INDEX idx_contact_message_created_at ON cms_contact_message(created_at DESC);
CREATE INDEX idx_contact_message_email ON cms_contact_message(email);
```

---

## Summary

### Endpoints
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/contact-us/` | None | Submit contact form |
| GET | `/api/v1/admin/contact-messages/` | Admin | List all messages |
| GET | `/api/v1/admin/contact-messages/{id}/` | Admin | View single message |
| PATCH | `/api/v1/admin/contact-messages/{id}/` | Admin | Update status/notes |

### Key Features
✅ Public contact form (no auth)  
✅ Email validation  
✅ Message length validation (min 10 chars)  
✅ Status tracking (NEW, IN_PROGRESS, RESOLVED, CLOSED)  
✅ Admin notes for internal use  
✅ Filter by status  
✅ Search by name/email/subject  
✅ Django admin integration  

Perfect for customer support and inquiries! 🎉
