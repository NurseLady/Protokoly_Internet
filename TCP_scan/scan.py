import socket


# Функция для сканирования TCP портов
def tcp_scan(host, start_port, end_port):
    open_ports = []
    for port in range(start_port, end_port + 1):
        try:
            # Создаем сокет
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Устанавливаем таймаут в 1 секунду
            sock.settimeout(1)
            # Пытаемся подключиться к порту
            result = sock.connect_ex((host, port))
            if result == 0:
                open_ports.append(port)
            sock.close()
        except socket.error:
            pass
    return open_ports


# Получаем данные от пользователя
host = input("Введите IP-адрес или доменное имя: ")
start_port = int(input("Введите начальный порт: "))
end_port = int(input("Введите конечный порт: "))

# Сканируем порты и выводим результат
open_ports = tcp_scan(host, start_port, end_port)
if len(open_ports) > 0:
    print("Открытые TCP порты:")
    for port in open_ports:
        print(port)
else:
    print("Нет открытых TCP портов в указанном диапазоне.")
