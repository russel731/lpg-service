translations = {
    "kz": {
        "welcome": "Қош келдіңіз!",
        "choose_lang": "Тілді таңдаңыз",
        "find_gas": "🔍 Газ табу",
        "add_station": "⛽ Жанармай құю станциясын қосу",
    },
    "ru": {
        "welcome": "Добро пожаловать!",
        "choose_lang": "Выберите язык",
        "find_gas": "🔍 Найти газ",
        "add_station": "⛽ Добавить заправку",
    }
}


def t(lang: str, key: str):
    return translations.get(lang, translations["ru"]).get(key, key)