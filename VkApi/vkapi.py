import requests
from urllib.parse import urlencode
import re

TOKEN = ''


def do_request(method, **kwargs):
    kwargs.setdefault('v', '5.131')
    kwargs.setdefault('access_token', TOKEN)
    return requests.get(f'https://api.vk.com/method/{method}?{urlencode(kwargs)}').json()


def get_user(id):
    try:
        user = do_request('users.get', user_ids=id)['response'][0]
    except KeyError:
        print('Не удалось получить имя пользователя')
        return
    print(user["first_name"] + ' ' + user["last_name"] + f' (id {user["id"]})')
    return user["id"]


def get_friends(id, count=None):
    ID = re.match(r'[A-Za-z]', id)
    if ID:
        id = get_user(id)
    try:
        if count:
            response = do_request('friends.get', user_id=id, order='hints', count=count)['response'][
                'items']
        else:
            response = do_request('friends.get', user_id=id, order='hints')['response']['items']
    except KeyError:
        print(f'Список друзей получить не удалось :(')
        return
    if response:
        print("Список друзей:")
        for friend in response:
            get_user(friend)
    else:
        print('Список друзей пуст')


def get_albums(id, count=None):
    ID = re.match(r'[A-Za-z]', id)
    if ID:
        id = get_user(id)
    try:
        if count:
            response = do_request('photos.getAlbums', owner_id=id, count=count)['response']['items']
        else:
            response = do_request('photos.getAlbums', owner_id=id)['response']['items']
    except KeyError:
        print('Список альбомов получить не удалось :(')
        return
    if response:
        print('Список альбомов:')
        for items in response:
            print(items['title'])
    else:
        print('Список альбомов пуст')


def get_members(id, count=None):
    try:
        if count:
            response = do_request('groups.getMembers', group_id=id, count=count)['response']['items']
        else:
            response = do_request('groups.getMembers', group_id=id)['response']['items']
    except KeyError:
        print('Список участников сообщества получить не удалось :',
              do_request('groups.getMembers', group_id=id)['error']['error_msg'])
        return

    if response:
        print('Список участников группы:')
        for user_id in response:
            print(get_user(user_id))


def print_help():
    print('Поддерживаемые команды:')
    print('user <user_ID> - получить имя пользователя')
    print('friends <user_ID> [count] - показать первые count друзей пользователя')
    print('albums <user_ID> [count] - показать первые count фотоальбомов')
    print('members <group_ID> [count] - показать первые count участников группы')


if __name__ == "__main__":
    with open('auth') as f:
        TOKEN = f.readline()
    commands = {'user': get_user,
                'friends': get_friends,
                "albums": get_albums,
                "members": get_members}

    while True:
        print(">>", end=" ")
        inp = input().split(' ')

        if inp[0] in commands:
            args = inp[1:]
            commands[inp[0]](*args)
        else:
            print_help()
