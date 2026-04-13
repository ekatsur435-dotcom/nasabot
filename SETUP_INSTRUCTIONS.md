# NASA Instagram API - Полная настройка

## 📋 Что нужно загрузить на GitHub

### Файлы для репозитория `nasabot`:

1. **app.py** - основной API (создан)
2. **requirements.txt** - зависимости (создан)
3. **render.yaml** - конфиг Render (создан)
4. **README.md** - описание (по желанию)
5. **.gitignore** - исключения (по желанию)

---

## 🚀 Шаг 1: Загрузка на GitHub

```bash
# Перейди в папку с файлами
cd /Users/artemt/Downloads

# Инициализируй git (если еще не сделано)
git init

# Добавь файлы
git add app.py requirements.txt render.yaml

# Сделай коммит
git commit -m "Initial NASA Instagram API"

# Добавь удаленный репозиторий (замени на свой URL)
git remote add origin https://github.com/ekatsur435-dotcom/nasabot.git

# Отправь на GitHub
git push -u origin main
```

**Или вручную:**
1. Открой https://github.com/ekatsur435-dotcom/nasabot
2. Нажми "Add file" → "Upload files"
3. Загрузи: `app.py`, `requirements.txt`, `render.yaml`
4. Commit changes

---

## 🚀 Шаг 2: Подключение к Render

1. Зайди на https://dashboard.render.com
2. Нажми **"New +"** → **"Web Service"**
3. Выбери **"Build and deploy from a Git repository"**
4. Подключи GitHub-аккаунт и выбери `nasabot`
5. Настройки:
   - **Name**: `nasa-instagram-api`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
6. Нажми **"Create Web Service"**

Жди 2-3 минуты пока соберется.

**Полученный URL** будет такой:
```
https://nasa-instagram-api.onrender.com
```

---

## 🔔 Шаг 3: Настройка UptimeRobot ("будка")

**Зачем:** Чтобы Render не "засыпал" через 15 минут.

1. Зайди на https://uptimerobot.com
2. Регистрация (бесплатно)
3. Нажми **"Add New Monitor"**
4. Настройки:
   - **Monitor Type**: `HTTP(s)`
   - **Friendly Name**: `NASA Instagram API`
   - **URL**: `https://nasa-instagram-api.onrender.com/health`
   - **Monitoring Interval**: `Every 5 minutes` (бесплатно)
5. Нажми **"Create Monitor"**

✅ Готово! Теперь API всегда "бодрый".

---

## 🚀 Шаг 4: Настройка плагина в WordPress

1. Установи плагин `nasa-instagram-autopost-v2.0.zip`
2. Перейди в **Настройки** → **NASA Instagram**
3. Заполни поля:
   - **Access Token**: (из Facebook Developers)
   - **Instagram User ID**: (из Facebook Developers)
   - **Render API URL**: `https://nasa-instagram-api.onrender.com/generate`
   - **Шаблон**: `Вертикальный (1080x1350)`
4. Сохрани настройки

---

## 🧪 Шаг 5: Тестирование

### Тест API:
```bash
curl -X POST https://nasa-instagram-api.onrender.com/generate \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Вилла в Анталье",
    "property_type": "Вилла",
    "property_status": "Продажа",
    "city": "Анталья",
    "label": "Гражданство",
    "distance_to_beach": "500м до пляжа",
    "image_url": "https://nasa-homes.com/wp-content/uploads/villa.jpg",
    "template": "vertical"
  }'
```

### Тест плагина:
1. Создай объект недвижимости в WordPress
2. Укажи таксономии: Вилла, Продажа, Гражданство, Анталья
3. Укажи расстояние до пляжа в поле `fave_distance_to_beach`
4. Сохрани объект
5. Проверь логи в настройках плагина

---

## 📁 Структура файлов

```
nasabot/
├── app.py              # API для генерации картинок
├── requirements.txt    # Зависимости Python
├── render.yaml         # Конфиг Render
└── README.md           # Описание (опционально)
```

---

## 🆘 Если что-то не работает

### Проблема: "Service unavailable"
- Проверь UptimeRobot — должен быть зеленый статус
- Проверь логи Render: Dashboard → Logs

### Проблема: Шрифты не отображаются
- Это нормально на бесплатном Render
- Картинки будут с системными шрифтами

### Проблема: "image_url is required"
- Проверь что у объекта есть featured image
- Или заполнено поле `fave_property_images`

---

## 📞 Поддержка

Если нужна помощь — пиши!
