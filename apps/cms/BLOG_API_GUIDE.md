# Blog API

Blog content supports multipart image uploads. The `content` field stores the
HTML produced by the rich-text editor, similar to the existing policy content.
Tags may be sent as a JSON array or as comma-separated text in multipart forms.
SEO fields are editable on the admin API and returned with public blogs.

## Public endpoints

Public endpoints are read-only and return published blogs only.

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/v1/blog-categories/` | List categories with published blog counts |
| GET | `/api/v1/blog-categories/{id}/` | Retrieve a category and its blog count |
| GET | `/api/v1/blogs/` | List published blogs |
| GET | `/api/v1/blogs/{id}/` | Retrieve a published blog; increments its view count |

Blog list filters:

| Query parameter | Meaning |
| --- | --- |
| `category={uuid}` | Filter by category |
| `min_views={number}` | Minimum view count |
| `max_views={number}` | Maximum view count |
| `is_featured=true\|false` | Filter featured blogs |
| `ordering=views` or `ordering=-views` | Order by view count |
| `ordering=created_at` or `ordering=-created_at` | Order by date |

Public responses contain the article fields and SEO metadata: `slug`, `excerpt`,
`meta_title`, `meta_description`, `meta_keywords`, `canonical_url`, `meta_robots`,
`og_title`, `og_description`, `og_url`, `og_image`, `twitter_card`, `twitter_title`,
`twitter_description`, and `twitter_image`. When optional title, description, or
social image fields are empty, responses fall back to the blog title, excerpt or
plain-text content, and main image respectively.

## Admin endpoints

All admin endpoints require staff authentication and support CRUD operations.

| Method | Endpoint | Description |
| --- | --- | --- |
| GET, POST | `/api/v1/admin/blog-categories/` | List or create categories |
| GET, PUT, PATCH, DELETE | `/api/v1/admin/blog-categories/{id}/` | Manage a category |
| GET, POST | `/api/v1/admin/blogs/` | List or create blogs |
| GET, PUT, PATCH, DELETE | `/api/v1/admin/blogs/{id}/` | Manage a blog |

Create a category:

```json
{ "name": "Materials and Care" }
```

Create a blog with `multipart/form-data` fields:

```text
title: Caring for wool felt
category: <category UUID>
image: <image file>
content: <HTML from the rich-text editor>
tags: ["care", "wool"]
is_featured: false
is_published: true
slug: caring-for-wool-felt
excerpt: Simple tips to help wool felt last longer.
meta_title: How to Care for Wool Felt | Nyanopan
meta_description: Learn how to clean and care for wool felt products.
meta_keywords: ["wool felt", "care"]
canonical_url: https://example.com/blog/caring-for-wool-felt
meta_robots: index, follow, max-image-preview:large
og_title: Caring for wool felt
og_description: Keep your wool felt products in great condition.
og_url: https://example.com/blog/caring-for-wool-felt
canonical_url: https://example.com/blog/caring-for-wool-felt
og_image: <optional social image file>
twitter_card: summary_large_image
twitter_title: Caring for wool felt
twitter_description: Simple care tips from Nyanopan.
twitter_image: <optional social image file>
```

Allowed `meta_robots` values are `index, follow`, `noindex, follow`,
`index, nofollow`, `noindex, nofollow`, `max-image-preview:large`, and those
four index/follow combinations with `max-image-preview:large`. Allowed
`twitter_card` values are `summary` and
`summary_large_image`. Slugs are generated from the title when omitted and
made unique automatically.

Blog admin responses also include `updated_at` and the category's name. The
`views` count is read-only and increments when a public blog detail is opened.
