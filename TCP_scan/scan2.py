import socket
import concurrent.futures
import struct

from tqdm import tqdm


# Функция для сканирования TCP портов
def tcp_scan(host, port):
    try:
        # Создаем сокет
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Устанавливаем таймаут в 1 секунду
        sock.settimeout(1)
        # Пытаемся подключиться к порту
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            return port
    except socket.error:
        return None


# Функция для сканирования UDP портов
def udp_scan(host, port):
    try:
        # Создаем сокет
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Устанавливаем таймаут в 1 секунду
        sock.settimeout(1)
        # Пытаемся отправить UDP пакет на порт
        sock.sendto(b'', (host, port))
        # Получаем ответ
        recPacket, (addr, x) = sock.recvfrom(1024)
        sock.close()

        # Проверяем, вдруг это ошибка о недоступности порта
        icmpHeader = recPacket[20:28]
        icmpType, code, checksum, packetID, sequence = struct.unpack(
            "bbHHh", icmpHeader)

        if (icmpType == 3) and code == 3:
            return None
        else:
            return port
    # Если ничего не ответили, то считаем порт открытым
    except socket.timeout:
        return port
    # Если с сокетом что-то ещё произошло, то считаем что порт закрыт
    except socket.error:
        return None


# Получаем данные от пользователя
host = input("Введите IP-адрес или доменное имя: ")
start_port = int(input("Введите начальный порт: "))
end_port = int(input("Введите конечный порт: "))

# Создаем пул потоков
with concurrent.futures.ThreadPoolExecutor() as executor:
    # Создаем список задач для каждого порта
    tcp_tasks = [executor.submit(tcp_scan, host, port) for port in range(start_port, end_port + 1)]
    udp_tasks = [executor.submit(udp_scan, host, port) for port in range(start_port, end_port + 1)]

    # Выводим прогресс сканирования TCP и UDP портов
    tcp_results = []
    udp_results = []
    with tqdm(total=len(tcp_tasks) + len(udp_tasks), desc="Сканирование портов") as pbar:
        for task in concurrent.futures.as_completed(tcp_tasks + udp_tasks):
            result = task.result()
            if result is not None:
                if task in tcp_tasks:
                    tcp_results.append(result)
                else:
                    udp_results.append(result)
            pbar.update(1)

# Выводим результат
if len(tcp_results) > 0:
    print("Открытые TCP порты:")
    tcp_results.sort()
    for port in tcp_results:
        print(port)
else:
    print("Нет открытых TCP портов в указанном диапазоне.")

if len(udp_results) > 0:
    print("Открытые UDP порты:")
    udp_results.sort()
    for port in udp_results:
        print(port)
else:
    print("Нет открытых UDP портов в указанном диапазоне.")
