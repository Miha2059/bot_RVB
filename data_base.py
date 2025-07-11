from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext

# Словник для зберігання даних (після можна замінити на БД)
devices = {}

# Стани для ConversationHandler
SELECTING_ACTION, ADD_DEVICE, FIND_DEVICE, CHANGE_RESPONSIBLE = range(4)

# Головне меню
main_menu = [['Додати', 'Знайти']]
add_menu = [['Рація', 'Акумулятор', 'Зарядний пристрій']]
find_menu = [['По серійному номеру', 'По відповідальній особі']]

# Функція старту
def start(update: Update, context: CallbackContext):
    keyboard = ReplyKeyboardMarkup(main_menu, one_time_keyboard=True)
    update.message.reply_text("Привіт! Вибери одну з опцій:", reply_markup=keyboard)
    return SELECTING_ACTION

# Головне меню
def main_menu_handler(update: Update, context: CallbackContext):
    user_input = update.message.text
    if user_input == "Додати":
        keyboard = ReplyKeyboardMarkup(add_menu, one_time_keyboard=True)
        update.message.reply_text("Виберіть тип пристрою:", reply_markup=keyboard)
        return ADD_DEVICE
    elif user_input == "Знайти":
        keyboard = ReplyKeyboardMarkup(find_menu, one_time_keyboard=True)
        update.message.reply_text("Виберіть спосіб пошуку:", reply_markup=keyboard)
        return FIND_DEVICE

# Додавання пристрою
def add_device(update: Update, context: CallbackContext):
    device_type = update.message.text
    context.user_data['device_type'] = device_type
    update.message.reply_text(f"Введіть назву {device_type}:")
    return ADD_DEVICE

def save_device(update: Update, context: CallbackContext):
    device_name = update.message.text
    device_type = context.user_data.get('device_type')
    update.message.reply_text(f"Введіть серійний номер {device_name}:")
    context.user_data['device_name'] = device_name
    return ADD_DEVICE

def save_serial(update: Update, context: CallbackContext):
    serial_number = update.message.text
    device_name = context.user_data.get('device_name')
    device_type = context.user_data.get('device_type')
    update.message.reply_text(f"Введіть відповідальну особу для {device_name}:")
    context.user_data['serial_number'] = serial_number
    return ADD_DEVICE

def save_responsible(update: Update, context: CallbackContext):
    responsible_person = update.message.text
    device_name = context.user_data.get('device_name')
    device_type = context.user_data.get('device_type')
    serial_number = context.user_data.get('serial_number')

    # Зберігаємо пристрій в словник
    devices[serial_number] = {
        "device_name": device_name,
        "device_type": device_type,
        "responsible_person": responsible_person
    }

    update.message.reply_text(f"Пристрій {device_name} успішно додано!")
    return SELECTING_ACTION

# Пошук пристрою
def find_device(update: Update, context: CallbackContext):
    search_type = update.message.text
    if search_type == 'По серійному номеру':
        update.message.reply_text("Введіть серійний номер:")
        return FIND_DEVICE
    elif search_type == 'По відповідальній особі':
        update.message.reply_text("Введіть відповідальну особу:")
        return FIND_DEVICE

def search_by_serial(update: Update, context: CallbackContext):
    serial_number = update.message.text
    device_info = devices.get(serial_number)
    if device_info:
        update.message.reply_text(f"Пристрій: {device_info['device_name']}\nТип: {device_info['device_type']}\nВідповідальна особа: {device_info['responsible_person']}")
        update.message.reply_text("Бажаєте змінити відповідальну особу? (так/ні)")
        return CHANGE_RESPONSIBLE
    else:
        update.message.reply_text("Пристрій не знайдено.")
        return SELECTING_ACTION

def search_by_responsible(update: Update, context: CallbackContext):
    responsible_person = update.message.text
    found_devices = [serial for serial, info in devices.items() if info['responsible_person'] == responsible_person]
    if found_devices:
        for serial in found_devices:
            device_info = devices[serial]
            update.message.reply_text(f"Пристрій: {device_info['device_name']}\nТип: {device_info['device_type']}\nСерійний номер: {serial}")
        update.message.reply_text("Бажаєте змінити відповідальну особу? (так/ні)")
        return CHANGE_RESPONSIBLE
    else:
        update.message.reply_text("Пристрій не знайдено.")
        return SELECTING_ACTION

def change_responsible(update: Update, context: CallbackContext):
    response = update.message.text.lower()
    if response == 'так':
        update.message.reply_text("Введіть нову відповідальну особу:")
        return CHANGE_RESPONSIBLE
    else:
        return SELECTING_ACTION

def save_new_responsible(update: Update, context: CallbackContext):
    new_responsible = update.message.text
    serial_number = context.user_data.get('serial_number')
    if serial_number and serial_number in devices:
        devices[serial_number]['responsible_person'] = new_responsible
        update.message.reply_text(f"Відповідальну особу змінено на {new_responsible}")
    return SELECTING_ACTION

# Окрема функція для обробки відміни
def cancel(update: Update, context: CallbackContext):
    update.message.reply_text("Операцію скасовано.")
    return SELECTING_ACTION

# Основна функція для запуску бота
def main():
    updater = Updater("7940312910:AAE8Y6HG7aVha-njidmgKZ_3QfBLMnu0WFg", use_context=True)
    dispatcher = updater.dispatcher

    # Визначення розмовних процесів
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECTING_ACTION: [MessageHandler(Filters.text, main_menu_handler)],
            ADD_DEVICE: [
                MessageHandler(Filters.text & ~Filters.command, save_device),
                MessageHandler(Filters.text & ~Filters.command, save_serial),
                MessageHandler(Filters.text & ~Filters.command, save_responsible),
            ],
            FIND_DEVICE: [MessageHandler(Filters.text & ~Filters.command, search_by_serial), MessageHandler(Filters.text & ~Filters.command, search_by_responsible)],
            CHANGE_RESPONSIBLE: [MessageHandler(Filters.text & ~Filters.command, change_responsible), MessageHandler(Filters.text & ~Filters.command, save_new_responsible)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
