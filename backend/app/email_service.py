from dataclasses import dataclass

import httpx


@dataclass
class EmailProvider:
    name: str
    api_url: str
    auth_header: str

    def build_payload(self, from_email: str, to_email: str, subject: str, html_body: str) -> dict:
        if self.name == "brevo":
            return {
                "sender": {"email": from_email},
                "to": [{"email": to_email}],
                "subject": subject,
                "htmlContent": html_body,
            }
        elif self.name == "mailjet":
            return {
                "Messages": [{
                    "From": {"Email": from_email},
                    "To": [{"Email": to_email}],
                    "Subject": subject,
                    "HTMLPart": html_body,
                }]
            }
        raise ValueError(f"Unknown provider: {self.name}")

    def build_headers(self, api_key: str) -> dict:
        if self.name == "brevo":
            return {
                "api-key": api_key,
                "accept": "application/json",
                "content-type": "application/json",
            }
        elif self.name == "mailjet":
            return {
                "accept": "application/json",
                "content-type": "application/json",
            }
        raise ValueError(f"Unknown provider: {self.name}")


PROVIDERS = {
    "brevo": EmailProvider(
        name="brevo",
        api_url="https://api.brevo.com/v3/smtp/email",
        auth_header="api-key",
    ),
    "mailjet": EmailProvider(
        name="mailjet",
        api_url="https://api.mailjet.com/v3.1/send",
        auth_header="Authorization",
    ),
}


def get_email_provider(name: str) -> EmailProvider:
    provider = PROVIDERS.get(name)
    if not provider:
        raise ValueError(f"Unknown email provider: {name}")
    return provider


async def send_download_email(
    provider_name: str,
    api_key: str,
    secret_key: str,
    from_email: str,
    to_email: str,
    download_url: str,
    filename: str,
) -> bool:
    provider = get_email_provider(provider_name)

    if provider_name == "mailjet" and not secret_key:
        raise ValueError("EMAIL_SECRET_KEY is required for Mailjet.")

    subject = "Your CSV is ready to download"
    html_body = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
        <h2>Your CSV is ready!</h2>
        <p>The file <strong>{filename}</strong> has been converted to CSV.</p>
        <p>
            <a href="{download_url}"
               style="display: inline-block; padding: 12px 24px; background: #2563eb;
                      color: white; text-decoration: none; border-radius: 6px;">
                Download CSV
            </a>
        </p>
        <p style="color: #666; font-size: 14px;">This link expires in 24 hours.</p>
    </div>
    """

    payload = provider.build_payload(from_email, to_email, subject, html_body)
    headers = provider.build_headers(api_key)

    async with httpx.AsyncClient() as client:
        request_kwargs = {"json": payload, "headers": headers}
        if provider_name == "mailjet":
            request_kwargs["auth"] = (api_key, secret_key)
        response = await client.post(provider.api_url, **request_kwargs)
        return response.status_code in (200, 201, 202)
