from flask import Blueprint, request, jsonify

company_data_bp = Blueprint('company_data', __name__, url_prefix='/company_data')

# Начальные данные — все поля из Settings.jsx
company_info = {
    # Компания
    "companyName": "Королевство Чудес",
    "companyEmail": "info@prazdnikvdom.kz",
    "companyPhone": "+7 (777) 123-45-67",
    "whatsappPhone": "+7 (777) 987-65-43",
    "companyAddress": "г. Петропавловск, ул. Ленина, 123",
    "companyDescription": "Профессиональная организация праздников и мероприятий",

    # Соцсети
    "socialInstagram": "https://instagram.com/korolevstvo_chudes",
    "socialFacebook": "",
    "socialYoutube": "",
    "socialTelegram": "",

    # Уведомления
    "emailNotifications": True,
    "telegramNotifications": False,
    "smsNotifications": False,
    "notificationEmail": "admin@prazdnikvdom.kz",

    # SEO
    "siteTitle": "Организация праздников в Петропавловске - Королевство Чудес",
    "siteDescription": "Профессиональная организация праздников в Петропавловске. Детские дни рождения, свадьбы, корпоративы.",
    "siteKeywords": "праздники петропавловск, аниматоры, организация свадеб",
    "googleAnalyticsId": "",
    "yandexMetricaId": "",

    # Интеграции
    "kaspiApiKey": "",
    "oneC_url": "",
    "smtpServer": "",
    "smtpPort": ""
}

# GET — получить все настройки
@company_data_bp.route('/', methods=['GET'])
def get_all_data():
    return jsonify(company_info), 200

# GET — получить конкретное поле
@company_data_bp.route('/<field>', methods=['GET'])
def get_field(field):
    if field not in company_info:
        return jsonify({"error": "Поле не найдено"}), 404
    return jsonify({field: company_info[field]}), 200

# POST — обновить данные
@company_data_bp.route('/', methods=['POST'])
def update_data():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Empty JSON'}), 400

    for key in company_info:
        if key in data:
            company_info[key] = data[key]

    return jsonify({'message': 'Данные успешно обновлены', 'data': company_info}), 200
