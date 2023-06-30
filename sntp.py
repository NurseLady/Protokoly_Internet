#!/usr/bin/env python
# -*- coding: utf-8 -*-
import errno
import signal
import struct
import socket
import sys
import time
import ntplib

TIME_1970 = 2208988800
PORT = 124
IP = '127.0.0.1'
TRUE_TIME_SERVER = 'time.windows.com'


def handle_interrupt(signal, frame):
    print("Программа завершена пользователем")
    sys.exit(0)


def run():
    shift = 0

    # Установим сдвиг времени, взяв его из файла 'config'
    try:
        with open('config') as conf_file:
            shift = int(conf_file.readline())
    except Exception as e:
        print('Не удалось установить сдвиг из файла: {}'.format(e))
    finally:
        print('Установлен сдвиг {} сек.'.format(shift))

    ntp = ntplib.NTPClient()

    # Настраиваем сокет
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((IP, PORT))

    print('Сервер запущен на {}:{}'.format(IP, PORT))

    signal.signal(signal.SIGINT, handle_interrupt)
    s.setblocking(False)

    while True:
        try:
            client, address = s.recvfrom(PORT)

            if not client:
                break

            # Получаем точное время
            request = ntp.request(TRUE_TIME_SERVER)
            true_time = request.tx_time
            data = bytearray(request.to_data())

            # Модифицируем то, что получили, заменяя время в пакете, полученном от сервера точного времени
            fake_time = bytearray(struct.pack('!1I', TIME_1970 + int(true_time) + shift))
            data[40:44] = fake_time
            request.from_data(data)

            print('Точное время: {}'.format(time.ctime(true_time)))
            print('Время со сдвигом для клиента: {}'.format(time.ctime(request.tx_time)))

            # Засылаем клиенту
            s.sendto(data, address)
        except KeyboardInterrupt:
            handle_interrupt(None, None)
        except socket.error as e:
            err = e.args[0]
            if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                pass
            else:
                print(f"Произошла ошибка: {e}")
    s.close()


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        exit(0)
