# Security

Do not commit secrets, webhook URLs, private contact data, or Vercel environment files.

For production, configure a strong random `SECRET_KEY` and use HTTPS. Contact submissions are validated server-side and, when configured, are forwarded to the private `CONTACT_WEBHOOK_URL`; they are not stored by this application.

If you discover a vulnerability, report it privately to the project owner instead of opening a public issue containing exploit details or secrets.
