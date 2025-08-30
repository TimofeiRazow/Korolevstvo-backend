import requests
from bs4 import BeautifulSoup

def get_product_from_service_online(barcode: str):
    try:
        url = f"https://service-online.su/text/shtrih-kod/?cod={barcode}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Ищем блок с зелёным текстом
        info_div = soup.find('div', style=lambda value: value and "color: green" in value)
        if not info_div:
            return None

        paragraphs = info_div.find_all('p')
        if len(paragraphs) >= 3:
            is_valid = 'верный' in paragraphs[0].get_text(strip=True)
            country = get_info_by_name('Страна производитель ', paragraphs)
            product_name = get_info_by_name('Это: ', paragraphs)
            category = get_info_by_name('Категория:', paragraphs)

            return {
                'barcode': barcode,
                'isValid': is_valid,
                'country': country,
                'name': product_name,
                'category': category,
                'source': 'service-online.su'
            }

        return None
    except Exception as e:
        print(f"Service-Online parsing failed: {e}")
        return None
    
def get_info_by_name(name: str, paragraphs) -> str:
    for paragraph in paragraphs:
        text = paragraph.get_text(strip=True)
        if name in text:
            return text.replace(name, '')
    return ''