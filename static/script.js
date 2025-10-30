// Глобальные переменные
let currentMaterials = [];

// Загрузка материалов
async function loadMaterials() {
    try {
        const response = await fetch('/api/materials');
        const data = await response.json();
        currentMaterials = data.materials || [];
        displayMaterials();
        updateStats();
    } catch (error) {
        console.error('Ошибка загрузки материалов:', error);
    }
}

// Отображение материалов
function displayMaterials() {
    const container = document.getElementById('materials-list');
    
    if (!currentMaterials || currentMaterials.length === 0) {
        container.innerHTML = `
            <div class="loading">
                <p>Пока нет сохраненных материалов</p>
                <p>Добавьте первый материал используя кнопку выше!</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = currentMaterials.map(material => `
        <div class="material-card">
            <div class="material-header">
                <div class="material-title">${material.title}</div>
                <div class="material-subject">${material.subject}</div>
            </div>
            <div class="material-content">${material.content}</div>
            <div class="material-footer">
                <div class="material-type">${getTypeLabel(material.type)} • ${material.date}</div>
                <button class="delete-btn" onclick="deleteMaterial(${material.id})">Удалить</button>
            </div>
        </div>
    `).join('');
}

// Получение русскоязычного названия типа
function getTypeLabel(type) {
    const types = {
        'lecture': 'Лекция',
        'book': 'Книга',
        'homework': 'Домашняя работа',
        'note': 'Заметка'
    };
    return types[type] || type;
}

// Добавление материала
async function addMaterial() {
    const title = document.getElementById('material-title').value;
    const content = document.getElementById('material-content').value;
    const subject = document.getElementById('material-subject').value;
    const type = document.getElementById('material-type').value;
    
    if (!title || !content || !subject) {
        alert('Пожалуйста, заполните все поля');
        return;
    }
    
    try {
        const response = await fetch('/api/add_material', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({title, content, subject, type})
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            // Очистка формы
            document.getElementById('material-title').value = '';
            document.getElementById('material-content').value = '';
            document.getElementById('material-subject').value = '';
            
            // Скрытие формы и обновление списка
            hideAddForm();
            currentMaterials.push(result.material);
            displayMaterials();
            updateStats();
            
            showNotification('Материал успешно сохранен!', 'success');
        }
    } catch (error) {
        console.error('Ошибка сохранения:', error);
        showNotification('Ошибка при сохранении материала', 'error');
    }
}

// Удаление материала
async function deleteMaterial(materialId) {
    if (!confirm('Вы уверены, что хотите удалить этот материал?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/delete_material/${materialId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            currentMaterials = currentMaterials.filter(m => m.id !== materialId);
            displayMaterials();
            updateStats();
            showNotification('Материал удален', 'success');
        }
    } catch (error) {
        console.error('Ошибка удаления:', error);
        showNotification('Ошибка при удалении материала', 'error');
    }
}

// ИИ помощник
async function askAI() {
    const questionInput = document.getElementById('ai-question');
    const question = questionInput.value.trim();
    const chatMessages = document.getElementById('chat-messages');
    
    if (!question) {
        alert('Пожалуйста, введите вопрос');
        return;
    }
    
    // Добавление вопроса пользователя
    chatMessages.innerHTML += `
        <div class="message user-message">
            <strong>Вы:</strong> ${question}
        </div>
    `;
    
    // Очистка поля ввода
    questionInput.value = '';
    
    // Показать индикатор загрузки
    chatMessages.innerHTML += `
        <div class="message ai-message loading">
            <strong>ИИ:</strong> Думаю...
        </div>
    `;
    
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    try {
        const response = await fetch('/api/ask_ai', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({question: question})
        });
        
        const data = await response.json();
        
        // Удаление индикатора загрузки
        const loadingMessages = chatMessages.querySelectorAll('.loading');
        loadingMessages.forEach(msg => msg.remove());
        
        // Добавление ответа ИИ
        chatMessages.innerHTML += `
            <div class="message ai-message">
                <strong>ИИ:</strong> ${data.answer}
            </div>
        `;
        
        chatMessages.scrollTop = chatMessages.scrollHeight;
        updateStats();
        
    } catch (error) {
        console.error('Ошибка запроса к ИИ:', error);
        
        // Удаление индикатора загрузки
        const loadingMessages = chatMessages.querySelectorAll('.loading');
        loadingMessages.forEach(msg => msg.remove());
        
        chatMessages.innerHTML += `
            <div class="message ai-message error">
                <strong>ИИ:</strong> Извините, произошла ошибка. Пожалуйста, попробуйте еще раз.
            </div>
        `;
    }
}

// Установка примера вопроса
function setExample(question) {
    document.getElementById('ai-question').value = question;
}

// Управление формой добавления
function showAddForm() {
    document.getElementById('add-form').style.display = 'block';
}

function hideAddForm() {
    document.getElementById('add-form').style.display = 'none';
}

// Обновление статистики
function updateStats() {
    // Обновление счетчика материалов
    const materialsCount = currentMaterials ? currentMaterials.length : 0;
    document.getElementById('materials-count').textContent = materialsCount;
    document.getElementById('total-materials').textContent = materialsCount;
    
    // Обновление других статистик
    const questionCount = document.querySelectorAll('.user-message').length;
    document.getElementById('total-questions').textContent = questionCount;
}

// Редактирование профиля
function editProfile() {
    const name = prompt('Введите ваше имя:', document.getElementById('user-name').textContent);
    const school = prompt('Введите ваше учебное заведение:', document.getElementById('user-school').textContent);
    const course = prompt('Введите ваш курс/класс:', document.getElementById('user-course').textContent);
    
    if (name) document.getElementById('user-name').textContent = name;
    if (school) document.getElementById('user-school').textContent = school;
    if (course) document.getElementById('user-course').textContent = course;
    
    showNotification('Профиль обновлен', 'success');
}

// Уведомления
function showNotification(message, type = 'info') {
    // Создание элемента уведомления
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'success' ? '#4CAF50' : type === 'error' ? '#ff4757' : '#6C63FF'};
        color: white;
        border-radius: 8px;
        z-index: 10000;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    `;
    
    document.body.appendChild(notification);
    
    // Автоматическое удаление через 3 секунды
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Загрузка материалов если на странице материалов
    if (document.getElementById('materials-list')) {
        loadMaterials();
    }
    
    // Обновление статистики на главной
    if (document.getElementById('materials-count')) {
        updateStats();
    }
    
    // Обработка Enter в поле вопроса ИИ
    const aiQuestionInput = document.getElementById('ai-question');
    if (aiQuestionInput) {
        aiQuestionInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                askAI();
            }
        });
    }
    
    // Обработка Enter в форме добавления материала
    const materialTitleInput = document.getElementById('material-title');
    if (materialTitleInput) {
        materialTitleInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                addMaterial();
            }
        });
    }
});