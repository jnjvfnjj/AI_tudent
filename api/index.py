from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import datetime
import requests
import time

app = Flask(__name__)

# Конфигурация
api_key = os.environ.get('DEEPSEEK_API_KEY')

# Простое хранение данных
DATA_FILE = '/tmp/data.json'  # Используем /tmp для Vercel

def init_data():
    if not os.path.exists(DATA_FILE):
        base_data = {
            "users": [],
            "materials": [],
            "subjects": ["Математика", "Физика", "Программирование", "Английский", "История", "Химия"]
        }
        save_data(base_data)

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_data():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if "materials" not in data:
                data["materials"] = []
            if "subjects" not in data:
                data["subjects"] = ["Математика", "Физика", "Программирование", "Английский", "История", "Химия"]
            if "users" not in data:
                data["users"] = []
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "users": [],
            "materials": [], 
            "subjects": ["Математика", "Физика", "Программирование", "Английский", "История", "Химия"]
        }

# Маршруты страниц
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/materials')
def materials():
    data = load_data()
    materials_list = data.get("materials", [])
    subjects_list = data.get("subjects", ["Математика", "Физика", "Программирование", "Английский"])
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
    data = load_data()
    return jsonify({"materials": data.get("materials", []), "subjects": data.get("subjects", [])})

@app.route('/api/add_material', methods=['POST'])
def add_material():
    data = load_data()
    material = {
        "id": len(data["materials"]) + 1,
        "title": request.json['title'],
        "content": request.json['content'],
        "subject": request.json['subject'],
        "type": request.json['type'],
        "date": datetime.now().strftime("%d.%m.%Y %H:%M")
    }
    data["materials"].append(material)
    save_data(data)
    return jsonify({"status": "success", "material": material})

@app.route('/api/delete_material/<int:material_id>', methods=['DELETE'])
def delete_material(material_id):
    data = load_data()
    data["materials"] = [m for m in data["materials"] if m["id"] != material_id]
    save_data(data)
    return jsonify({"status": "success"})

class AIHelper:
    def __init__(self):
        self.last_request_time = 0
        self.min_interval = 1
    
    def ask_question(self, question):
        current_time = time.time()
        if current_time - self.last_request_time < self.min_interval:
            time.sleep(self.min_interval - (current_time - self.last_request_time))
        
        try:
            # DeepSeek API вместо OpenAI
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
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result['choices'][0]['message']['content']
                self.last_request_time = time.time()
                return answer
            else:
                return f"Ошибка API: {response.status_code} - {response.text}"
            
        except Exception as e:
            return f"Произошла ошибка: {str(e)}"

# Создаем экземпляр помощника
ai_helper = AIHelper()

@app.route('/api/ask_ai', methods=['POST'])
def ask_ai():
    try:
        question = request.json['question']
        
        if not question or len(question.strip()) < 3:
            return jsonify({"answer": "Пожалуйста, задайте более конкретный вопрос."})
        
        if not api_key:
            return jsonify({"answer": "API ключ не настроен. Пожалуйста, проверьте настройки."})
        
        answer = ai_helper.ask_question(question)
        return jsonify({"answer": answer})
        
    except Exception as e:
        return jsonify({"answer": f"Извините, произошла непредвиденная ошибка: {str(e)}"})

# Инициализация при импорте
init_data()