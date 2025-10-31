from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import datetime
import requests
import time

app = Flask(__name__)

# Конфигурация для Vercel
api_key = os.environ.get('DEEPSEEK_API_KEY')

# Хранение данных в памяти (для Vercel)
# В Vercel файловая система read-only, кроме /tmp
DATA_FILE = '/tmp/data.json'

# Глобальная переменная для хранения данных в памяти
app_data = {
    "users": [],
    "materials": [],
    "subjects": ["Математика", "Физика", "Программирование", "Английский", "История", "Химия"]
}

def init_data():
    global app_data
    try:
        # Пытаемся загрузить из файла
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
                app_data = loaded_data
    except Exception:
        # Если ошибка, используем данные по умолчанию
        pass
    
    # Гарантируем наличие всех необходимых полей
    if "materials" not in app_data:
        app_data["materials"] = []
    if "subjects" not in app_data:
        app_data["subjects"] = ["Математика", "Физика", "Программирование", "Английский", "История", "Химия"]
    if "users" not in app_data:
        app_data["users"] = []

def save_data():
    global app_data
    try:
        # Пытаемся сохранить в файл
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(app_data, f, ensure_ascii=False, indent=2)
    except Exception:
        # В Vercel /tmp может быть недоступен, просто игнорируем
        pass

# Маршруты страниц
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/materials')
def materials():
    materials_list = app_data.get("materials", [])
    subjects_list = app_data.get("subjects", ["Математика", "Физика", "Программирование", "Английский"])
    return render_template('materials.html', materials=materials_list, subjects=subjects_list)

@app.route('/ai-helper')
def ai_helper():
    return render_template('ai_helper.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')

# API endpoints
@app.route('/api/materials')
def get_materials():
    return jsonify({"materials": app_data.get("materials", []), "subjects": app_data.get("subjects", [])})

@app.route('/api/add_material', methods=['POST'])
def add_material():
    material = {
        "id": len(app_data["materials"]) + 1,
        "title": request.json['title'],
        "content": request.json['content'],
        "subject": request.json['subject'],
        "type": request.json['type'],
        "date": datetime.now().strftime("%d.%m.%Y %H:%M")
    }
    app_data["materials"].append(material)
    save_data()
    return jsonify({"status": "success", "material": material})

@app.route('/api/delete_material/<int:material_id>', methods=['DELETE'])
def delete_material(material_id):
    app_data["materials"] = [m for m in app_data["materials"] if m["id"] != material_id]
    save_data()
    return jsonify({"status": "success"})

class AIHelper:
    def __init__(self):
        self.last_request_time = 0
        self.min_interval = 1
    
    def ask_question(self, question):
        current_time = time.time()
        if current_time - self.last_request_time < self.min_interval:
            time.sleep(self.min_interval - (current_time - self.last_request_time))
        
        # Если API ключ не установлен, возвращаем демо-ответ
        if not api_key:
            demo_responses = [
                f"Отличный вопрос! '{question}' - это очень интересная тема. В обычных условиях я бы объяснил это подробно, но сейчас API ключ не настроен. Для работы с AI-помощником необходимо добавить DEEPSEEK_API_KEY в настройки Vercel.",
                f"Вопрос '{question}' действительно важен для понимания. Для получения полного ответа необходимо настроить API ключ DeepSeek в переменных окружения Vercel.",
                f"Я бы с радостью объяснил тему '{question}', но сначала нужно настроить аутентификацию. Добавьте DEEPSEEK_API_KEY в настройки вашего проекта на Vercel.",
            ]
            import random
            return random.choice(demo_responses)
        
        try:
            # DeepSeek API
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "system", 
                        "content": """Ты - умный помощник для студентов и учеников. 
                        Твоя задача - объяснять сложные темы простыми и понятными словами.
                        Используй аналогии, примеры из жизни и дружелюбный тон.
                        Если тема очень сложная, разбей объяснение на несколько простых шагов.
                        Будь поддерживающим и мотивирующим."""
                    },
                    {
                        "role": "user", 
                        "content": f"Пожалуйста, объясни следующее простыми словами, как если бы ты объяснял другу: {question}"
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 2000
            }
            
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result['choices'][0]['message']['content']
                self.last_request_time = time.time()
                return answer
            else:
                return f"Ошибка API: {response.status_code}. Пожалуйста, проверьте API ключ и попробуйте снова."
            
        except Exception as e:
            return f"Произошла ошибка при подключении: {str(e)}"

# Создаем экземпляр помощника
ai_helper_instance = AIHelper()

@app.route('/api/ask_ai', methods=['POST'])
def ask_ai():
    try:
        question = request.json['question']
        
        if not question or len(question.strip()) < 3:
            return jsonify({"answer": "Пожалуйста, задайте более конкретный вопрос."})
        
        answer = ai_helper_instance.ask_question(question)
        return jsonify({"answer": answer})
        
    except Exception as e:
        return jsonify({"answer": f"Извините, произошла непредвиденная ошибка: {str(e)}"})

# Инициализация при запуске
init_data()

# Для Vercel нужно экспортировать app как handler
handler = app