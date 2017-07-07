# -*- coding: utf-8 -*-
#
#  Copyright 2013 Grigoriy Kramarenko <root@rosix.ru>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  

from __future__ import unicode_literals

### Протокол работы ICL ###

VERSION = (1, 1) # 2012-05-28
__version__ = '%s.%s' % VERSION

__all__ = ('ICL_COMMANDS', 'BUGS', 'ICL_MODES', 'ICL_SUBMODES',
    'ICL_FLAGS', 'FP_FLAGS')

### Команды ICL ###
#                     Разрядность денежных величин
# Все суммы в данном разделе – целые величины, указанные в «мде». МДЕ –
# минимальная денежная единица. С 01.01.1998 в Российской Федерации 1 МДЕ
# равна 1 копейке (до 01.01.1998 1 МДЕ была равна 1 рублю).
#
#                       Формат передачи значений
# Все числовые величины передаются в двоичном формате, если не указано
# другое. Первым передается самый младший байт, последним самый старший
# байт.
#
# При передаче даты (3 байта) сначала передаѐтся число (1 байт – ДД),
# затем месяц (2 байта – ММ), и последним – год (1 байт – ГГ).
#
# При передаче времени (3 байта) первым байтом передаются часы (1 байт
# – ЧЧ), затем минуты (2 байта – ММ), и последними передаются секунды (1
# байт – СС).
#
#                          Ответы и коды ошибок
# Ответное сообщение содержит корректную информацию, если код ошибки
# (второй байт в ответном сообщении) 0.
# Если код ошибки не 0, передается только код команды и код
# ошибки – 2 байта.
#

ICL_COMMANDS = {
    0x01: 'Запрос дампа',
    0x02: 'Запрос данных',
    0x03: 'Прерывание выдачи данных',
    0x0D: 'Фискализация (перерегистрация) с длинным РНМ',
    0x0E: 'Ввод длинного заводского номера',
    0x0F: 'Запрос длинного заводского номера и длинного РНМ',

    0x10: 'Короткий запрос состояния ФР',
    0x11: 'Запрос состояния ФР',
    0x12: 'Печать жирной строки',
    0x13: 'Гудок',
    0x14: 'Установка параметров обмена',
    0x15: 'Чтение параметров обмена',
    0x16: 'Технологическое обнуление',
    0x17: 'Печать строки',
    0x18: 'Печать заголовка документа',
    0x19: 'Тестовый прогон',
    0x1A: 'Запрос денежного регистра',
    0x1B: 'Запрос операционного регистра',
    0x1C: 'Запись лицензии',
    0x1D: 'Чтение лицензии',
    0x1E: 'Запись таблицы',
    0x1F: 'Чтение таблицы',

    0x20: 'Запись положения десятичной точки',
    0x21: 'Программирование времени',
    0x22: 'Программирование даты',
    0x23: 'Подтверждение программирования даты',
    0x24: 'Инициализация таблиц начальными значениями',
    0x25: 'Отрезка чека',
    0x26: 'Прочитать параметры шрифта',
    0x27: 'Общее гашение',
    0x28: 'Открыть денежный ящик',
    0x29: 'Протяжка',
    0x2A: 'Выброс подкладного документа',
    0x2B: 'Прерывание тестового прогона',
    0x2C: 'Снятие показаний операционных регистров',
    0x2D: 'Запрос структуры таблицы',
    0x2E: 'Запрос структуры поля',
    0x2F: 'Печать строки данным шрифтом',

    0x40: 'Суточный отчет без гашения',
    0x41: 'Суточный отчет с гашением',
    0x42: 'Отчёт по секциям',
    0x43: 'Отчёт по налогам',

    0x50: 'Внесение',
    0x51: 'Выплата',
    0x52: 'Печать клише',
    0x53: 'Конец документа',
    0x53: 'Печать рекламного текста',

    0x60: 'Ввод заводского номера',
    0x61: 'Инициализация ФП',
    0x62: 'Запрос суммы записей в ФП',
    0x63: 'Запрос даты последней записи в ФП',
    0x64: 'Запрос диапазона дат и смен',
    0x65: 'Фискализация (перерегистрация)',
    0x66: 'Фискальный отчет по диапазону дат',
    0x67: 'Фискальный отчет по диапазону смен',
    0x68: 'Прерывание полного отчета',
    0x69: 'Чтение параметров фискализации (перерегистрации)',

    0x70: 'Открыть фискальный подкладной документ',
    0x71: 'Открыть стандартный фискальный подкладной документ',
    0x72: 'Формирование операции на подкладном документе',
    0x73: 'Формирование стандартной операции на подкладном документе',
    0x74: 'Формирование скидки/надбавки на подкладном документе',
    0x75: 'Формирование стандартной скидки/надбавки на подкладном документе',
    0x76: 'Формирование закрытия чека на подкладном документе',
    0x77: 'Формирование стандартного закрытия чека на подкладном документе',
    0x78: 'Конфигурация подкладного документа',
    0x79: 'Установка стандартной конфигурации подкладного документа',
    0x7A: 'Заполнение буфера подкладного документа нефискальной информацией',
    0x7B: 'Очистка строки буфера подкладного документа от нефискальной информации',
    0x7C: 'Очистка всего буфера подкладного документа от нефискальной информации',
    0x7D: 'Печать подкладного документа',
    0x7E: 'Общая конфигурация подкладного документа',

    0x80: 'Продажа',
    0x81: 'Покупка',
    0x82: 'Возврат продажи',
    0x83: 'Возврат покупки',
    0x84: 'Сторно',
    0x85: 'Закрытие чека',
    0x86: 'Скидка',
    0x87: 'Надбавка',
    0x88: 'Аннулирование чека',
    0x89: 'Подытог чека',
    0x8A: 'Сторно скидки',
    0x8B: 'Сторно надбавки',
    0x8C: 'Повтор документа',
    0x8D: 'Открыть чек',

    0x90: 'Формирование чека отпуска нефтепродуктов в режиме предоплаты заданной дозы',
    0x91: 'Формирование чека отпуска нефтепродуктов в режиме предоплаты на заданную сумму',
    0x92: 'Формирование чека коррекции при неполном отпуске нефтепродуктов',
    0x93: 'Задание дозы РК в миллилитрах',
    0x94: 'Задание дозы РК в денежных единицах',
    0x95: 'Продажа нефтепродуктов',
    0x96: 'Останов РК',
    0x97: 'Пуск РК',
    0x98: 'Сброс РК',
    0x99: 'Сброс всех ТРК',
    0x9A: 'Задание параметров РК',
    0x9B: 'Считать литровый суммарный счетчик',

    0x9E: 'Запрос текущей дозы РК',
    0x9F: 'Запрос состояния РК',

    0xA0: 'Отчет ЭКЛЗ по отделам в заданном диапазоне дат',
    0xA1: 'Отчет ЭКЛЗ по отделам в заданном диапазоне номеров смен',
    0xA2: 'Отчет ЭКЛЗ по закрытиям смен в заданном диапазоне дат',
    0xA3: 'Отчет ЭКЛЗ по закрытиям смен в заданном диапазоне номеров смен',
    0xA4: 'Итоги смены по номеру смены ЭКЛЗ',
    0xA5: 'Платежный документ из ЭКЛЗ по номеру КПК',
    0xA6: 'Контрольная лента из ЭКЛЗ по номеру смены',
    0xA7: 'Прерывание полного отчета ЭКЛЗ или контрольной ленты ЭКЛЗ или печати платежного документа ЭКЛЗ',
    0xA8: 'Итог активизации ЭКЛЗ',
    0xA9: 'Активизация ЭКЛЗ',
    0xAA: 'Закрытие архива ЭКЛЗ',
    0xAB: 'Запрос регистрационного номера ЭКЛЗ',
    0xAC: 'Прекращение ЭКЛЗ',
    0xAD: 'Запрос состояния по коду 1 ЭКЛЗ',
    0xAE: 'Запрос состояния по коду 2 ЭКЛЗ',
    0xAF: 'Тест целостности архива ЭКЛЗ',

    0xB0: 'Продолжение печати',
    0xB1: 'Запрос версии ЭКЛЗ',
    0xB2: 'Инициализация архива ЭКЛЗ',
    0xB3: 'Запрос данных отчёта ЭКЛЗ',
    0xB4: 'Запрос контрольной ленты ЭКЛЗ',
    0xB5: 'Запрос документа ЭКЛЗ',
    0xB6: 'Запрос отчёта ЭКЛЗ по отделам в заданном диапазоне дат',
    0xB7: 'Запрос отчёта ЭКЛЗ по отделам в заданном диапазоне номеров смен',
    0xB8: 'Запрос отчёта ЭКЛЗ по закрытиям смен в заданном диапазоне дат',
    0xB9: 'Запрос отчёта ЭКЛЗ по закрытиям смен в заданном диапазоне номеров смен',
    0xBA: 'Запрос в ЭКЛЗ итогов смены по номеру смены',
    0xBB: 'Запрос итога активизации ЭКЛЗ',
    0xBC: 'Вернуть ошибку ЭКЛЗ',

    0xC0: 'Загрузка графики',
    0xC1: 'Печать графики',
    0xC2: 'Печать штрих-кода',
    0xC3: 'Загрузка расширенной графики',
    0xC4: 'Печать расширенной графики',
    0xC5: 'Печать линии',
    0xC6: 'Суточный отчет с гашением в буфер',
    0xC7: 'Распечатать отчет из буфера',
    0xC8: 'Запрос количества строк в буфере печати',
    0xC9: 'Получить строку буфера печати ',
    0xCA: 'Очистить буфер печати ',

    0xD0: 'Запрос состояния ФР IBM длинный',
    0xD1: 'Коды ошибок',

    0xDD: 'Загрузка данных',
    0xDE: 'Печать многомерного штрих-кода',

    0xE0: 'Открыть смену',
    0xE1: 'Допечатать ПД',
    0xE2: 'Открыть нефискальный документ',
    0xE3: 'Закрыть нефискальный документ',
    0xE4: 'Печать Реквизита',
    0xE5: 'Запрос состояния купюроприемника',
    0xE6: 'Запрос регистров купюроприемника',
    0xE7: 'Отчет по купюроприемнику',
    0xE8: 'Оперативный отчет НИ',

    0xF0: 'Управление заслонкой',
    0xF1: 'Выдать чек',

    0xF3: 'Установить пароль ЦТО',

    0xFC: 'Получить тип устройства',
    0xFD: 'Управление портом дополнительного внешнего устройства',
}

### Коды ошибок ###
# В первом параметре значений указывается источник возникновения ошибки:
# фискальная память (ФП), электронная контрольная лента защищѐнная
# (ЭКЛЗ) или сама ККТ.
BUGS = {
    0x00: ('ФП', 'Ошибок нет'),
    0x01: ('ФП', 'Неисправен накопитель ФП 1, ФП 2 или часы'),
    0x02: ('ФП', 'Отсутствует ФП 1'),
    0x03: ('ФП', 'Отсутствует ФП 2'),
    0x04: ('ФП', 'Некорректные параметры в команде обращения к ФП'),
    0x05: ('ФП', 'Нет запрошенных данных'),
    0x06: ('ФП', 'ФП в режиме вывода данных'),
    0x07: ('ФП', 'Некорректные параметры в команде для данной реализации ФП'),
    0x08: ('ФП', 'Команда не поддерживается в данной реализации ФП'),
    0x09: ('ФП', 'Некорректная длина команды'),
    0x0A: ('ФП', 'Формат данных не BCD'),
    0x0B: ('ФП', 'Неисправна ячейка памяти ФП при записи итога'),

    0x11: ('ФП', 'Не введена лицензия'),
    0x12: ('ФП', 'Заводской номер уже введен'),
    0x13: ('ФП', 'Текущая дата меньше даты последней записи в ФП'),
    0x14: ('ФП', 'Область сменных итогов ФП переполнена'),
    0x15: ('ФП', 'Смена уже открыта'),
    0x16: ('ФП', 'Смена не открыта'),
    0x17: ('ФП', 'Номер первой смены больше номера последней смены'),
    0x18: ('ФП', 'Дата первой смены больше даты последней смены'),
    0x19: ('ФП', 'Нет данных в ФП'),
    0x1A: ('ФП', 'Область перерегистраций в ФП переполнена'),
    0x1B: ('ФП', 'Заводской номер не введен'),
    0x1C: ('ФП', 'В заданном диапазоне есть поврежденная запись'),
    0x1D: ('ФП', 'Повреждена последняя запись сменных итогов'),
    0x1E: ('ФП', 'Область перерегистраций ФП переполнена'),
    0x1F: ('ФП', 'Отсутствует память регистров'),

    0x20: ('ФП', 'Переполнение денежного регистра при добавлении'),
    0x21: ('ФП', 'Вычитаемая сумма больше содержимого денежного регистра'),
    0x22: ('ФП', 'Неверная дата'),
    0x23: ('ФП', 'Нет записи активизации'),
    0x24: ('ФП', 'Область активизаций переполнена'),
    0x25: ('ФП', 'Нет активизации с запрашиваемым номером'),
    0x26: ('ФП', 'В ФП присутствует 3 или более битых записей сменных итогов'),
    0x27: ('ФП', 'Признак несовпадения КС, з/н, перерегистраций или активизаций'),

    0x2B: ('ККТ', 'Невозможно отменить предыдущую команду'),
    0x2C: ('ККТ', 'Обнулѐнная касса (повторное гашение невозможно)'),
    0x2D: ('ККТ', 'Сумма чека по секции меньше суммы сторно'),
    0x2E: ('ККТ', 'В ККТ нет денег для выплаты'),

    0x30: ('ККТ', 'ККТ заблокирован, ждет ввода пароля налогового инспектора'),

    0x32: ('ККТ', 'Требуется выполнение общего гашения'),
    0x33: ('ККТ', 'Некорректные параметры в команде'),
    0x34: ('ККТ', 'Нет данных'),
    0x35: ('ККТ', 'Некорректный параметр при данных настройках'),
    0x36: ('ККТ', 'Некорректные параметры в команде для данной реализации ККТ'),
    0x37: ('ККТ', 'Команда не поддерживается в данной реализации ККТ'),
    0x38: ('ККТ', 'Ошибка в ПЗУ'),
    0x39: ('ККТ', 'Внутренняя ошибка ПО ККТ'),
    0x3A: ('ККТ', 'Переполнение накопления по надбавкам в смене'),
    0x3B: ('ККТ', 'Переполнение накопления в смене'),
    0x3C: ('ККТ', 'ЭКЛЗ: неверный регистрационный номер'),
    0x3D: ('ККТ', 'Смена не открыта – операция невозможна'),
    0x3E: ('ККТ', 'Переполнение накопления по секциям в смене'),
    0x3F: ('ККТ', 'Переполнение накопления по скидкам в смене'),

    0x40: ('ККТ', 'Переполнение диапазона скидок'),
    0x41: ('ККТ', 'Переполнение диапазона оплаты наличными'),
    0x42: ('ККТ', 'Переполнение диапазона оплаты типом 2'),
    0x43: ('ККТ', 'Переполнение диапазона оплаты типом 3'),
    0x44: ('ККТ', 'Переполнение диапазона оплаты типом 4'),
    0x45: ('ККТ', 'Cумма всех типов оплаты меньше итога чека'),
    0x46: ('ККТ', 'Не хватает наличности в кассе'),
    0x47: ('ККТ', 'Переполнение накопления по налогам в смене'),
    0x48: ('ККТ', 'Переполнение итога чека'),
    0x49: ('ККТ', 'Операция невозможна в открытом чеке данного типа'),
    0x4A: ('ККТ', 'Открыт чек – операция невозможна'),
    0x4B: ('ККТ', 'Буфер чека переполнен'),
    0x4C: ('ККТ', 'Переполнение накопления по обороту налогов в смене'),
    0x4D: ('ККТ', 'Вносимая безналичной оплатой сумма больше суммы чека'),
    0x4E: ('ККТ', 'Смена превысила 24 часа'),
    0x4F: ('ККТ', 'Неверный пароль'),

    0x50: ('ККТ', 'Идет печать предыдущей команды'),
    0x51: ('ККТ', 'Переполнение накоплений наличными в смене'),
    0x52: ('ККТ', 'Переполнение накоплений по типу оплаты 2 в смене'),
    0x53: ('ККТ', 'Переполнение накоплений по типу оплаты 3 в смене'),
    0x54: ('ККТ', 'Переполнение накоплений по типу оплаты 4 в смене'),
    0x55: ('ККТ', 'Чек закрыт – операция невозможна'),
    0x56: ('ККТ', 'Нет документа для повтора'),
    0x57: ('ККТ', 'ЭКЛЗ: количество закрытых смен не совпадает с ФП'),
    0x58: ('ККТ', 'Ожидание команды продолжения печати'),
    0x59: ('ККТ', 'Документ открыт другим оператором'),
    0x5A: ('ККТ', 'Скидка превышает накопления в чеке'),
    0x5B: ('ККТ', 'Переполнение диапазона надбавок'),
    0x5C: ('ККТ', 'Понижено напряжение 24В'),
    0x5D: ('ККТ', 'Таблица не определена'),
    0x5E: ('ККТ', 'Некорректная операция'),
    0x5F: ('ККТ', 'Отрицательный итог чека'),

    0x60: ('ККТ', 'Переполнение при умножении'),
    0x61: ('ККТ', 'Переполнение диапазона цены'),
    0x62: ('ККТ', 'Переполнение диапазона количества'),
    0x63: ('ККТ', 'Переполнение диапазона отдела'),
    0x64: ('ККТ', 'ФП отсутствует'),
    0x65: ('ККТ', 'Не хватает денег в секции'),
    0x66: ('ККТ', 'Переполнение денег в секции'),
    0x67: ('ККТ', 'Ошибка связи с ФП'),
    0x68: ('ККТ', 'Не хватает денег по обороту налогов'),
    0x69: ('ККТ', 'Переполнение денег по обороту налогов'),
    0x6A: ('ККТ', 'Ошибка питания в момент ответа по I2C'),
    0x6B: ('ККТ', 'Нет чековой ленты'),
    0x6C: ('ККТ', 'Нет контрольной ленты'),
    0x6D: ('ККТ', 'Не хватает денег по налогу'),
    0x6E: ('ККТ', 'Переполнение денег по налогу'),
    0x6F: ('ККТ', 'Переполнение по выплате в смене'),

    0x70: ('ККТ', 'Переполнение ФП'),
    0x71: ('ККТ', 'Ошибка отрезчика'),
    0x72: ('ККТ', 'Команда не поддерживается в данном подрежиме'),
    0x73: ('ККТ', 'Команда не поддерживается в данном режиме'),
    0x74: ('ККТ', 'Ошибка ОЗУ'),
    0x75: ('ККТ', 'Ошибка питания'),
    0x76: ('ККТ', 'Ошибка принтера: нет импульсов с тахогенератора'),
    0x77: ('ККТ', 'Ошибка принтера: нет сигнала с датчиков'),
    0x78: ('ККТ', 'Замена ПО'),
    0x79: ('ККТ', 'Замена ФП'),
    0x7A: ('ККТ', 'Поле не редактируется'),
    0x7B: ('ККТ', 'Ошибка оборудования'),
    0x7C: ('ККТ', 'Не совпадает дата'),
    0x7D: ('ККТ', 'Неверный формат даты'),
    0x7E: ('ККТ', 'Неверное значение в поле длины'),
    0x7F: ('ККТ', 'Переполнение диапазона итога чека'),

    0x80: ('ККТ', 'Ошибка связи с ФП'),
    0x81: ('ККТ', 'Ошибка связи с ФП'),
    0x82: ('ККТ', 'Ошибка связи с ФП'),
    0x83: ('ККТ', 'Ошибка связи с ФП'),
    0x84: ('ККТ', 'Переполнение наличности'),
    0x85: ('ККТ', 'Переполнение по продажам в смене'),
    0x86: ('ККТ', 'Переполнение по покупкам в смене'),
    0x87: ('ККТ', 'Переполнение по возвратам продаж в смене'),
    0x88: ('ККТ', 'Переполнение по возвратам покупок в смене'),
    0x89: ('ККТ', 'Переполнение по внесению в смене'),
    0x8A: ('ККТ', 'Переполнение по надбавкам в чеке'),
    0x8B: ('ККТ', 'Переполнение по скидкам в чеке'),
    0x8C: ('ККТ', 'Отрицательный итог надбавки в чеке'),
    0x8D: ('ККТ', 'Отрицательный итог скидки в чеке'),
    0x8E: ('ККТ', 'Отрицательный итог скидки в чеке'),
    0x8F: ('ККТ', 'Касса не фискализирована'),

    0x90: ('ККТ', 'Поле превышает размер, установленный в настройках'),
    0x91: ('ККТ', 'Выход за границу поля печати при данных настройках шрифта'),
    0x92: ('ККТ', 'Наложение полей'),
    0x93: ('ККТ', 'Восстановление ОЗУ прошло успешно'),
    0x94: ('ККТ', 'Исчерпан лимит операций в чеке'),
    0x95: ('ЭКЛЗ', 'Неизвестная ошибка ЭКЛЗ'),

    0xA0: ('ККТ', 'Ошибка связи с ЭКЛЗ'),
    0xA1: ('ККТ', 'ЭКЛЗ отсутствует'),
    0xA2: ('ЭКЛЗ', 'ЭКЛЗ: Некорректный формат или параметр команды'),
    0xA3: ('ЭКЛЗ', 'Некорректное состояние ЭКЛЗ'),
    0xA4: ('ЭКЛЗ', 'Авария ЭКЛЗ'),
    0xA5: ('ЭКЛЗ', 'Авария КС в составе ЭКЛЗ'),
    0xA6: ('ЭКЛЗ', 'Исчерпан временной ресурс ЭКЛЗ'),
    0xA7: ('ЭКЛЗ', 'ЭКЛЗ переполнена'),
    0xA8: ('ЭКЛЗ', 'ЭКЛЗ: Неверные дата и время'),
    0xA9: ('ЭКЛЗ', 'ЭКЛЗ: Нет запрошенных данных'),
    0xAA: ('ЭКЛЗ', 'Переполнение ЭКЛЗ (отрицательный итог документа)'),

    0xB0: ('ККТ', 'ЭКЛЗ: Переполнение в параметре количество'),
    0xB1: ('ККТ', 'ЭКЛЗ: Переполнение в параметре сумма'),
    0xB2: ('ККТ', 'ЭКЛЗ: Уже активизирована'),

    0xC0: ('ККТ', 'Контроль даты и времени (подтвердите дату и время)'),
    0xC1: ('ККТ', 'ЭКЛЗ: суточный отчѐт с гашением прервать нельзя'),
    0xC2: ('ККТ', 'Превышение напряжения в блоке питания'),
    0xC3: ('ККТ', 'Несовпадение итогов чека и ЭКЛЗ'),
    0xC4: ('ККТ', 'Несовпадение номеров смен'),
    0xC5: ('ККТ', 'Буфер подкладного документа пуст'),
    0xC6: ('ККТ', 'Подкладной документ отсутствует'),
    0xC7: ('ККТ', 'Поле не редактируется в данном режиме'),
    0xC8: ('ККТ', 'Отсутствуют импульсы от таходатчика'),
    0xC9: ('ККТ', 'Перегрев печатающей головки'),
    0xCA: ('ККТ', 'Температура вне условий эксплуатации'),
}

blank_dict = {}
### Режимы ККТ ###
# Режим ККМ – одно из состояний ККМ, в котором она может находиться.
# Режимы ККМ описываются одним байтом: младший полубайт – номер режима,
# старший полубайт – битовое поле, определяющее статус режима (для режимов
# 8, 13 и 14).
# Номера и назначение режимов и статусов:
ICL_MODES = {
    0:  ('Принтер в рабочем режиме.', blank_dict),
    1:  ('Выдача данных.', blank_dict),
    2:  ('Открытая смена, 24 часа не кончились.', blank_dict),
    3:  ('Открытая смена, 24 часа кончились.', blank_dict),
    4:  ('Закрытая смена.', blank_dict),
    5:  ('Блокировка по неправильному паролю налогового инспектора.', blank_dict),
    6:  ('Ожидание подтверждения ввода даты.', blank_dict),
    7:  ('Разрешение изменения положения десятичной точки.', blank_dict),
    8:  ('Открытый документ:', {
            0:  'Продажа.',
            1:  'Покупка.',
            2:  'Возврат продажи.',
            3:  'Возврат покупки.'
        }),
    9:  ('Режим разрешения технологического обнуления. В этот режим ККМ '\
        'переходит по включению питания, если некорректна информация в '\
        'энергонезависимом ОЗУ ККМ.', blank_dict),
    10: ('Тестовый прогон.', blank_dict),
    11: ('Печать полного фис. отчета.', blank_dict),
    12: ('Печать отчёта ЭКЛЗ.', blank_dict),
    13: ('Работа с фискальным подкладным документом:', {
            0:  'Продажа (открыт).',
            1:  'Покупка (открыт).',
            2:  'Возврат продажи (открыт).',
            3:  'Возврат покупки (открыт).'
        }),
    14: ('Печать подкладного документа.', {
            0:  'Ожидание загрузки.',
            1:  'Загрузка и позиционирование.',
            2:  'Позиционирование.',
            3:  'Печать.',
            4:  'Печать закончена.',
            5:  'Выброс документа.',
            6:  'Ожидание извлечения.'
        }),
    15: ('Фискальный подкладной документ сформирован.', blank_dict),
}

### Подрежимы ККТ ###
# Подрежим ККТ – одно из состояний ККТ , в котором он может находиться.
# Номера и назначение подрежимов:
KKT_SUBMODES = {
    0:  'Бумага есть – ККТ не в фазе печати операции – может принимать '\
        'от хоста команды, связанные с печатью на том документе, датчик'\
        ' которого сообщает о наличии бумаги.',
    1:  'Пассивное отсутствие бумаги – ККТ не в фазе печати операции – '\
        'не принимает от хоста команды, связанные с печатью на том '\
        'документе, датчик которого сообщает об отсутствии бумаги.',
    2:  'Активное отсутствие бумаги – ККТ в фазе печати операции – '\
        'принимает только команды, не связанные с печатью. Переход из '\
        'этого подрежима только в подрежим 3.',
    3:  'После активного отсутствия бумаги – ККТ ждет команду '\
        'продолжения печати. Кроме этого принимает команды, не '\
        'связанные с печатью.',
    4:  'Фаза печати операции полных фискальных отчетов – ККТ не '\
        'принимает от хоста команды, связанные с печатью, кроме команды'\
        ' прерывания печати.',
    5:  'Фаза печати операции – ККТ не принимает от хоста команды, '\
        'связанные с печатью.',
}

### Флаги ККТ ###
KKT_FLAGS = {
    0:  'Рулон операционного журнала',
    1:  'Рулон чековой ленты',
    2:  'Верхний датчик подкладного документа',
    3:  'Нижний датчик подкладного документа',
    4:  'Положение десятичной точки',
    5:  'ЭКЛЗ',
    6:  'Оптический датчик операционного журнала',
    7:  'Оптический датчик чековой ленты',
    8:  'Рычаг термоголовки операционного журнала',
    9:  'Рычаг термоголовки чековой ленты',
    10: 'Крышка корпуса ФР',
    11: 'Денежный ящик',
    12: 'Отказ правого датчика принтера | Бумага на входе в презентер | Модель принтера',
    13: 'Отказ левого датчика принтера | Бумага на выходе из презентера',
    14: 'ЭКЛЗ почти заполнена',
    15: 'Увеличенная точность количества | Буфер принтера непуст',
}

### Флаги ФП ###
FP_FLAGS = {
    0: {0:'ФП 1 нет',                      1:'ФП 1 есть'},
    1: {0:'ФП 2 нет',                      1:'ФП 2 есть'},
    2: {0:'Лицензия не введена',           1:'Лицензия введена'},
    3: {0:'Переполнения ФП нет',           1:'Есть переполнение ФП'},
    4: {0:'Батарея ФП >80%',               1:'Батарея ФП <80%'},
    5: {0:'Последняя запись ФП испорчена', 1:'Последняя запись ФП корректна'},
    6: {0:'Смена в ФП закрыта',            1:'Смена в ФП открыта'},
    7: {0:'24 часа в ФП не кончились',     1:'24 часа в ФП кончились'},
}
