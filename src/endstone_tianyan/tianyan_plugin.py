from endstone.command import Command, CommandSender
from endstone.plugin import Plugin
from endstone import ColorFormat,Player
from endstone.event import event_handler, BlockBreakEvent,PlayerInteractEvent,ActorKnockbackEvent,BlockPlaceEvent,PlayerCommandEvent,PlayerJoinEvent,PlayerChatEvent,PlayerInteractActorEvent
import os
from datetime import datetime
import json
import threading
import math
from datetime import datetime, timedelta
import shutil
import time as tm
from collections import defaultdict
import re
import sqlite3
from endstone.form import ModalForm,Dropdown,Label,ActionForm,TextInput,Slider,MessageForm
from endstone.inventory import Inventory,PlayerInventory
from endstone.block import BlockData

# Код для совместимости, предназначенный для работы с данными версий до 1.1.3
def ensure_blockdata_column():
    cursor.execute("PRAGMA table_info(interactions)")
    columns = [column[1] for column in cursor.fetchall()]  # Получить все названия столбцов
    if 'blockdata' not in columns:
        cursor.execute("ALTER TABLE interactions ADD COLUMN blockdata TEXT")
        conn.commit()

subdir = "plugins/tianyan_data"
if not os.path.exists(subdir):
    os.makedirs(subdir)
banlist = os.path.join('plugins/tianyan_data/banlist.json')
banidlist = os.path.join('plugins/tianyan_data/banidlist.json')
config_file = os.path.join(subdir, 'config.json')

default_config = {
    'Записывать ли естественные блоки': True,
    'Записывать ли искусственные блоки': True,
    'Записывать ли только важных существ': True,
}
if not os.path.exists(config_file):
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, ensure_ascii=False)
# Чтение файла конфигурации
with open(config_file, 'r', encoding='utf-8') as f:
    config = json.load(f)
    
# Установить переменные на основе значений из конфигурационного файла
natural = 1 if config.get('Записывать ли естественные блоки', False) else 0
human = 1 if config.get('Записывать ли искусственные блоки', False) else 0
nbanimal = 1 if config.get('Записывать ли только важных существ', False) else 0

# Включить запись природных блоков, но не включать запись искусственных блоков
if natural == 1 and human == 0:
    blockrec = 1
# Включить всё
elif natural == 1 and human == 1:
    blockrec = 2
# Выключить все блоки
elif natural == 0 and human == 0:
    blockrec = 3
# Выключить запись природных блоков, включить запись искусственных блоков
elif natural == 0 and human == 1:
    blockrec = 4

# Инициализация базы данных SQLite
db_file = "plugins/tianyan_data/tydata.db"
conn = sqlite3.connect(db_file, check_same_thread=False)
cursor = conn.cursor()

# Создать таблицу
cursor.execute("""
CREATE TABLE IF NOT EXISTS interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    action TEXT,
    x INTEGER,
    y INTEGER,
    z INTEGER,
    type TEXT,
    world TEXT,
    time TEXT,
    blockdata TEXT
)
""")
conn.commit()

chestrec_data = []
breakrec_data = []
animalrec_data = []
placerec_data = []
actorrec_data = []
lock = threading.Lock()  # Блокировка для обеспечения потокобезопасности
running_lock = threading.Lock()
is_running = False

# Записать данные в SQLite
def write_to_db():
    global chestrec_data, breakrec_data, animalrec_data, placerec_data, actorrec_data, is_running
    with lock:
        with running_lock:
            if is_running:
                return
            is_running = True
    try:
        if placerec_data:
            with conn:
                for data in placerec_data:
                    cursor.execute("""
                        INSERT INTO interactions (name, action, x, y, z, type, world, time)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        data['name'],
                        data['action'],
                        data['coordinates']['x'],
                        data['coordinates']['y'],
                        data['coordinates']['z'],
                        data['type'],
                        data['world'],
                        data['time']
                    ))
            placerec_data.clear()
        if chestrec_data:
            with conn:
                for data in chestrec_data:
                    cursor.execute("""
                        INSERT INTO interactions (name, action, x, y, z, type, world, time)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        data['name'],
                        data['action'],
                        data['coordinates']['x'],
                        data['coordinates']['y'],
                        data['coordinates']['z'],
                        data['type'],
                        data['world'],
                        data['time']
                    ))
            chestrec_data.clear()
        if breakrec_data:
            with conn:
                for data in breakrec_data:
                    if 'blockdata' in data:
                        cursor.execute("""
                            INSERT INTO interactions (name, action, x, y, z, type, world, time, blockdata)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            data['name'],
                            data['action'],
                            data['coordinates']['x'],
                            data['coordinates']['y'],
                            data['coordinates']['z'],
                            data['type'],
                            data['world'],
                            data['time'],
                            data['blockdata']
                        ))
                    else:
                        cursor.execute("""
                            INSERT INTO interactions (name, action, x, y, z, type, world, time)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            data['name'],
                            data['action'],
                            data['coordinates']['x'],
                            data['coordinates']['y'],
                            data['coordinates']['z'],
                            data['type'],
                            data['world'],
                            data['time']
                        ))
            breakrec_data.clear()
        if animalrec_data:
            with conn:
                for data in animalrec_data:
                    cursor.execute("""
                        INSERT INTO interactions (name, action, x, y, z, type, world, time)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        data['name'],
                        data['action'],
                        data['coordinates']['x'],
                        data['coordinates']['y'],
                        data['coordinates']['z'],
                        data['type'],
                        data['world'],
                        data['time']
                    ))
            animalrec_data.clear()
        if actorrec_data:
            with conn:
                for data in actorrec_data:
                    cursor.execute("""
                        INSERT INTO interactions (name, action, x, y, z, type, world, time)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        data['name'],
                        data['action'],
                        data['coordinates']['x'],
                        data['coordinates']['y'],
                        data['coordinates']['z'],
                        data['type'],
                        data['world'],
                        data['time']
                    ))
            actorrec_data.clear()
    finally:
        with running_lock:
            is_running = False


# Регулярная запись данных
def periodic_write():
    while True:
        write_to_db()
        tm.sleep(20)

# Запуск потока для регулярной записи
thread = threading.Thread(target=periodic_write)
thread.daemon = True
thread.start()

# Записать в файл при отключении плагина
def on_plugin_close():
    write_to_db()  # Убедиться, что данные записываются в файл при закрытии


 
           

class TianyanPlugin(Plugin):
    api_version = "0.5"

    commands = {
        "ty": {
            "description": "Запросить записи поведения игрока и некоторых сущностей — формат: /ty x y z Время (единица: часы) Радиус",
            "usages": ["/ty [pos:pos] [float:float] [float:float]"],
            "permissions": ["tianyan_plugin.command.ty"],
        },
        "tyhelp": {
            "description": "Просмотреть справочную информацию о команде для небесного глаза",
            "usages": ["/tyhelp"],
            "permissions": ["tianyan_plugin.command.tyhelp"],
        },
        "tyban": {
            "description": "Заблокировать игрока (доступно только для администраторов)",
            "usages": ["/tyban <msg: message> [msg: message]"],
            "permissions": ["tianyan_plugin.command.tyban"],
        },
        "tyunban": {
            "description": "Удалить игрока из чёрного списка (доступно только для администраторов)",
            "usages": ["/tyunban <msg: message> [msg: message]"],
            "permissions": ["tianyan_plugin.command.tyunban"],
        },
        "tybanlist": {
            "description": "Вывести список всех игроков, добавленных в чёрный список (доступно только для администраторов)",
            "usages": ["/tybanlist"],
            "permissions": ["tianyan_plugin.command.tybanlist"],
        },
        "banid": {
            "description": "Заблокировать ID устройства (доступно только для администраторов)",
            "usages": ["/banid <msg: message>"],
            "permissions": ["tianyan_plugin.command.banid"],
        },
        "unbanid": {
            "description": "Удалить ID устройства из чёрного списка устройств (доступно только для администраторов)",
            "usages": ["/unbanid <msg: message>"],
            "permissions": ["tianyan_plugin.command.unbanid"],
        },
        "banidlist": {
            "description": "Вывести список всех ID устройств, добавленных в чёрный список (доступно только для администраторов)",
            "usages": ["/banidlist"],
            "permissions": ["tianyan_plugin.command.banidlist"],
        },
        "tys": {
            "description": "Поиск по ключевым словам — формат: /tys тип поиска ключевое слово время (единица: часы) (доступно только для администраторов)",
            "usages": ["/tys <msg: message> <msg: message> <float:float>"],
            "permissions": ["tianyan_plugin.command.tys"],
        },
        "tygui": {
            "description": "Использовать графический интерфейс для запроса записей поведения игрока и некоторых сущностей",
            "usages": ["/tygui"],
            "permissions": ["tianyan_plugin.command.tygui"],
        },
        "tysgui": {
            "description": "Использовать графический интерфейс для поиска по ключевым словам и запроса записей поведения игрока и некоторых сущностей",
            "usages": ["/tysgui"],
            "permissions": ["tianyan_plugin.command.tysgui"],
        },
        "tyback": {
            "description": "Экспериментальная функция восстановления поведения игрока при прямом размещении и разрушении блоков — формат: /tyback координаты время (единица: часы) радиус имя игрока (необязательно) (доступно только для администраторов)",
            "usages": ["/tyback [pos:pos] <float:float> <float:float> [msg: message]"],
            "permissions": ["tianyan_plugin.command.tyback"],
        }
        #"tyo": {
        #    "description": "Осмотреть инвентарь игрока",
        #    "usages": ["/tyo <msg:message>"],
        #    "permissions": ["tianyan_plugin.command.tyo"],
        #}
        #"test": {
        #    "description": "2",
        #    "usages": ["/test"],
        #    "permissions": ["tianyan_plugin.command.test"],
        #},
    }

    permissions = {
        "tianyan_plugin.command.ty": {
            "description": "Запросить записи поведения игрока и некоторых сущностей",
            "default": True, 
        },
        "tianyan_plugin.command.tyban": {
            "description": "Заблокировать игрока",
            "default": "op", 
        },
        "tianyan_plugin.command.tyunban": {
            "description": "Удалить игрока из чёрного списка (доступно только для администраторов)",
            "default": "op", 
        },
        "tianyan_plugin.command.tybanlist": {
            "description": "Вывести список всех заблокированных игроков (доступно только для администраторов)",
            "default": "op", 
        },
        "tianyan_plugin.command.banid": {
            "description": "Заблокировать ID устройства (доступно только для администраторов)",
            "default": "op", 
        },
        "tianyan_plugin.command.unbanid": {
            "description": "Снять блокировку с ID устройства (доступно только для администраторов)",
            "default": "op", 
        },
        "tianyan_plugin.command.banidlist": {
            "description": "Вывести список всех заблокированных ID устройств (доступно только для администраторов)",
            "default": "op", 
        },
        "tianyan_plugin.command.tys": {
            "description": "Поиск по ключевым словам (доступно только для администраторов)",
            "default": "op", 
        },
        "tianyan_plugin.command.tyhelp": {
            "description": "Посмотреть справочную информацию о команде для небесного глаза",
            "default": True, 
        },
        "tianyan_plugin.command.tygui": {
            "description": "Использовать графический интерфейс для запроса записей поведения игрока и некоторых сущностей",
            "default": True, 
        },
        "tianyan_plugin.command.tysgui": {
            "description": "Использовать графический интерфейс для поиска по ключевым словам и запроса записей поведения игрока и некоторых сущностей (доступно только для администраторов)",
            "default": "op", 
        },
        "tianyan_plugin.command.tyo": {
            "description": "Обследовать инвентарь игрока",
            "default": "op", 
        },
        "tianyan_plugin.command.tyback": {
            "description": "Настроить восстановление (или откат)",
            "default": "op", 
        },
        "tianyan_plugin.command.test": {
            "description": "1",
            "default": True, 
        }
    }

    def on_load(self) -> None:
        self.logger.info("on_load is called!")
        ensure_blockdata_column()

    def on_enable(self) -> None:
        self.logger.info(f"{ColorFormat.YELLOW}Плагин Небесный Глаз активирован, версия V1.1.3, конфигурационный файл находится в plugins/tianyan_data/config.json")
        self.logger.info(f"{ColorFormat.YELLOW}Остальные файлы данных находятся в plugins/tianyan_data/")
        self.logger.info(f"{ColorFormat.YELLOW}Адрес обновления проектаhttps://github.com/yuhangle/Endstone_TianyanPlugin")
        self.logger.info(f"{ColorFormat.YELLOW}Перевод на русский https://urban.sytes.net")
        self.register_events(self)

    def on_disable(self) -> None:
        self.logger.info("on_disable is called!")
        on_plugin_close()
           
    def on_command(self, sender: CommandSender, command: Command, args: list[str]) -> bool:
                        
        if command.name == "tyhelp":
            sender.send_message(f"{ColorFormat.YELLOW}Метод использования команд Небесного Глаза")
            sender.send_message(f"{ColorFormat.YELLOW}Используйте команду /tyban для добавления игрока в чёрный список. Формат: /tyban имя игрока причина (необязательно)")
            sender.send_message(f"{ColorFormat.YELLOW}Используйте команду /tyunban для удаления игрока из чёрного списка. Формат: /tyunban имя игрока")
            sender.send_message(f"{ColorFormat.YELLOW}Используйте команду /banlist для вывода списка всех игроков, добавленных в чёрный список")
            sender.send_message(f"{ColorFormat.YELLOW}Используйте команду /banid для добавления устройства игрока в чёрный список (если устройство целевого игрока онлайн, добавление в чёрный список не приведёт к немедленному исключению; используйте другие методы для исключения этого игрока). Формат: /banid ID устройства")
            sender.send_message(f"{ColorFormat.YELLOW}Используйте команду /unbanid для удаления устройства игрока из чёрного списка. Формат: /unban ID устройства")
            sender.send_message(f"{ColorFormat.YELLOW}Используйте команду /banlist для вывода списка всех устройств игроков, добавленных в чёрный список")
            sender.send_message(f"{ColorFormat.YELLOW}Используйте команду /ty для запроса записей поведения игрока и некоторых сущностей. Формат: /ty x y z время (единица: часы) радиус")
            sender.send_message(f"{ColorFormat.YELLOW}Используйте команду /tys для поиска по ключевым словам в записях поведения игрока и некоторых сущностей. Формат: /tys тип поиска ключевое слово время (единица: часы) (доступно только для администраторов)")
            sender.send_message(f"{ColorFormat.YELLOW}Используйте команду /tygui для запроса записей поведения игрока и некоторых сущностей через графический интерфейс")
            sender.send_message(f"{ColorFormat.YELLOW}Используйте команду /tysgui для поиска по ключевым словам в записях поведения игрока и некоторых сущностей через графический интерфейс (доступно только для администраторов)")
            sender.send_message(f"{ColorFormat.YELLOW}Разбор параметров команды tys. Типы поиска: player, action, object (игрок или исполнитель действия, действие, объект, на который было направлено действие). Ключевые слова поиска: имя игрока или имя исполнителя действия, взаимодействие, разрушение, атака, размещение, имя объекта, на который было направлено действие")
            sender.send_message(f"{ColorFormat.YELLOW}Экспериментальная функция. Используйте команду /tyback для восстановления действий игрока по размещению и разрушению блоков. Формат: /tyback координаты время (единица: часы) радиус имя игрока, выполнявшего действия (необязательно) (доступно только для администраторов)")
            
        elif command.name == "ty":
            if len(args) <= 2:
                if not isinstance(sender, Player):
                    self.logger.info(f"{ColorFormat.RED}Ошибка формата команды! Пожалуйста, проверьте правильность команды. Если используются ~ ~ ~, введите координаты напрямую")
                else:
                    sender.send_error_message("Ошибка формата команды! Пожалуйста, проверьте правильность команды. Если используются ~ ~ ~, введите координаты напрямую")
                return True
            elif "~" in args[0]:
                if not isinstance(sender, Player):
                    self.logger.info(f"{ColorFormat.RED}Ошибка формата команды! Пожалуйста, проверьте правильность команды. Если используются ~ ~ ~, введите координаты напрямую")
                else:
                    sender.send_error_message("Ошибка формата команды! Пожалуйста, проверьте правильность команды. Если используются ~ ~ ~, введите координаты напрямую")
            elif float(args[2]) > 100:
                if not isinstance(sender, Player):
                    self.logger.info(f"{ColorFormat.RED}Максимальное значение радиуса запроса — 100!")
                else:
                    sender.send_error_message("Максимальный радиус запроса составляет 100!")
            else:
                positions = args[0]
                times = float(args[1])
                r = float(args[2])
                coordinates = positions
                x, y, z = map(float, coordinates.split())
                max_lines = 322
                
                # Получить текущее время
                current_time = datetime.now()
                time_threshold = current_time - timedelta(hours=times)
                
                # Запросить базу данных
                results = []
                query = """
                SELECT name, action, x, y, z, type, world, time FROM interactions
                WHERE (x - ?)*(x - ?) + (y - ?)*(y - ?) + (z - ?)*(z - ?) <= ?
                AND time >= ?
                """
                radius_squared = r ** 2
                with conn:
                    cursor.execute(query, (x, x, y, y, z, z, radius_squared, time_threshold.isoformat()))
                    rows = cursor.fetchall()
                    for row in rows:
                        results.append({
                            'name': row[0],
                            'action': row[1],
                            'coordinates': {'x': row[2], 'y': row[3], 'z': row[4]},
                            'type': row[5],
                            'world': row[6],
                            'time': row[7]
                        })
                
                # Обработка результатов
                if not results:
                    if not isinstance(sender, Player):
                        self.logger.info(f"{ColorFormat.YELLOW}Не найдено никаких результатов")
                    else:
                        sender.send_message(f"{ColorFormat.YELLOW}Не найдено никаких результатов")
                else:
                    if not isinstance(sender, Player):
                        self.logger.info(f"{ColorFormat.YELLOW}Для вас найдены записи о действиях игроков и некоторых сущностей в радиусе {r} блоков от этих координат за последние {times} часов")
                    else:
                        sender.send_message(f"{ColorFormat.YELLOW}Найдены записи о действиях игроков и некоторых сущностей в радиусе {r} блоков от указанных координат за последние {times} часов. Пожалуйста, проверьте их через всплывающее окно")
                    output_message = ""  # Создайте пустую строку для хранения всей выводимой информации
                    for item in results:
                        name = item['name']
                        coordinates = item['coordinates']
                        type = item['type']
                        time = item['time']
                        world = item['world']
                        action = item['action']
                        
                        # Отформатировать информацию одной записи
                        message = f"{ColorFormat.YELLOW} Исполнитель действия: {name} \n Действие: {action} \n Координаты: {coordinates} \n Время: {time} \n Тип объекта: {type} \n Измерение: {world}\n"
                        output_message += message + "-" * 20 + "\n"  # Добавить одну запись в общий вывод                  
                    if not isinstance(sender, Player):
                        self.logger.info(output_message)
                    else:
                        #self.server.get_player(sender.name).send_form(ActionForm(title=f'{ColorFormat.BLUE}§l§oЗаписи запросов в радиусе {r} блоков за последние {times} часов',content=output_message))
                        lines = output_message.split("\n")
                        if len(lines) > max_lines:
                            page = 0
                            segments = ["\n".join(lines[i:i + max_lines]) for i in range(0, len(lines), max_lines)]
                            
                            def show(sender):
                                
                                def next_button_click():
                                    def on_click(sender):
                                        nonlocal page  # Используйте nonlocal для объявления переменной page как переменной внешней области видимости
                                        page += 1
                                        if page >= len(segments):  # Проверить, есть ли следующая страница
                                            page = 0  # Вернуться на первую страницу
                                        show(sender)
                                    return on_click
                                
                                def up_button_click():
                                    def on_click(sender):
                                        nonlocal page  # Использовать nonlocal для объявления переменной page как переменной внешней области видимости
                                        if page == 0:  # Если на первой странице, перейти на последнюю страницу
                                            page = len(segments) - 1
                                        else:
                                            page -= 1
                                        show(sender)
                                    return on_click
                                
                                next =  ActionForm.Button(text="Следующая страница",on_click=next_button_click())
                                up =  ActionForm.Button(text="Предыдущая страница",on_click=up_button_click())
                                    
                            # Показать окно первой страницы
                                self.server.get_player(sender.name).send_form(
                                    ActionForm(
                                        title=f'{ColorFormat.BLUE}§l§oЗаписи запросов в радиусе {r} блоков за последние {times} часов - страница {page + 1}',
                                        content=segments[page],
                                        buttons=[up,next]
                                        )
                                    )
                            show(sender)
                        else:
                            self.server.get_player(sender.name).send_form(
                                    ActionForm(
                                        title=f'{ColorFormat.BLUE}§l§oЗаписи запросов в радиусе {r} блоков за последние {times} часов',
                                        content=output_message,
                                        )
                                    )
                        
        elif command.name == "tyban":
            if len(args) == 0:
                if not isinstance(sender, Player):
                    self.logger.info("Ошибка формата")
                else:
                    sender.send_error_message("Ошибка формата")
            if len(args) >= 3:
                if not isinstance(sender, Player):
                    self.logger.info("Ошибка формата")
                else:
                    sender.send_error_message("Ошибка формата")
            else:
                if len(args) == 2:
                    playername = args[0]
                    reason = args[1]
                if len(args) == 1:
                    playername = args[0]
                    reason = "No reason"

                # Проверить, существует ли файл
                if not os.path.exists(banlist):
                    # Если файл не существует, создать пустой файл черного списка
                    with open(banlist, 'w') as file:
                        json.dump({}, file)

                # Чтение файла черного списка
                with open(banlist, 'r',encoding='utf-8') as file:
                    blacklist = json.load(file)
                    
                if playername in blacklist:
                    if not isinstance(sender, Player):
                        entry = blacklist[playername]
                        reason = entry.get("reason")
                        timestamp = entry.get("timestamp")
                        self.logger.info(f"Игрок {playername} уже был добавлен в черный список {timestamp}, причина: {reason}. Пожалуйста, не добавляйте его снова")
                    else:
                        reason = blacklist[playername]
                        sender.send_error_message(f"Игрок {playername} уже был добавлен в черный список {timestamp}, причина: {reason}. Пожалуйста, не добавляйте его снова")
                else:
                    # Записать имя игрока и причину в черный список
                    timestamp = datetime.now().isoformat()  # Использовать текущий временной штамп в качестве значения по умолчанию
                    # Создать новый элемент, содержащий всю информацию
                    entry = {
                        "reason": reason,
                        "timestamp": timestamp
                    }
                    blacklist[playername] = entry

                    # Записать обновленный черный список обратно в файл
                    with open(banlist, 'w', encoding='utf-8') as file:  # Указать кодировку UTF-8
                        json.dump(blacklist, file, ensure_ascii=False, indent=4)
                    
                    if not isinstance(sender, Player):
                        self.logger.info(f"Игрок {playername} был добавлен в черный список, причина: {reason}")
                        self.server.dispatch_command(self.server.command_sender,f'Кикнуть {playername}, причина: {reason}')
                    else:
                        sender.send_error_message(f"Игрок {playername} был добавлен в черный список, причина: {reason}")
                        sender.perform_command(f"Кикнуть {playername}, причина: {reason}")
        
        elif command.name == "tyunban":
            if len(args) == 0:
                if not isinstance(sender, Player):
                    self.logger.info("Ошибка формата")
                else:
                    sender.send_error_message("Ошибка формата")
            if len(args) >= 2:
                if not isinstance(sender, Player):
                    self.logger.info("Ошибка формата")
                else:
                    sender.send_error_message("Ошибка формата")
            else:
                yplayername = args[0]
                playername = yplayername.strip('"')
                # Проверить, существует ли файл
                if not os.path.exists(banlist):
                    # Если файл не существует, создать пустой файл черного списка
                    with open(banlist, 'w',encoding='utf-8') as file:
                        json.dump({}, file)
                    if not isinstance(sender, Player):
                        self.logger.info("Файл черного списка не существует, он был автоматически создан")
                    else:
                        sender.send_error_message("Файл черного списка не существует, он был автоматически создан")
                else:
                    # Читать файл черного списка
                    with open(banlist, 'r', encoding='utf-8') as file:
                        blacklist = json.load(file)
                    
                    # Проверить, находится ли игрок в черном списке
                    if playername in blacklist:
                        del blacklist[playername]
                        # Записать обновленный черный список обратно в файл
                        with open(banlist, 'w', encoding='utf-8') as file:  # Указать кодировку UTF-8
                            json.dump(blacklist, file, ensure_ascii=False, indent=4)
                        if not isinstance(sender, Player):
                            self.logger.info(f"Игрок {playername} был удален из черного списка")
                        else:
                            sender.send_error_message(f"Игрок {playername} был удален из черного списка")
                    else:
                        if not isinstance(sender, Player):
                            self.logger.info(f"Игрок {playername} не существует в черном списке")
                        else:
                            sender.send_error_message(f"Игрок {playername} отсутствует в черном списке")
        elif command.name == "tybanlist":
            # Проверить, существует ли файл
            if not os.path.exists(banlist):
                if not isinstance(sender, Player):
                    self.logger.info(f"Файл черного списка не существует")
                else:
                    sender.send_error_message(f"Файл черного списка не существует")
                    
            else:
                # Читать файл черного списка
                with open(banlist, 'r', encoding='utf-8') as file:
                    blacklist = json.load(file)
                if not blacklist:
                    if not isinstance(sender, Player):
                        self.logger.info("В черном списке нет игроков")
                    else:
                        sender.send_error_message("В черном списке нет игроков")
                else:
                    # Перебрать всех игроков в черном списке
                    for playername, entry in blacklist.items():
                        reason = entry.get("reason")
                        timestamp = entry.get("timestamp")
                        if not isinstance(sender, Player):
                            self.logger.info(f"Игрок {playername} был забанен {timestamp}, причина: {reason}")
                        else:
                            sender.send_error_message(f"Игрок {playername} был забанен {timestamp}, причина: {reason}")

        elif command.name == "banid":
            if len(args) == 0:
                if not isinstance(sender, Player):
                    self.logger.info("Ошибка формата")
                else:
                    sender.send_error_message("Ошибка формата")
            if len(args) >= 2:
                if not isinstance(sender, Player):
                    self.logger.info("Ошибка формата")
                else:
                    sender.send_error_message("Ошибка формата")
            else:
                if len(args) == 1:
                    device_id = args[0]

                # Проверить, существует ли файл
                if not os.path.exists(banidlist):
                    # Если файл не существует, создать пустой файл черного списка
                    with open(banidlist, 'w') as file:
                        json.dump({}, file)

                # Читать файл черного списка по идентификаторам устройств
                with open(banidlist, 'r',encoding='utf-8') as file:
                    blackidlist = json.load(file)
                    
                if device_id in blackidlist:
                    if not isinstance(sender, Player):
                        entry = blackidlist[device_id]
                        timestamp = entry.get("timestamp")
                        self.logger.info(f"Устройство с ID {device_id} уже было добавлено в черный список устройств {timestamp}, пожалуйста, не добавляйте снова")
                    else:
                        entry = blackidlist[device_id]
                        timestamp = entry.get("timestamp")
                        sender.send_error_message(f"Устройство с ID {device_id} уже было добавлено в черный список устройств {timestamp}, пожалуйста, не добавляйте снова")
                else:
                    # Записать идентификатор устройства в черный список
                    timestamp = datetime.now().isoformat()  # Использовать текущий временной штамп в качестве значения по умолчанию
                    # Создать новый элемент, содержащий всю информацию
                    entry = {
                        "timestamp": timestamp
                    }
                    blackidlist[device_id] = entry

                    # Записать обновленный черный список обратно в файл
                    with open(banidlist, 'w', encoding='utf-8') as file:  # Указать кодировку UTF-8
                        json.dump(blackidlist, file, ensure_ascii=False, indent=4)
                    if not isinstance(sender, Player):
                        self.logger.info(f"Устройство с ID {device_id} было добавлено в черный список")
                    else:
                        sender.send_error_message(f"Устройство с ID {device_id} было добавлено в черный список")
        
        elif command.name == "unbanid":
            if len(args) == 0:
                if not isinstance(sender, Player):
                    self.logger.info("Ошибка формата")
                else:
                    sender.send_error_message("Ошибка формата")
            if len(args) >= 2:
                if not isinstance(sender, Player):
                    self.logger.info("Ошибка формата")
                else:
                    sender.send_error_message("Ошибка формата")
            else:
                device_id = args[0]
                # Проверьте, существует ли файл
                if not os.path.exists(banlist):
                    # Если файл не существует, создайте пустой файл черного списка
                    with open(banidlist, 'w',encoding='utf-8') as file:
                        json.dump({}, file)
                    if not isinstance(sender, Player):
                        self.logger.info("Файл черного списка ID устройств не существует, создан автоматически")
                    else:
                        sender.send_error_message("Файл черного списка ID устройств не существует, создан автоматически")
                else:
                    # Чтение файла черного списка устройств
                    with open(banidlist, 'r', encoding='utf-8') as file:
                        blackidlist = json.load(file)
                    
                    # Проверьте, находится ли устройство в черном списке
                    if device_id in blackidlist:
                        del blackidlist[device_id]
                        # Запишите обновленный черный список обратно в файл
                        with open(banidlist, 'w', encoding='utf-8') as file:  # Указать кодировку UTF-8
                            json.dump(blackidlist, file, ensure_ascii=False, indent=4)
                        if not isinstance(sender, Player):
                            self.logger.info(f"Устройство с ID {device_id} удалено из черного списка")
                        else:
                            sender.send_error_message(f"Устройство с ID {device_id} удалено из черного списка")
                    else:
                        if not isinstance(sender, Player):
                            self.logger.info(f"Устройство с ID {device_id} отсутствует в черном списке")
                        else:
                            sender.send_error_message(f"Устройство с ID {device_id} отсутствует в черном списке")
                            
        elif command.name == "banidlist":
            # Проверьте, существует ли файл
            if not os.path.exists(banidlist):
                if not isinstance(sender, Player):
                    self.logger.info(f"Файл черного списка устройств не существует")
                else:
                    sender.send_error_message(f"Файл черного списка устройств не существует")
                    
            else:
                # Чтение файла черного списка устройств
                with open(banidlist, 'r', encoding='utf-8') as file:
                    blackidlist = json.load(file)
                if not blackidlist:
                    if not isinstance(sender, Player):
                        self.logger.info("В черном списке нет устройств")
                    else:
                        sender.send_error_message("В черном списке нет устройств")
                else:
                    # Перебор всех устройств в черном списке
                    for device_id, entry in blackidlist.items():
                        timestamp = entry.get("timestamp")
                        if not isinstance(sender, Player):
                            self.logger.info(f"Устройство с ID {device_id} было заблокировано в {timestamp}.")
                        else:
                            sender.send_error_message(f"Устройство с ID {device_id} было заблокировано в {timestamp}.")
        elif command.name == "tys":
            if len(args) <= 2:
                if not isinstance(sender, Player):
                    self.logger.info(f"{ColorFormat.RED}Ошибка формата команды! Пожалуйста, проверьте правильность команды")
                else:
                    sender.send_error_message("Ошибка формата команды! Пожалуйста, проверьте правильность команды")
                return True
            elif args[0] not in ["player", "action", "object"]:  # Игрок, действие, объект
                if not isinstance(sender, Player):
                    self.logger.info(f"{ColorFormat.RED}Ошибка формата команды! Неизвестный параметр {args[0]}")
                else:
                    sender.send_error_message(f"Ошибка формата команды! Неизвестный параметр {args[0]}")
            else:
                searchtype = args[0]  # Тип поиска
                searchobject = args[1]  # Ключевое слово для поиска
                time = float(args[2])  # Временной диапазон поиска
                # Ограничение на максимальное количество строк
                max_lines = 322
                            
                def search_db(keyword, time, stype):
                    """
                    Запрос записей, соответствующих условиям, из базы данных SQLite

                    Args:
                        keyword: Ключевое слово для поиска
                        time: Временной диапазон (единица измерения: часы)
                        stype: Тип поля для поиска

                    Returns:
                        Список записей, соответствующих условиям
                    """
                    now = datetime.now()
                    search_time = now - timedelta(hours=time)

                    query = f"""
                    SELECT name, action, x, y, z, type, world, time 
                    FROM interactions
                    WHERE {stype} LIKE ?
                    AND time >= ?
                    """
                    results = []
                    with conn:
                        cursor.execute(query, (f"%{keyword}%", search_time.isoformat()))
                        rows = cursor.fetchall()
                        for row in rows:
                            results.append({
                                'name': row[0],
                                'action': row[1],
                                'coordinates': {'x': row[2], 'y': row[3], 'z': row[4]},
                                'type': row[5],
                                'world': row[6],
                                'time': row[7]
                            })
                    return results

                def output(keyword, time, stype):
                    results = search_db(keyword, time, stype)
                    if not results:
                        if not isinstance(sender, Player):
                            self.logger.info(f"{ColorFormat.YELLOW}Не найдено результатов по запросу")
                        else:
                            sender.send_message(f"{ColorFormat.YELLOW}Не найдено результатов по запросу")
                    else:
                        if not isinstance(sender, Player):
                            self.logger.info(f"{ColorFormat.YELLOW}\nДля вас были найдены следующие материалы по ключевому слову {keyword}" + "-" * 20)
                        else:
                            sender.send_message(f"{ColorFormat.YELLOW}Для вас были найдены материалы по ключевому слову {keyword}, пожалуйста, посмотрите их в всплывающем окне\n")
                        output_message = ""  # Создайте пустую строку для хранения всей информации вывода
                        for record in results:
                        # Отформатировать информацию о записи
                            message = f" {ColorFormat.YELLOW}Исполнитель действия: {record['name']} \n Действие: {record['action']} \n Координаты: {record['coordinates']} \n Время: {record['time']} \n Тип объекта: {record['type']} \n Мир: {record['world']} \n"
                            output_message += message + "-" * 20 + "\n"  # Добавьте запись в общий вывод   
                        if not isinstance(sender, Player):
                            self.logger.info(output_message)
                        else:
                            lines = output_message.split("\n")
                            if len(lines) > max_lines:
                                page = 0
                                segments = ["\n".join(lines[i:i + max_lines]) for i in range(0, len(lines), max_lines)]
                                
                                def show(sender):
                                    
                                    def next_button_click():
                                        def on_click(sender):
                                            nonlocal page  # Используйте nonlocal для объявления переменной page как переменной внешней области видимости
                                            page += 1
                                            if page >= len(segments):  # Проверьте, есть ли следующая страница
                                                page = 0  # Вернуться на первую страницу
                                            show(sender)
                                        return on_click
                                    
                                    def up_button_click():
                                        def on_click(sender):
                                            nonlocal page  # Используйте nonlocal для объявления переменной page как переменной внешней области видимости
                                            if page == 0:  # Если находитесь на первой странице, перейдите на последнюю страницу
                                                page = len(segments) - 1
                                            else:
                                                page -= 1
                                            show(sender)
                                        return on_click
                                    
                                    next =  ActionForm.Button(text="Следующая страница",on_click=next_button_click())
                                    up =  ActionForm.Button(text="Предыдущая страница",on_click=up_button_click())
                                        
                                # Показать окно первой страницы
                                    self.server.get_player(sender.name).send_form(
                                        ActionForm(
                                            title=f'{ColorFormat.BLUE}§l§o{keyword} записи за {time} часов — страница {page + 1}',
                                            content=segments[page],
                                            buttons=[up,next]
                                            )
                                        )
                                show(sender)
                            else:
                                self.server.get_player(sender.name).send_form(
                                        ActionForm(
                                            title=f'{ColorFormat.BLUE}§l§oЗаписи по ключевому слову {keyword} за {time} часов',
                                            content=output_message,
                                            )
                                        )

                # Поиск по имени игрока
                if searchtype == "player":
                    stype = "name"
                    keyword = searchobject
                    output(keyword, time, stype)
                # Поиск по действию
                elif searchtype == "action":
                    stype = "action"
                    keyword = searchobject
                    output(keyword, time, stype)
                # Поиск по объекту цели
                elif searchtype == "object":
                    stype = "type"
                    keyword = searchobject
                    output(keyword, time, stype)
                    
        elif command.name == "tygui":
            if not isinstance(sender, Player):
                sender.send_error_message("Команда не может быть использована в консоли")
            else:
                submit = lambda player, json_str: (
                    #self.logger.info(f"Received JSON: {json_str}"),  # Записать журнал
                    player.perform_command(
                        f'ty {__import__("json").loads(json_str)[0]} {__import__("json").loads(json_str)[1]} {__import__("json").loads(json_str)[2]}'
                    )
                )
                self.server.get_player(sender.name).send_form(
                    ModalForm(
                        title=f'{ColorFormat.YELLOW}Меню поиска через "Небесный глаз"',
                        controls=[
                            TextInput(label='Координаты', placeholder='Введите координаты для поиска'),
                            TextInput(label='Время', placeholder='Введите время для поиска (в часах)'),
                            TextInput(label='Радиус', placeholder='Введите радиус для поиска')
                        ],
                        on_submit=submit
                    )
                )
            
        elif command.name == "tysgui":
            if not isinstance(sender, Player):
                sender.send_error_message("Команда не может быть использована в консоли")
            else:
                submit = lambda player, json_str: (
                    #self.logger.info(f"Received JSON: {json_str}"),  # Записать журнал
                    player.perform_command(
                        f'tys {['player','action','object'][__import__('json').loads(json_str)[0]]} "{__import__("json").loads(json_str)[1]}" {__import__("json").loads(json_str)[2]}'
                    )
                )
                self.server.get_player(sender.name).send_form(
                    ModalForm(
                        title=f'{ColorFormat.YELLOW}Меню поиска по ключевым словам через "Небесный глаз"',
                        controls=[
                            Dropdown(label='Выберите тип поиска (игрок или исполнитель действия, действие, объект, над которым было выполнено действие)',options=['player','action','object']),
                            TextInput(label='Ключевое слово', placeholder='Введите ключевое слово для поиска'),
                            TextInput(label='Время', placeholder='Введите время для поиска (в часах)'),
                        ],
                        on_submit=submit
                    )
                )
                
        #elif command.name == "tyo":
        #    playername = args[0]
        #    ms = self.server.get_player(playername).inventory
        #    sender.send_message(ms)
            
        elif command.name == "tyback":
            if len(args) < 3:
                if not isinstance(sender, Player):
                    self.logger.info(f"{ColorFormat.RED}Ошибка формата команды! Пожалуйста, проверьте правильность команды. Если используете ~ ~ ~, введите координаты напрямую")
                else:
                    sender.send_error_message("Ошибка формата команды! Пожалуйста, проверьте правильность команды. Если используется ~ ~ ~, введите координаты напрямую")
                return True
            elif "~" in args[0]:
                if not isinstance(sender, Player):
                    self.logger.info(f"{ColorFormat.RED}Ошибка формата команды! Пожалуйста, проверьте правильность команды. Если используется ~ ~ ~, введите координаты напрямую")
                else:
                    sender.send_error_message("Ошибка формата команды! Пожалуйста, проверьте правильность команды. Если используется ~ ~ ~, введите координаты напрямую")
            elif float(args[2]) > 100:
                if not isinstance(sender, Player):
                    self.logger.info(f"{ColorFormat.RED}Максимальное значение радиуса — 100!")
                else:
                    sender.send_error_message("Максимальное значение радиуса — 100!")
            else:
                positions = args[0]
                times = float(args[1])
                r = float(args[2])
                coordinates = positions
                x, y, z = map(float, coordinates.split())
                max_lines = 322
                exe_player_dim = self.server.get_player(sender.name).location.dimension.name
                
                #Получить текущее время
                current_time = datetime.now()
                time_threshold = current_time - timedelta(hours=times)
                
                # Откатить действия для отдельного игрока
                if len(args) == 4:
                    do_player_name = args[3]
                
                    # Запрос к базе данных
                    results = []
                    query = """
                    SELECT name, action, x, y, z, type, world, time, blockdata FROM interactions
                    WHERE (x - ?)*(x - ?) + (y - ?)*(y - ?) + (z - ?)*(z - ?) <= ?
                    AND time >= ?
                    AND world = ?
                    AND name = ?
                    """
                    radius_squared = r ** 2
                    with conn:
                        cursor.execute(query, (x, x, y, y, z, z, radius_squared, time_threshold.isoformat(),exe_player_dim,do_player_name))
                        rows = cursor.fetchall()
                        for row in rows:
                            results.append({
                                'name': row[0],
                                'action': row[1],
                                'coordinates': {'x': row[2], 'y': row[3], 'z': row[4]},
                                'type': row[5],
                                'world': row[6],
                                'time': row[7],
                                'blockdata': row[8] if row[8] is not None else ''  # Обработка поля blockdata
                            })
                # Если нет информации о игроке, не добавлять
                else:
                    # Запрос к базе данных
                    results = []
                    query = """
                    SELECT name, action, x, y, z, type, world, time, blockdata FROM interactions
                    WHERE (x - ?)*(x - ?) + (y - ?)*(y - ?) + (z - ?)*(z - ?) <= ?
                    AND time >= ?
                    AND world = ?
                    """
                    radius_squared = r ** 2
                    with conn:
                        cursor.execute(query, (x, x, y, y, z, z, radius_squared, time_threshold.isoformat(),exe_player_dim))
                        rows = cursor.fetchall()
                        for row in rows:
                            results.append({
                                'name': row[0],
                                'action': row[1],
                                'coordinates': {'x': row[2], 'y': row[3], 'z': row[4]},
                                'type': row[5],
                                'world': row[6],
                                'time': row[7],
                                'blockdata': row[8] if row[8] is not None else None  # Обработка поля blockdata
                            })
                
                # Обработка результатов
                if not results:
                    if not isinstance(sender, Player):
                        self.logger.info(f"{ColorFormat.RED}Пожалуйста, не используйте консоль")
                    else:
                        sender.send_message(f"{ColorFormat.YELLOW}Нет записанных данных")
                else:
                    if not isinstance(sender, Player):
                        self.logger.info(f"{ColorFormat.RED}Пожалуйста, не используйте консоль")
                    else:
                        sender.send_message(f"{ColorFormat.YELLOW}Начать восстановление блоков в пределах {r} блоков за {times} часов")
                        
                        for item in results:
                            
                            turnaction = item['action']
                            if turnaction == 'Разрушить':
                                coordinates = item['coordinates']
                                type = item['type']
                                x,y,z = coordinates['x'],coordinates['y'],coordinates['z']
                                pos = f'{x} {y} {z}'
                                blockdata = item['blockdata']
                                sender.perform_command(f'setblock {pos} {type}{blockdata}')
                                #action = 'Разместить'
                            elif turnaction == 'Разместить':
                                coordinates = item['coordinates']
                                x,y,z = coordinates['x'],coordinates['y'],coordinates['z']
                                pos = f'{x} {y} {z}'
                                sender.perform_command(f'setblock {pos} air')
                                #action = 'Разрушить'
                        
        
        elif command.name == "test":
            self.server.get_player(sender.name).send_form(
                MessageForm(
                    title='Тестовая форма',
                    content='Первый император, не завершивший своего дела, внезапно скончался. В настоящее время мир разделён на три части, Ичжоу ослаблен, и это действительно критический момент для жизни и смерти. Однако слуги при дворе не ослабляют своих усилий, верные служители на внешнем фронте забывают о собственной жизни, всё это — из-за великой милости, оказанной первым императором, и желания отплатить за это Вашему Величеству. Поэтому надлежит открыть уши для справедливых советов, чтобы прославить наследие первого императора и возродить дух доблестных людей, не следует самоуничижаться, приводя ложные примеры и запирать путь для искренних советов.(сообщение для проверки которое написал сам китаец)',
                    button1='Определить',
                    button2='Отменить'
                )
            )

        return True
        
# Взаимодействие с контейнерами и другие события взаимодействия
    @event_handler
    def blockjh(self,event: PlayerInteractEvent): 
        # Разделительная линия
        def record_data(name, action, x, y, z, type,world):
            # """Записать действия игрока в файл data.json"""
            interaction = {
                'name': name,
                'action': action,
                'coordinates': {'x': x, 'y': y, 'z': z},
                'time': datetime.now().isoformat(),  # Записать текущее время
                'type': type,
                "world": world
            } 
            
            with lock:  # Обеспечить безопасность потока
                chestrec_data.append(interaction)                  
            #threading.Thread(target=write_to_file).start()
            
        if event.block.type == "minecraft:chest":
            name = event.player.name
            action = "Взаимодействие"
            x = event.block.x
            y = event.block.y
            z = event.block.z
            type = "Сундук"
            world = event.block.location.dimension.name
            record_data(name, action, x, y, z, type, world)
            
        if event.block.type == "minecraft:trapped_chest":
            name = event.player.name
            action = "Взаимодействие"
            x = event.block.x
            y = event.block.y
            z = event.block.z
            type = "Сундук-ловушка"
            world = event.block.location.dimension.name
            record_data(name, action, x, y, z, type, world)
            
        if event.block.type == "minecraft:barrel":
            name = event.player.name
            action = "Взаимодействие"
            x = event.block.x
            y = event.block.y
            z = event.block.z
            type = "Бочка"
            world = event.block.location.dimension.name
            record_data(name, action, x, y, z, type, world)
            
        if event.block.type == "minecraft:ender_chest":
            name = event.player.name
            action = "Взаимодействие"
            x = event.block.x
            y = event.block.y
            z = event.block.z
            type = "Эндер сундук"
            world = event.block.location.dimension.name
            record_data(name, action, x, y, z, type, world)
            
        if event.block.type == "minecraft:hopper":
            name = event.player.name
            action = "Взаимодействие"
            x = event.block.x
            y = event.block.y
            z = event.block.z
            type = "Воронка"
            world = event.block.location.dimension.name
            record_data(name, action, x, y, z, type, world)
            
        if event.block.type == "minecraft:dispenser":
            name = event.player.name
            action = "Взаимодействие"
            x = event.block.x
            y = event.block.y
            z = event.block.z
            type = "Раздатчик"
            world = event.block.location.dimension.name
            record_data(name, action, x, y, z, type, world)
            
        if event.block.type == "minecraft:dropper":
            name = event.player.name
            action = "Взаимодействие"
            x = event.block.x
            y = event.block.y
            z = event.block.z
            type = "Выбрасыватель"
            world = event.block.location.dimension.name
            record_data(name, action, x, y, z, type, world)
            
        if event.block.type == "minecraft:lever":
            name = event.player.name
            action = "Взаимодействие"
            x = event.block.x
            y = event.block.y
            z = event.block.z
            type = "Рычаг"
            world = event.block.location.dimension.name
            record_data(name, action, x, y, z, type, world)
            
        if event.block.type == "minecraft:unpowered_repeater":
            name = event.player.name
            action = "Взаимодействие"
            x = event.block.x
            y = event.block.y
            z = event.block.z
            type = "Незапитанный повторитель"
            world = event.block.location.dimension.name
            record_data(name, action, x, y, z, type, world)
            
        if event.block.type == "minecraft:unpowered_comparator":
            name = event.player.name
            action = "Взаимодействие"
            x = event.block.x
            y = event.block.y
            z = event.block.z
            type = "Незапитанный компоратор"
            world = event.block.location.dimension.name
            record_data(name, action, x, y, z, type, world)
            
        if event.block.type == "minecraft:powered_comparator":
            name = event.player.name
            action = "Взаимодействие"
            x = event.block.x
            y = event.block.y
            z = event.block.z
            type = "Запитанный компоратор"
            world = event.block.location.dimension.name
            record_data(name, action, x, y, z, type, world)
            
        if event.block.type == "minecraft:powered_repeater":
            name = event.player.name
            action = "Взаимодействие"
            x = event.block.x
            y = event.block.y
            z = event.block.z
            type = "Запитанный повторитель"
            world = event.block.location.dimension.name
            record_data(name, action, x, y, z, type, world)
            
        if event.block.type == "minecraft:dropper":
            name = event.player.name
            action = "Взаимодействие"
            x = event.block.x
            y = event.block.y
            z = event.block.z
            type = "Выбрасыватель"
            world = event.block.location.dimension.name
            record_data(name, action, x, y, z, type, world)
            
        if event.block.type == "minecraft:jukebox":
            name = event.player.name
            action = "Взаимодействие"
            x = event.block.x
            y = event.block.y
            z = event.block.z
            type = "Проигрыватель"
            world = event.block.location.dimension.name
            record_data(name, action, x, y, z, type, world)
            
        if event.block.type == "minecraft:noteblock":
            name = event.player.name
            action = "Взаимодействие"
            x = event.block.x
            y = event.block.y
            z = event.block.z
            type = "Нотный Блок"
            world = event.block.location.dimension.name
            record_data(name, action, x, y, z, type, world)
            
        if event.block.type in [
            "minecraft:wooden_button","minecraft:spruce_button","minecraft:birch_button","minecraft:jungle_button","minecraft:acacia_button",
            "minecraft:dark_oak_button","minecraft:mangrove_button","minecraft:cherry_button","minecraft:bamboo_button","minecraft:pale_oak_button",
            "minecraft:crimson_button","minecraft:warped_button","minecraft:stone_button","minecraft:polished_blackstone_button"
            ]:
            name = event.player.name
            action = "Взаимодействие"
            x = event.block.x
            y = event.block.y
            z = event.block.z
            type = "Кнопка"
            world = event.block.location.dimension.name
            record_data(name, action, x, y, z, type, world)
            
        if event.block.type in [
            "minecraft:standing_sign","minecraft:spruce_standing_sign","minecraft:birch_standing_sign","minecraft:jungle_standing_sign","minecraft:acacia_standing_sign",
            "minecraft:darkoak_standing_sign","minecraft:mangrove_standing_sign","minecraft:cherry_standing_sign","minecraft:pale_oak_standing_sign","minecraft:bamboo_standing_sign",
            "minecraft:crimson_standing_sign","minecraft:warped_standing_sign","minecraft:wall_sign","minecraft:spruce_wall_sign","minecraft:birch_wall_sign","minecraft:jungle_wall_sign",
            "minecraft:acacia_wall_sign","minecraft:darkoak_wall_sign","minecraft:mangrove_wall_sign","minecraft:cherry_wall_sign","minecraft:pale_oak_wall_sign","minecraft:bamboo_wall_sign","minecraft:crimson_wall_sign","minecraft:warped_wall_sign"
            ]:
            name = event.player.name
            action = "Взаимодействие"
            x = event.block.x
            y = event.block.y
            z = event.block.z
            type = "Табличка"
            world = event.block.location.dimension.name
            record_data(name, action, x, y, z, type, world)
            
        if event.block.type in [
            "minecraft:oak_hanging_sign","minecraft:spruce_hanging_sign","minecraft:birch_hanging_sign","jungle_hanging_sign","acacia_hanging_sign",
            "dark_oak_hanging_sign","mangrove_hanging_sign","cherry_hanging_sign","pale_oak_hanging_sign","bamboo_hanging_sign","crimson_hanging_sign","warped_hanging_sign"
            ]:
            name = event.player.name
            action = "Взаимодействие"
            x = event.block.x
            y = event.block.y
            z = event.block.z
            type = "Подвесная табличка"
            world = event.block.location.dimension.name
            record_data(name, action, x, y, z, type, world)
            
        if event.block.type in [
            "minecraft:anvil","minecraft:chipped_anvil","minecraft:damaged_anvil"
            ]:
            name = event.player.name
            action = "Взаимодействие"
            x = event.block.x
            y = event.block.y
            z = event.block.z
            type = "Наковальня"
            world = event.block.location.dimension.name
            record_data(name, action, x, y, z, type, world)
            
        if event.block.type in [
            "minecraft:furnace","minecraft:lit_furnace"
            ]:
            name = event.player.name
            action = "Взаимодействие"
            x = event.block.x
            y = event.block.y
            z = event.block.z
            type = "Печь"
            world = event.block.location.dimension.name
            record_data(name, action, x, y, z, type, world)
            
        if event.block.type in [
            "minecraft:blast_furnace","minecraft:lit_blast_furnace"
            ]:
            name = event.player.name
            action = "Взаимодействие"
            x = event.block.x
            y = event.block.y
            z = event.block.z
            type = "Плавильня"
            world = event.block.location.dimension.name
            record_data(name, action, x, y, z, type, world)
        
        if event.block.type in [
            "minecraft:undyed_shulker_box", "minecraft:white_shulker_box", 
            "minecraft:light_gray_shulker_box", "minecraft:gray_shulker_box", 
            "minecraft:brown_shulker_box", "minecraft:red_shulker_box", 
            "minecraft:orange_shulker_box", "minecraft:yellow_shulker_box", 
            "minecraft:lime_shulker_box", "minecraft:green_shulker_box", 
            "minecraft:cyan_shulker_box", "minecraft:light_blue_shulker_box", 
            "minecraft:blue_shulker_box", "minecraft:purple_shulker_box", 
            "minecraft:magenta_shulker_box", "minecraft:pink_shulker_box"
        ]:
            name = event.player.name
            action = "Взаимодействие"
            x = event.block.x
            y = event.block.y
            z = event.block.z
            world = event.block.location.dimension.name
            type = "Ящик шалкера"
            record_data(name, action, x, y, z, type,world)
        
        if str(event.item) in [
            "ItemStack(minecraft:flint_and_steel x 1)","ItemStack(minecraft:lava_bucket x 1)","ItemStack(minecraft:water_bucket x 1)","ItemStack(minecraft:powder_snow_bucket x 1)","ItemStack(minecraft:cod_bucket x 1)","ItemStack(minecraft:salmon_bucket x 1)","ItemStack(minecraft:pufferfish_bucket x 1)","ItemStack(minecraft:tropical_fish_bucket x 1)","ItemStack(minecraft:axolotl_bucket x 1)","ItemStack(minecraft:tadpole_bucket x 1)"
        ]:
            name = event.player.name
            blocktype = event.block.type
            action = "Взаимодействие"
            x = event.block.x
            y = event.block.y
            z = event.block.z
            type = f"{blocktype}, использовано {event.item}"
            world = event.block.location.dimension.name
            record_data(name, action, x, y, z, type,world)
            
        # Количество не определено
        item_str = str(event.item)
        bucket_pattern = r"ItemStack\(minecraft:bucket\s+x\s*\d+\)"
        if re.match(bucket_pattern, item_str) and event.block.type in [
            "minecraft:water","minecraft:lava","minecraft:powder_snow"]:# Ведро взаимодействует с блоками, которые могут быть в него налиты
            name = event.player.name
            blocktype = event.block.type
            action = "Взаимодействие"
            x = event.block.x
            y = event.block.y
            z = event.block.z
            type = f"{blocktype}, использовано {event.item}"
            world = event.block.location.dimension.name
            record_data(name, action, x, y, z, type,world)

        fire_pattern = r"ItemStack\(minecraft:fire_charge\s+x\s*\d+\)"
        if re.match(fire_pattern, item_str):# Огненный шар
            name = event.player.name
            blocktype = event.block.type
            action = "Взаимодействие"
            x = event.block.x
            y = event.block.y
            z = event.block.z
            type = f"{blocktype}, использовано {event.item}"
            world = event.block.location.dimension.name
            record_data(name, action, x, y, z, type,world)
            
        if event.block.type == "minecraft:bed":# Кровать
            name = event.player.name
            blocktype = event.block.type
            action = "Взаимодействие"
            x = event.block.x
            y = event.block.y
            z = event.block.z
            type = f"{blocktype}, использовано {event.item}"
            world = event.block.location.dimension.name
            record_data(name, action, x, y, z, type,world)
            
        if event.block.type == "minecraft:respawn_anchor":# Якорь возрождения
            name = event.player.name
            blocktype = event.block.type
            action = "Взаимодействие"
            x = event.block.x
            y = event.block.y
            z = event.block.z
            type = f"{blocktype}, использовано {event.item}"
            world = event.block.location.dimension.name
            record_data(name, action, x, y, z, type,world)
       
# Событие разрушения блока
    @event_handler
    def blockbreak(self, event: BlockBreakEvent):
        def record_data(name, action, x, y, z,type,world,blockdata):
            # """Записать действия игрока в файл data.json"""
            interaction = {
                'name': name,
                'action': action,
                'coordinates': {'x': x, 'y': y, 'z': z},
                'time': datetime.now().isoformat(),  # Записать текущее время
                'type': type,
                'world': world,
                'blockdata': blockdata
            }  
            with lock:  # Обеспечить безопасность потока
                breakrec_data.append(interaction)                  
            #threading.Thread(target=write_to_file).start()
            
            # Записывать только природные блоки
        if blockrec == 1:
            if event.block.type in [
                "minecraft:stone","minecraft:granite","minecraft:diorite","minecraft:andesite","minecraft:grass_block","minecraft:dirt","minecraft:coarse_dirt","minecraft:podzol",
                "minecraft:sand","minecraft:red_sand","minecraft:gravel","minecraft:gold_ore","minecraft:iron_ore","minecraft:coal_ore","minecraft:oak_log","minecraft:spruce_log",
                "minecraft:birch_log","minecraft:jungle_log","minecraft:oak_leaves","minecraft:spruce_leaves","minecraft:birch_leaves","minecraft:jungle_leaves","minecraft:sponge","minecraft:wet_sponge",
                "minecraft:lapis_ore","minecraft:cobweb","minecraft:short_grass","minecraft:fern","minecraft:dead_bush","minecraft:dandelion","minecraft:poppy","minecraft:blue_orchid",
                "minecraft:allium","minecraft:azure_bluet","minecraft:red_tulip","minecraft:orange_tulip","minecraft:white_tulip","minecraft:oxeye_daisy","minecraft:brown_mushroom","minecraft:obsidian",
                "minecraft:diamond_ore","minecraft:redstone_ore","minecraft:snow","minecraft:ice","minecraft:snow_block","minecraft:cactus","minecraft:clay","minecraft:pumpkin","minecraft:netherrack",
                "minecraft:glowstone","minecraft:brown_mushroom_block","minecraft:red_mushroom_block","minecraft:mushroom_stem","minecraft:melon","minecraft:vine","minecraft:mycelium","minecraft:lily_pad",
                "minecraft:nether_wart","minecraft:end_stone","minecraft:emerald_ore","minecraft:nether_quartz_ore","minecraft:acacia_leaves","minecraft:dark_oak_leaves",
                "minecraft:acacia_log","minecraft:dark_oak_log","minecraft:prismarine","minecraft:hay_block",
                "minecraft:packed_ice","minecraft:sunflower","minecraft:lilac","minecraft:tall_grass","minecraft:large_fern","minecraft:rose_bush",
                "minecraft:peony","minecraft:red_sandstone","minecraft:chorus_plant","minecraft:chorus_flower","minecraft:dirt_path","minecraft:magma_block",
                "minecraft:nether_wart_block","minecraft:bone_block","minecraft:blue_ice","minecraft:seagrass","minecraft:tall_seagrass","minecraft:kelp",
                "minecraft:bamboo","minecraft:cornflower","minecraft:lily_of_the_valley","minecraft:sweet_berry_bush","minecraft:crimson_nylium","minecraft:crimson_stem",
                "minecraft:crimson_fungus","minecraft:crimson_roots","minecraft:warped_nylium","minecraft:warped_stem","minecraft:warped_fungus","minecraft:warped_roots","minecraft:warped_wart_block",
                "minecraft:ancient_debris","minecraft:crying_obsidian","minecraft:blackstone","minecraft:nether_gold_ore","minecraft:basalt","minecraft:nether_sprouts",
                "minecraft:weeping_vines","minecraft:twisting_vines","minecraft:shroomlight","minecraft:soul_soil","minecraft:azalea","minecraft:flowering_azalea","minecraft:azalea_leaves",
                "minecraft:flowering_azalea_leaves","minecraft:moss_carpet","minecraft:moss_block","minecraft:hanging_roots","minecraft:spore_blossom","minecraft:small_dripleaf",
                "minecraft:big_dripleaf","minecraft:glow_lichen","minecraft:small_amethyst_bud","minecraft:medium_amethyst_bud","minecraft:medium_amethyst_bud","minecraft:large_amethyst_bud",
                "minecraft:amethyst_cluster","minecraft:pointed_dripstone","minecraft:deepslate","minecraft:calcite","minecraft:tuff","minecraft:dripstone_block","minecraft:rooted_dirt",
                "minecraft:deepslate_coal_ore","minecraft:deepslate_iron_ore","minecraft:copper_ore","minecraft:deepslate_copper_ore","minecraft:deepslate_gold_ore","minecraft:deepslate_redstone_ore",
                "minecraft:deepslate_emerald_ore","minecraft:deepslate_lapis_ore","minecraft:deepslate_diamond_ore","minecraft:amethyst_block","minecraft:budding_amethyst","minecraft:mangrove_log",
                "minecraft:mangrove_leaves","minecraft:mangrove_roots","minecraft:muddy_mangrove_roots","minecraft:mud","minecraft:cherry_log","minecraft:cherry_leaves","minecraft:torchflower","minecraft:pink_petals",
                "minecraft:pitcher_plant"
            ]:
                name = event.player.name
                action = "Разрушить"
                x = event.block.x
                y = event.block.y
                z = event.block.z
                type = event.block.type
                world = event.block.location.dimension.name
                turnblock = event.block.data.block_states
                blockdata = f" [{', '.join([f'"{key}"={value}' if isinstance(value, (bool, int, float)) else f'"{key}"="{value}"' for key, value in turnblock.items()])}]"
                record_data(name, action, x, y, z,type,world,blockdata)

        # Полностью открыть
        if blockrec == 2:
            if True:
                name = event.player.name
                action = "Разрушить"
                x = event.block.x
                y = event.block.y
                z = event.block.z
                type = event.block.type
                world = event.block.location.dimension.name
                turnblock = event.block.data.block_states
                blockdata = f" [{', '.join([f'"{key}"={value}' if isinstance(value, (bool, int, float)) else f'"{key}"="{value}"' for key, value in turnblock.items()])}]"
                record_data(name, action, x, y, z,type,world,blockdata)
                
        # Записывать только искусственные блоки
        if blockrec == 4:
            if event.block.type in [
                "minecraft:stone","minecraft:granite","minecraft:diorite","minecraft:andesite","minecraft:grass_block","minecraft:dirt","minecraft:coarse_dirt","minecraft:podzol",
                "minecraft:sand","minecraft:red_sand","minecraft:gravel","minecraft:gold_ore","minecraft:iron_ore","minecraft:coal_ore","minecraft:oak_log","minecraft:spruce_log",
                "minecraft:birch_log","minecraft:jungle_log","minecraft:oak_leaves","minecraft:spruce_leaves","minecraft:birch_leaves","minecraft:jungle_leaves","minecraft:sponge","minecraft:wet_sponge",
                "minecraft:lapis_ore","minecraft:cobweb","minecraft:short_grass","minecraft:fern","minecraft:dead_bush","minecraft:dandelion","minecraft:poppy","minecraft:blue_orchid",
                "minecraft:allium","minecraft:azure_bluet","minecraft:red_tulip","minecraft:orange_tulip","minecraft:white_tulip","minecraft:oxeye_daisy","minecraft:brown_mushroom","minecraft:obsidian",
                "minecraft:diamond_ore","minecraft:redstone_ore","minecraft:snow","minecraft:ice","minecraft:snow_block","minecraft:cactus","minecraft:clay","minecraft:pumpkin","minecraft:netherrack",
                "minecraft:glowstone","minecraft:brown_mushroom_block","minecraft:red_mushroom_block","minecraft:mushroom_stem","minecraft:melon","minecraft:vine","minecraft:mycelium","minecraft:lily_pad",
                "minecraft:nether_wart","minecraft:end_stone","minecraft:emerald_ore","minecraft:nether_quartz_ore","minecraft:acacia_leaves","minecraft:dark_oak_leaves",
                "minecraft:acacia_log","minecraft:dark_oak_log","minecraft:prismarine","minecraft:hay_block",
                "minecraft:packed_ice","minecraft:sunflower","minecraft:lilac","minecraft:tall_grass","minecraft:large_fern","minecraft:rose_bush",
                "minecraft:peony","minecraft:red_sandstone","minecraft:chorus_plant","minecraft:chorus_flower","minecraft:dirt_path","minecraft:magma_block",
                "minecraft:nether_wart_block","minecraft:bone_block","minecraft:blue_ice","minecraft:seagrass","minecraft:tall_seagrass","minecraft:kelp",
                "minecraft:bamboo","minecraft:cornflower","minecraft:lily_of_the_valley","minecraft:sweet_berry_bush","minecraft:crimson_nylium","minecraft:crimson_stem",
                "minecraft:crimson_fungus","minecraft:crimson_roots","minecraft:warped_nylium","minecraft:warped_stem","minecraft:warped_fungus","minecraft:warped_roots","minecraft:warped_wart_block",
                "minecraft:ancient_debris","minecraft:crying_obsidian","minecraft:blackstone","minecraft:nether_gold_ore","minecraft:basalt","minecraft:nether_sprouts",
                "minecraft:weeping_vines","minecraft:twisting_vines","minecraft:shroomlight","minecraft:soul_soil","minecraft:azalea","minecraft:flowering_azalea","minecraft:azalea_leaves",
                "minecraft:flowering_azalea_leaves","minecraft:moss_carpet","minecraft:moss_block","minecraft:hanging_roots","minecraft:spore_blossom","minecraft:small_dripleaf",
                "minecraft:big_dripleaf","minecraft:glow_lichen","minecraft:small_amethyst_bud","minecraft:medium_amethyst_bud","minecraft:medium_amethyst_bud","minecraft:large_amethyst_bud",
                "minecraft:amethyst_cluster","minecraft:pointed_dripstone","minecraft:deepslate","minecraft:calcite","minecraft:tuff","minecraft:dripstone_block","minecraft:rooted_dirt",
                "minecraft:deepslate_coal_ore","minecraft:deepslate_iron_ore","minecraft:copper_ore","minecraft:deepslate_copper_ore","minecraft:deepslate_gold_ore","minecraft:deepslate_redstone_ore",
                "minecraft:deepslate_emerald_ore","minecraft:deepslate_lapis_ore","minecraft:deepslate_diamond_ore","minecraft:amethyst_block","minecraft:budding_amethyst","minecraft:mangrove_log",
                "minecraft:mangrove_leaves","minecraft:mangrove_roots","minecraft:muddy_mangrove_roots","minecraft:mud","minecraft:cherry_log","minecraft:cherry_leaves","minecraft:torchflower","minecraft:pink_petals",
                "minecraft:pitcher_plant"
            ]:
                return False
            else :
                name = event.player.name
                action = "Разрушить"
                x = event.block.x
                y = event.block.y
                z = event.block.z
                type = event.block.type
                world = event.block.location.dimension.name
                turnblock = event.block.data.block_states
                blockdata = f" [{', '.join([f'"{key}"={value}' if isinstance(value, (bool, int, float)) else f'"{key}"="{value}"' for key, value in turnblock.items()])}]"
                record_data(name, action, x, y, z,type,world,blockdata)
                
# Событие удара по существу
    @event_handler
    def animal(self, event: ActorKnockbackEvent):
        def record_data(name, action, x, y, z,type,world):
            # """Записать действия игрока в файл data.json"""
            interaction = {
                'name': name,
                'action': action,
                'coordinates': {'x': x, 'y': y, 'z': z},
                'time': datetime.now().isoformat(),  # Записать текущее время
                'type': type,
                'world': world
            }  
            with lock:  # Обеспечить безопасность потока
                animalrec_data.append(interaction)                  
            #threading.Thread(target=write_to_file).start()
            
            # Записывать только важные существа
        if nbanimal == 1:
            if event.actor.name in [
                "Horse","Pig","Wolf","Cat","Sniffer","Parrot","Donkey","Mule","Villager","Allay"
            ]:
                name = event.source.name
                action = "Атака"
                x = event.actor.location.x
                y = event.actor.location.y
                z = event.actor.location.z
                type = event.actor.name
                world = event.actor.location.dimension.name
                record_data(name,action, x, y, z,type,world)

        # Полностью открыть
        else:
            if True:
                name = event.source.name
                action = "Атака"
                x = event.actor.location.x
                y = event.actor.location.y
                z = event.actor.location.z
                type = event.actor.name
                world = event.actor.location.dimension.name
                record_data(name,action, x, y, z,type,world)   
 

# Событие размещения блока
    @event_handler
    def blockplace(self, event: BlockPlaceEvent):
        def record_data(name, action, x, y, z,type,world):
            # """Записать действия игрока в файл data.json"""
            interaction = {
                'name': name,
                'action': action,
                'coordinates': {'x': x, 'y': y, 'z': z},
                'time': datetime.now().isoformat(),  # Записать текущее время
                'type': type,
                'world': world
            }  
            with lock:  # Обеспечить безопасность потока
                placerec_data.append(interaction)                  
        #threading.Thread(target=write_to_file).start()
        name = event.player.name
        action = "Разместить"
        x = event.block_placed_state.x
        y = event.block_placed_state.y
        z = event.block_placed_state.z
        type = event.block_placed_state.type
        world = event.block_placed_state.location.dimension.name
        record_data(name,action, x, y, z,type,world)
        
        
    # Событие взаимодействия с существом
    @event_handler
    def actorjh(self, event: PlayerInteractActorEvent):
        def record_data(name, action, x, y, z,type,world):
            # """Записать действия игрока в файл data.json"""
            interaction = {
                'name': name,
                'action': action,
                'coordinates': {'x': x, 'y': y, 'z': z},
                'time': datetime.now().isoformat(),  # Записать текущее время
                'type': type,
                'world': world
            }  
            with lock:  # Обеспечить безопасность потока
                actorrec_data.append(interaction)                  
        #threading.Thread(target=write_to_file).start()
        name = event.player.name
        action = "Взаимодействие"
        x = event.actor.location.block_x
        y = event.actor.location.block_y
        z = event.actor.location.block_z
        type = event.actor.name
        world = event.actor.location.dimension.name
        record_data(name,action, x, y, z,type,world)
        
# Не переведено, т.к. не является рабочей частью
# 用于调试的事件
#    @event_handler
#    def blocktest(self,event: PlayerInteractEvent ):  
#        player = event.player
#        inv = player.inventory
#        self.server.broadcast_message(ColorFormat.YELLOW + f"{event.player.name}" + "位置" f"{event.block.x}"" " + f"{event.block.y}"" " + f"{event.block.z}" + f"{event.block.type}" + f"{event.block.location.dimension.name}" + f"{event.item}" + f"{inv}")
# 用于调试的事件
#    @event_handler
#    def test(self,event: BlockBreakEvent): 
#        current_tps = self.server.current_tps
#        self.server.broadcast_message(f"{current_tps}") 
#        turnblock = event.block.data.block_states
#        blockdata = f" [{', '.join([f'{key}={value}' if isinstance(value, (bool, int, float)) else f'"{key}"="{value}"' for key, value in turnblock.items()])}]"
#        turnblock = event.block.data.block_states
#        blockdata = ', '.join([f'"{key}"={value}' if isinstance(value, (bool, int, float)) else f'"{key}"="{value}"' for key, value in turnblock.items()])
#        blockdata = f" [{', '.join([f'"{key}"={value}' if isinstance(value, (bool, int, float)) else f'"{key}"="{value}"' for key, value in turnblock.items()])}]"
#        self.server.broadcast_message(ColorFormat.YELLOW + f"{event.block.type} blockdata: {blockdata}")
# 用于调试的命令发送事件
#    @event_handler
#    def test(self,event: PlayerCommandEvent):  
#        self.server.broadcast_message(ColorFormat.YELLOW + f"{event.player.name}" + f"{PlayerCommandEvent.command}" + " " + f"{Player.address}")
        
# Записать словарь команд игрока


    # Проверка команд на спам: если за 10 секунд отправлено 12 и более команд, это считается спамом
    @event_handler    
    def commandsban(self, event: PlayerCommandEvent):
        def ban(playername,reason):
            # Проверить, существует ли файл
            if not os.path.exists(banlist):
                # Если файл не существует, создать пустой файл черного списка
                with open(banlist, 'w') as file:
                    json.dump({}, file)

            # Прочитать файл черного списка
            with open(banlist, 'r') as file:
                blacklist = json.load(file)
            # Записать имя игрока и причину в черный список
            blacklist[playername] = reason
            # Записать обновлённый черный список обратно в файл
            with open(banlist, 'w', encoding='utf-8') as file:  # Определить кодировку UTF-8
                json.dump(blacklist, file, ensure_ascii=False, indent=4)
            self.logger.info(f"Игрок {playername} был добавлен в черный список, причина: {reason}")
        player_name = event.player.name
        #command = PlayerCommandEvent.command
        current_time = tm.time()
        
        # Записать команду игрока и время её выполнения
        player_commands[player_name].append(current_time)
        
        # Сохранять команды за последние 10 секунд
        player_commands[player_name] = [t for t in player_commands[player_name] if current_time - t <= 10]
        
        # Проверить, превышает ли количество команд за последние 10 секунд установленный порог
        if len(player_commands[player_name]) > 12:  # Пороговое значение — 12 команд
            reason = "Вы забанены за подозрение в отправке множества команд за короткий промежуток времени"
            event.player.kick(reason)
            #self.logger.info(f"{player_name}" + f"{reason}")
            playername = player_name
            ban(playername,reason)
            self.server.broadcast_message(f"Игрок {playername} забанен за подозрение в отправке множества команд за короткий промежуток времени")
            player_commands[player_name] = []  # Очистить записи
            
    # Проверить спам в чате: если за 10 секунд отправлено 6 и более сообщений, это считается спамом
    @event_handler    
    def chatban(self, event: PlayerChatEvent):
        def ban(playername,reason):
            # Проверить, существует ли файл
            if not os.path.exists(banlist):
                # Если файл не существует, создать пустой файл черного списка
                with open(banlist, 'w',encoding='utf-8') as file:
                    json.dump({}, file)

            # Прочитать файл черного списка
            with open(banlist, 'r', encoding='utf-8') as file:
                blacklist = json.load(file)
            # Записать имя игрока и причину в черный список
            timestamp = datetime.now().isoformat()  # Использовать текущий временной штамп в качестве значения по умолчанию
            # Создать новый элемент, включающий всю информацию
            entry = {
                "reason": reason,
                "timestamp": timestamp
            }
            blacklist[playername] = entry

            # Записать обновлённый чёрный список в файл
            with open(banlist, 'w', encoding='utf-8') as file:  # Определить кодировку UTF-8
                json.dump(blacklist, file, ensure_ascii=False, indent=4)
            self.logger.info(f"Игрок {playername} был добавлен в чёрный список, причина: {reason}")
        player_name = event.player.name
        #command = PlayerCommandEvent.command
        current_time = tm.time()
        
        # Записать команду игрока и время её выполнения
        player_message[player_name].append(current_time)
        
        # Сохранять команды за последние 10 секунд
        player_message[player_name] = [t for t in player_message[player_name] if current_time - t <= 10]
        
        # Проверить, превышает ли количество команд за 60 секунд установленный порог
        if len(player_message[player_name]) > 6:  # Пороговое значение — 6
            reason = "Вы были забанены за подозрение в отправке нескольких сообщений за короткое время"
            event.player.kick(reason)
            #self.logger.info(f"{player_name}" + f"{reason}")
            playername = player_name
            ban(playername,reason)
            self.server.broadcast_message(f"Игрок {playername} был забанен за подозрение в отправке нескольких сообщений за короткое время")
            player_message[player_name] = []  # Очистить записи
        
    # Проверка забаненных игроков
    @event_handler
    def banjoin(self, event: PlayerJoinEvent):
        playername = event.player.name
        player = event.player
        device_id = getattr(player,'device_id', 'Неизвестный идентификатор устройства')
        # Проверить, существует ли файл
        if not os.path.exists(banlist):
            # Если файл не существует, создать пустой файл черного списка
            with open(banlist, 'w') as file:
                json.dump({}, file)
        if not os.path.exists(banidlist):
            # Если файл не существует, создать пустой файл чёрного списка
            with open(banidlist, 'w') as file:
                json.dump({}, file)

        # Прочитать файл черного списка
        with open(banlist, 'r', encoding='utf-8') as file:
            blacklist = json.load(file)
        with open(banidlist, 'r', encoding='utf-8') as file:
            blackidlist = json.load(file)
        
        # Проверить, находится ли игрок в чёрном списке
        if playername in blacklist:
            entry = blacklist[playername]
            reason = entry.get("reason")
            timestamp = entry.get("timestamp")
            event.player.kick(f"Вы были забанены, причина: {reason}, время блокировки: {timestamp}")
            self.logger.info(f"Игрок {playername} находится в списке забаненных, был исключён, причина блокировки: {reason}")
        # Проверить, находится ли идентификатор устройства игрока в чёрном списке
        if device_id in blackidlist:
            entry = blackidlist[device_id]
            timestamp = entry.get("timestamp")
            event.player.kick(f"Ваше устройство было заблокировано {timestamp}")
            self.logger.info(f"Заблокированное устройство с ID {device_id} попыталось присоединиться к серверу, было исключено")
        else:
            return False
        
    @event_handler
    def joinmsg(self, event: PlayerJoinEvent):
        player = event.player
        pname = player.name
        #pip = player.address.hostname
        pid = getattr(player, 'device_id', 'Неизвестный идентификатор устройства')
        pos = getattr(player, 'device_os', 'Неизвестная система')
        self.logger.info(f"{ColorFormat.YELLOW}Игрок {pname} (ID устройства: {pid}, название системы: {pos}) присоединился к игре")
        
            
        
player_commands = defaultdict(list)
player_message = defaultdict(list)
