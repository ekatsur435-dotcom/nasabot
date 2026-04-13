# NASA Instagram Template Render API

API для генерации Instagram-шаблонов для объектов недвижимости.

## Деплой на Render.com (Бесплатно)

### 1. Подготовка

Убедитесь что у вас есть:
- `render_api.py` — основной файл API
- `requirements.txt` — зависимости

### 2. Создание сервиса на Render

1. Зарегистрируйтесь на [render.com](https://render.com)
2. Нажмите "New Web Service"
3. Выберите "Build and deploy from a Git repository"
4. Создайте новый репозиторий на GitHub/GitLab и загрузите файлы:
   ```bash
   git init
   git add render_api.py requirements.txt
   git commit -m "Initial commit"
   git push origin main
   ```
5. Подключите репозиторий к Render

### 3. Настройка

**Build Command:**
```bash
pip install -r requirements.txt
```

**Start Command:**
```bash
gunicorn render_api:app
```

**Environment:**
- Python 3
- Free tier ($5/месяц)

### 4. Получение URL

После деплоя Render выдаст URL типа:
```
https://nasa-instagram-api.onrender.com
```

Добавьте `/generate` в настройки плагина:
```
https://nasa-instagram-api.onrender.com/generate
```

## Тестирование API

```bash
curl -X POST https://your-app.onrender.com/generate \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Luxury Villa in Antalya",
    "price": "€250,000",
    "property_type": "Вилла",
    "property_status": "Продажа",
    "city": "Анталья",
    "label": "🇹🇷 Гражданство",
    "distance_to_beach": "🌊 500м до пляжа",
    "image_url": "https://example.com/villa.jpg",
    "template": "vertical"
  }'
```

## Локальный запуск

```bash
pip install -r requirements.txt
python render_api.py
```

API будет доступен на `http://localhost:5000`
