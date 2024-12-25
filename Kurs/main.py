import asyncio
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import json

data = None

# Установите токен вашего бота и API-ключ Eden AI
TELEGRAM_TOKEN = "7634374408:AAH2oaUZuODXB9KbbgC-pKzfKo-krWlMeOc"
EDENAI_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiZDU2MDU1MDItNGJlNS00NjE4LTkzOWQtZWIyMTI4YTE3NzVhIiwidHlwZSI6ImFwaV90b2tlbiJ9.lPzvre9AJIYByJFYF_PJXiXHsTMYFiIRenTRUZcMf4E"

# Инициализация бота и диспетчера
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# Функция для вызова API Eden AI с параметрами предпочтений пользователя
def get_car_recommendations(preferences):
    url = "https://api.edenai.run/v2/workflow/881223cf-a666-423b-97eb-c4ccaa625b3b/execution/"
    headers = {"Authorization": f"Bearer {EDENAI_API_KEY}"}
    
    payload = {
        "prompt": f"Ты — эксперт по автомобилям. Помоги выбрать автомобиль по следующим предпочтениям: {preferences}. Пожалуйста, предложи несколько вариантов автомобилей, которые соответствуют этим критериям, с указанием модели, цены и кратким описанием."
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        #print(f"Response status: {response.status_code}")
        #print(f"Response body: {response.text}")  # Выводим тело ответа для анализа
        
        if response.status_code == 201:
            return response.json().get('id')  # Возвращаем ID запроса для дальнейшей проверки
        else:
            return {"error": f"Ошибка API Eden AI: {response.status_code}"}
    except Exception as e:
        return {"error": f"Произошла ошибка: {str(e)}"}

# Функция для получения результатов выполнения из Eden AI
def get_results_from_eden(execution_id):
    url = f"https://api.edenai.run/v2/workflow/881223cf-a666-423b-97eb-c4ccaa625b3b/execution/{execution_id}/"
    headers = {"Authorization": f"Bearer {EDENAI_API_KEY}"}
    
    try:
        response = requests.get(url, headers=headers)
        #print(f"Response status: {response.status_code}")
        #print(f"Response body: {response.text}")  # Выводим тело ответа для анализа
        
        if response.status_code == 200:
            data = json.loads(response.text)
            return response.json()
        else:
            return {"error": f"Ошибка при получении результатов: {response.status_code}"}
    except Exception as e:
        return {"error": f"Произошла ошибка: {str(e)}"}

# Обработчик команды /start
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "Привет! Я помогу тебе выбрать автомобиль по твоим предпочтениям. "
        "Напиши, что ты ищешь в автомобиле (например, 'вместительный, экономичный, для города')."
    )

# Обработчик текстовых сообщений
@dp.message()
async def handle_message(message: types.Message):
    user_preferences = message.text
    await message.answer("Ищу автомобили, подходящие под твои предпочтения...")

    # Вызов функции API Eden AI для получения ID запроса
    execution_id = get_car_recommendations(user_preferences)
    
    if "error" in execution_id:
        await message.answer(f"Произошла ошибка: {execution_id['error']}")
        return

    # Периодически проверяем статус обработки
    while True:
        results = get_results_from_eden(execution_id)

        if "error" in results:
            await message.answer(f"Произошла ошибка при получении результатов: {results['error']}")
            return
        
        content = results.get("content", {})
        
        # Проверяем статус ответа: если он "succeeded", останавливаем цикл
        if content.get("status") == "succeeded":
            break
        
        await asyncio.sleep(5)  # Пауза в 5 секунд, прежде чем повторить запрос

    # Извлекаем generated_text из ответа и отправляем пользователю
    generated_text = content['results']['text__chat']['results'][0]['generated_text']
    if not generated_text:
        await message.answer("К сожалению, подходящих автомобилей не найдено.")
    else:
        await message.answer(str(generated_text))  # Обеспечиваем, чтобы это было строкой

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
