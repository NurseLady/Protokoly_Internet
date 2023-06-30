#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import struct
import socket
import time

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

ntp_server = 'localhost'
ntp_port = 124

# Формируем и высылаем пакет SNTP
packet = struct.pack('!B B B B 11I', 0b00100011, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
s.sendto(packet, (ntp_server, ntp_port))

# Получаем ответ от сервера NTP
response, address = s.recvfrom(1024)
s.close()
unpack_result = struct.unpack('!B B B B 11I', response)

# Получаем значение времени из пакета. Я не знаю почему это работает
NTP_time_delta = (datetime.date(*time.gmtime(0)[0:3]) - datetime.date(1900, 1, 1)).days * 24 * 3600
timestamp = unpack_result[13] + float(unpack_result[14]) / 2 ** 32 - NTP_time_delta

# Преобразуем время в удобный формат и выводим
formatted_time = time.ctime(timestamp)
print("Время с сервера NTP:", formatted_time)
