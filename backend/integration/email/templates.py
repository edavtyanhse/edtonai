"""Email HTML templates."""


def render_verification_email(verify_url: str) -> tuple[str, str]:
    """Render verification email. Returns (subject, html_body)."""
    subject = "EdTon.ai — Подтвердите email"
    html = f"""\
    <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto; padding: 32px;">
        <h2 style="color: #1a1a2e;">Добро пожаловать в EdTon.ai!</h2>
        <p>Для завершения регистрации подтвердите ваш email:</p>
        <a href="{verify_url}"
           style="display: inline-block; padding: 12px 32px; background: #3b82f6;
                  color: white; text-decoration: none; border-radius: 8px;
                  font-weight: 600; margin: 16px 0;">
            Подтвердить email
        </a>
        <p style="color: #666; font-size: 13px;">
            Ссылка действительна 24 часа. Если вы не регистрировались — проигнорируйте это письмо.
        </p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;" />
        <p style="color: #999; font-size: 12px;">EdTon.ai — AI-адаптация резюме</p>
    </div>
    """
    return subject, html
