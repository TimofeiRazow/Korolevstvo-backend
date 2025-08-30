import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app, render_template_string

def send_email(to_email, subject, html_content, text_content=None):
    """Отправка email"""
    try:
        smtp_server = current_app.config.get('MAIL_SERVER')
        smtp_port = current_app.config.get('MAIL_PORT')
        username = current_app.config.get('MAIL_USERNAME')
        password = current_app.config.get('MAIL_PASSWORD')
        
        if not all([smtp_server, username, password]):
            print("Email configuration not set")
            return False
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = username
        msg['To'] = to_email
        
        if text_content:
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            msg.attach(text_part)
        
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(username, password)
        server.send_message(msg)
        server.quit()
        
        return True
    
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False

def send_booking_notification(booking, is_quick=False):
    """Отправка уведомления о новой заявке"""
    admin_email = current_app.config.get('ADMIN_EMAIL')
    
    if is_quick:
        subject = f"Быстрая заявка - {booking.phone}"
        html_content = f"""
        <h2>Новая быстрая заявка!</h2>
        <p><strong>Имя:</strong> {booking.name}</p>
        <p><strong>Телефон:</strong> {booking.phone}</p>
        <p><strong>Сообщение:</strong> {booking.message}</p>
        <p><strong>Дата создания:</strong> {booking.created_at}</p>
        """
    else:
        service_name = booking.service.title if booking.service else "Не указана"
        subject = f"Новая заявка на {service_name}"
        html_content = f"""
        <h2>Новая заявка на бронирование!</h2>
        <p><strong>Имя:</strong> {booking.name}</p>
        <p><strong>Телефон:</strong> {booking.phone}</p>
        <p><strong>Email:</strong> {booking.email or 'Не указан'}</p>
        <p><strong>Услуга:</strong> {service_name}</p>
        <p><strong>Дата мероприятия:</strong> {booking.event_date or 'Не указана'}</p>
        <p><strong>Время:</strong> {booking.event_time or 'Не указано'}</p>
        <p><strong>Количество гостей:</strong> {booking.guests_count or 'Не указано'}</p>
        <p><strong>Бюджет:</strong> {booking.budget or 'Не указан'}</p>
        <p><strong>Место проведения:</strong> {booking.location or 'Не указано'}</p>
        <p><strong>Сообщение:</strong> {booking.message or 'Нет сообщения'}</p>
        <p><strong>Дата создания:</strong> {booking.created_at}</p>
        """
    
    # Отправка администратору
    send_email(admin_email, subject, html_content)
    
    # Отправка клиенту подтверждения
    if booking.email and not is_quick:
        client_subject = "Ваша заявка принята - Королевство Чудес"
        client_html = f"""
        <h2>Спасибо за заявку!</h2>
        <p>Здравствуйте, {booking.name}!</p>
        <p>Ваша заявка успешно принята. Мы свяжемся с Вами в ближайшее время для уточнения деталей.</p>
        <p><strong>Номер заявки:</strong> #{booking.id}</p>
        <p><strong>Услуга:</strong> {service_name}</p>
        <p>С уважением,<br>Команда "Королевство Чудес"</p>
        <p>Телефон: +7 (7152) 123-456</p>
        """
        send_email(booking.email, client_subject, client_html)

def send_contact_message(name, email, phone, subject, message):
    """Отправка сообщения обратной связи"""
    admin_email = current_app.config.get('ADMIN_EMAIL')
    
    html_content = f"""
    <h2>Сообщение с сайта</h2>
    <p><strong>Имя:</strong> {name}</p>
    <p><strong>Email:</strong> {email}</p>
    <p><strong>Телефон:</strong> {phone or 'Не указан'}</p>
    <p><strong>Тема:</strong> {subject}</p>
    <p><strong>Сообщение:</strong></p>
    <p>{message}</p>
    <p><strong>Дата:</strong> {datetime.now()}</p>
    """
    
    send_email(admin_email, f"Сообщение с сайта: {subject}", html_content)