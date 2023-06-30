#!/usr/bin/env python
# -*- coding: utf-8 -*-

import errno
import signal
import socket
import sys
import time
import dnslib
import pickle

ROOT_IP = '199.7.91.13'
IP = '127.0.0.1'
PORT = 53
cache = {}


def handle_interrupt(signal, frame):
    print("Программа завершена пользователем")
    sys.exit(0)


def update_cache():
    new_cache = {}

    for k in cache:
        if cache[k][0][0].ttl > time.time() - cache[k][1]:
            new_cache[k] = cache[k]

    cache.clear()
    cache.update(new_cache)


def send_dns_request(request, ip, client):
    try:
        client.sendto(request, (ip, 53))
        response, _ = client.recvfrom(2048)
        response = dnslib.DNSRecord.parse(response)

        if response.header.a == 1:
            cache[(response.questions[0].qname, response.questions[0].qtype)] = response.rr, time.time()

        if response.auth:
            cache[(response.auth[0].rname, response.auth[0].rtype)] = response.auth, time.time()

        for additional in response.ar:
            cache[(additional.rname, additional.rtype)] = [additional], time.time()

        with open('cache', 'wb') as f:
            pickle.dump(cache, f)
    except Exception:
        print("Связаться с авторитетным сервером не удалось :(")


def run():
    # Пытаемся подгрузить кэш из файлика, если это возможно
    try:
        with open('cache', 'rb') as f:
            cache.clear()
            cache.update(pickle.load(f))
            print("Кэш подгружен из файла")
    except:
        print("Файл кэша открыть не удалось, будет создан новый кэш")

    # Создаём сокеты для сервера и клиента
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((IP, PORT))

    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.settimeout(5)

    signal.signal(signal.SIGINT, handle_interrupt)
    server.setblocking(False)

    # Вечный цикл по обработке клиентских запросов
    while True:
        try:
            new_domain = ''
            # Получаем клиентский запрос
            request, address = server.recvfrom(2048)
            res = dnslib.DNSRecord.parse(request)
            domain = res.questions[0].qname

            print(domain)

            str_domain = str(domain)

            if str_domain.rfind('.') == len(str_domain) - 1:
                str_domain = str_domain[:str_domain.rfind('.')]
                new_domain = str_domain

            # Вносим последние изменения в кэш и проверяем, нет ли в нём нужного ответа
            update_cache()

            question_type = res.questions[0].qtype
            if not cache.get((domain, question_type)):
                print('Ответ будет получен от авторитетного сервера')
            else:
                print('Овет взят из кэша')


            # Пока ответ не появится в кэше и пока ещё есть часть доменного имени для следующего запроса
            need_root_dns_query = False
            need_authoritative_dns_query = False

            while not cache.get((domain, question_type)) and new_domain:

                # Если не удалось найти ответ в кэше для полного домена, отправляем запрос на корневой сервер
                if need_root_dns_query:
                    send_dns_request(request, ROOT_IP, client)
                    need_root_dns_query = False
                    need_authoritative_dns_query = True

                # Если не удалось найти ответ в кэше для полного домена, но удалось найти ответ для его поддомена
                elif need_authoritative_dns_query:

                    # Обновляем new_domain, чтобы он содержал только поддомен
                    last_dot = new_domain.rfind('.')
                    d = str_domain[last_dot + 1:]
                    new_domain = new_domain[:last_dot]

                    # запрос отправляется на авторитетный DNS-сервер, указанный в NS-записи для поддомена, найденной в кэше
                    if cache.get((dnslib.DNSLabel(d), 2)):
                        ns = cache.get((dnslib.DNSLabel(d), 2))[0]

                        for i in ns:
                            try:
                                ip = str(cache.get((dnslib.DNSLabel(str(i.rdata)), 1))[0][0].rdata)
                                send_dns_request(request, ip, client)
                            except:
                                pass
                else:
                    last_dot = new_domain.find('.')

                    if not last_dot == -1:
                        # Последняя метка в доменном имени для поиска NS-записов для поддомена в кэше.
                        d = str_domain[last_dot + 1:]
                        new_domain = new_domain[last_dot + 1:]
                        try:
                            # Если в кэше есть NS-записи для d.
                            if cache.get((dnslib.DNSLabel(d), 2)):
                                ns = cache.get((dnslib.DNSLabel(d), 2))[0]

                                #  Перебираем каждый NS-запис в списке ns. Получаем IP из кэша, отправляем запрос
                                for i in ns:
                                    ip = str(cache.get((dnslib.DNSLabel(str(i.rdata)), 1))[0][0].rdata)
                                    send_dns_request(request, ip, client)

                                need_authoritative_dns_query = True
                                last_dot = str_domain.rfind('.' + d)
                                new_domain = str_domain[:last_dot]

                        except Exception as e:
                            print(f'Ошибка: {e}')
                    # Если достигнут корневой домен
                    else:
                        need_root_dns_query = True
                        new_domain = str_domain
            # Если в кэше запись для заданного домена и типа запроса, посылаем его клиенту
            if cache.get((domain, question_type)):
                header = dnslib.DNSHeader(res.header.id, q=1, a=len(cache.get((domain, question_type))[0]))
                response = dnslib.DNSRecord(header, res.questions, cache.get((domain, question_type))[0])
                server.sendto(response.pack(), address)
            else:
                print("Связаться с авторитетным сервером не удалось :(")
        except KeyboardInterrupt:
            handle_interrupt(None, None)
        except socket.error as e:
            err = e.args[0]
            if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                pass
            else:
                print(f"Произошла ошибка: {e}")


if __name__ == '__main__':
    run()
