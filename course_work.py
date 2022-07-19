import requests
import json
import os
import sys
from datetime import datetime
import time
from tqdm import tqdm


class VK:
    def __init__(self, count=5):
        self.params = {
            'owner_id': input("Введите ID пользователя ВК: "),
            'access_token': input("Введите токен пользователя ВК: "),
            'album_id': 'profile',
            'v': '5.131',
            'extended': '1',
            'photo_sizes': '1',
            'offset': '0',
            'count': count
        }

    def get_photos_info(self):
        global photos_info
        json_res = requests.get('https://api.vk.com/method/photos.get', params=self.params).json()
        photos_info_list = json_res['response']['items']
        photos_info = []
        for photo_info in tqdm(photos_info_list, desc='Получение информации о фотографиях пользователя'):
            photo_info_dict = {}
            # создание названий фотографий
            likes_count = str(photos_info_list[photos_info_list.index(photo_info)]['likes']['count'])
            likes_count_ext = likes_count + '.jpg'
            for photo_dict in photos_info:
                if likes_count_ext not in photo_dict.values():
                    photo_info_dict["file_name"] = likes_count_ext
                else:
                    date = str(datetime.fromtimestamp(photos_info_list[photos_info_list.index(photo_info)]['date']).
                               strftime('%d-%m-%Y_%H-%M'))
                    photo_info_dict["file_name"] = likes_count + "_" + date + '.jpg'
                    break
            else:
                if len(photos_info) == 0:
                    photo_info_dict["file_name"] = likes_count_ext
            # сохранение url фотографий, соответствующих наибольшему размеру фото
            photo_sizes_list = photos_info_list[photos_info_list.index(photo_info)]['sizes']
            for size in photo_sizes_list[::-1]:
                if size['type'] == 'w':
                    photo_info_dict["file_size"] = 'w'
                    photo_info_dict["file_url"] = size['url']
                    break
            photos_info.append(photo_info_dict)
            time.sleep(0.5)
        with open(os.path.join(os.path.dirname(sys.argv[0]), 'photos_info.json'), 'w', encoding="utf-8") as file:
            json.dump(photos_info, file, indent=4)
        print('Создан json-файл с информацией о фотографиях пользователя --> photos_info.json\r')
        return photos_info


class YaDisk:
    def __init__(self):
        self.ya_token = input("Введите токен пользователя Яндекс.Диск: ")
        self.dir_title = input("Введите название создаваемой на Яндекс.Диск папки: ")
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': 'OAuth {}'.format(self.ya_token)
        }
        self.params = {
            'path': self.dir_title,
            'overwrite': 'true'
        }

    def upload_photos(self, user):
        global new_dir_title
        headers = self.headers
        params = self.params
        response = requests.put('https://cloud-api.yandex.net/v1/disk/resources', headers=headers, params=params)
        # если папки с таким названием нет на Яндекс.Диск
        if response.status_code == 201:
            print(f'Указанная папка успешно создана!\r')
            if isinstance(user, VK):
                for photo in tqdm(photos_info, desc='Загрузка фото пользователя в указанную папку на Яндекс.Диск: '):
                    photo_title = photo['file_name']
                    params = {
                        'path': f'{self.dir_title}/{photo_title}',
                        'overwrite': 'true'
                    }
                    # получение ссылки для загрузки
                    response_get = requests.get('https://cloud-api.yandex.net/v1/disk/resources/upload',
                                                headers=headers, params=params)
                    href = response_get.json().get("href", "")
                    # загрузка фото
                    response_put = requests.put(href, data=requests.get(str(photo["file_url"])).content)
        else:
            # если папка с таким названием уже имеется на Яндекс.Диск:
            while response.status_code != 201:
                print(f'Папка "{self.dir_title}" уже существует, введите другое название!\r')
                new_dir_title = input('Другое название папки: ')
                self.dir_title = new_dir_title
                new_params = {
                    'path': new_dir_title,
                    'overwrite': 'true'
                }
                response = requests.put('https://cloud-api.yandex.net/v1/disk/resources', headers=headers,
                                        params=new_params)
            else:
                print(f'Указанная папка успешно создана!\r')
                if isinstance(user, VK):
                    for photo in tqdm(photos_info,
                                      desc='Загрузка фото пользователя в указанную папку на Яндекс.Диск: '):
                        photo_title = photo['file_name']
                        params = {
                            'path': f'{new_dir_title}/{photo_title}',
                            'overwrite': 'true'
                        }
                        # получение ссылки для загрузки
                        response_get = requests.get('https://cloud-api.yandex.net/v1/disk/resources/upload',
                                                    headers=headers, params=params)
                        href = response_get.json().get("href", "")
                        # загрузка фото
                        response_put = requests.put(href, data=requests.get(str(photo["file_url"])).content)
        print('Загрузка выполнена успешно!')


if __name__ == '__main__':
    vk_user = VK(10)
    vk_user.get_photos_info()
    ya_disk_user = YaDisk()
    ya_disk_user.upload_photos(vk_user)