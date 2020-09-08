import requests
import json
import os
import datetime

def create_file_on_PC(adres_dir, type_adres = 'ForPC', file_name = ''):
  parts_adress = adres_dir.split('|')
  result = ''
  if type_adres == 'ForPC':
    for part in parts_adress:
      result = os.path.join(result, part)
      if not os.path.exists(result):
        os.mkdir(result)
  else:
    result = parts_adress[-1]
  return os.path.join(result, file_name)
def create_YaDir(dtime, AOuthData):
    my_string = dtime[0:19]
    dir_name = ''
    for char in my_string:
        if char == ':':
            dir_name = dir_name + '-'
        else:
            dir_name = dir_name + char

    URL = 'https://cloud-api.yandex.net/v1/disk/resources'
    params = {'path': dir_name}
    headers = {'Accept': 'application/json', 'Authorization': AOuthData['YaToken']}

    create_dir = requests.put(URL, params=params, headers = headers)
    downloadinfo = catch_request_error(create_dir, 'YanCreateDir', dir_name)
    if downloadinfo['error']:
        return downloadinfo
    else:
      downloadinfo['user_massage'] = f'[Создание каталога YaDisk] Каталог {dir_name} создан успешно'
    result = {'dir': dir_name, 'downloadinfo': downloadinfo}
    return result
def get_adres_on_PC(adres):
    parts_adress = adres.split('|')
    result = ''
    for part in parts_adress:
      result = os.path.join(result, part)
      if not os.path.exists(result):
         os.mkdir(result)
    return result
def catch_request_error(answer, type_reqoest, data = ''):
  result = {}
  result['error'] = 0
  if answer.status_code < 200 or answer.status_code > 299:
    result['error'] = 1
    if type_reqoest == 'VKGetLinks':
      result['user_massage'] = f'[Получение ссылок для скачивания изображений VK] Ошибка соединения с сервером. Получен ответ сервера: {answer.status_code}'
    elif type_reqoest == 'YanGetLink':
      result['user_massage'] = f'[Получение ссылок для загрузки изображений YaDisk] Ошибка соединения с сервером. Получен ответ сервера: {answer.status_code}'
    elif type_reqoest == 'YanDownloadPhoto':
      result['user_massage'] = f'[Загрузка изображения YaDisk] Ошибка соединения с сервером. Получен ответ сервера: {answer.status_code}'
    elif type_reqoest == 'YanCreateDir':
      result['user_massage'] = f'[Создание каталога YaDisk] Не удалось создать каталог {data}. ' + answer.json()['message']
    return result
  else:
    if type_reqoest == 'VKGetLinks':
      JSONanswer = answer.json()
      if 'error' in JSONanswer.keys():
        result['error'] = 1
        result['error_code'] = JSONanswer['error']['error_code']
        result['error_msg'] = JSONanswer['error']['error_msg']
        result['user_massage'] = f'В ответе сервера получена ошибка: ERROR_CODE = {result["error_code"]} - {result["error_msg"]}'
  return result
def find_max_size(photo_size_list):
    photo_size_max = 0
    result_data = {}
    for photo in photo_size_list:
        pixel_count = photo['height'] * photo['width']
        if pixel_count > photo_size_max:
            photo_size_max = pixel_count
            result_data = photo
    return result_data
def get_input_data(filename):
    with open(filename) as f:
        result = json.load(f)
        if result['owner_id'][0] == '0':
            print('ВНИМАНИЕ! Во входных данных [owner_id] будет приведен к типу [int] для дальнейшей работы.')
            print('Содержащиеся в начале строки "0" будут удалены.')
        result['owner_id'] = int(result['owner_id'])
    return result
class DownloadPhotoFromVKInPS():
    URL = 'https://api.vk.com/method/photos.get'
    def __init__(self, AOuthData):
        self.adres_for_save = get_adres_on_PC(AOuthData['adres_for_save'])
        self.parametrs_photos_get = {
            'lang': 0,
            'owner_id': AOuthData['owner_id'],
            'album_id': 'profile',
            'rev': 0,
            'extended': 1,
            'feed_type': 'photo',
            'photo_sizes': 1,
            'offset': 2,
            'count': AOuthData['count'],
            'access_token': AOuthData['access_token'],
            'v': 5.122
        }
        self.answer = requests.get(url=self.URL, params=self.parametrs_photos_get)
        self.downloadinfo = catch_request_error(self.answer, 'VKGetLinks')
        if self.downloadinfo['error']:
            pass
        else:
          self.downloadinfo['user_massage'] = '[Загрузка ссылок на фото ВК] Ссылки на фото в VK загружены.'
          self.JSONanswer = self.answer.json()
        pass

    def download_photos_on_PC(self, dtime):
        list_photos = self.answer.json()['response']['items']
        # name_filelog = os.path.join(self.adres_for_save, f'filelog.txt')
        name_filelog = f'filelog.txt'

        for_log = []
        self.downloads = []
        list_names = {}

        with open(name_filelog, 'a') as filelog:
            for photo in list_photos:
                link_size = find_max_size(photo['sizes'])

                name = f'{str(photo["likes"]["count"])}.jpg'
                if name in list_names.keys():
                  list_names[name] = list_names[name] + 1
                  name = f'{str(photo["likes"]["count"])}' + f'_{list_names[name]}.jpg'
                else:
                  list_names[name] = 1

                loginfo = {"name": name, "size": link_size['type']}
                photo_name = os.path.join(self.adres_for_save, loginfo["name"])
                elem = {'name': name, 'adres': photo_name}
                self.downloads.append(elem)

                with open(photo_name, 'wb') as save_photo:
                    data = requests.get(link_size['url'])
                    save_photo.write(data.content)
                for_log.append(loginfo)

            log_dict = {}
            log_dict[dtime] = for_log
            json.dump(log_dict, filelog, indent=2)
        return 0

    def delite_rubbish(self):
        import shutil
        dir_path = self.adres_for_save
        shutil.rmtree(dir_path)

class YaUploader:
    PREPARE_UPLOAD_URL = 'https://cloud-api.yandex.net/v1/disk/resources/upload'

    def __init__(self, AOuthData, PC_file_adres, dir_name):
        self.TOKEN = AOuthData['YaToken']
        self.headers = {'Accept': 'application/json', 'Authorization': self.TOKEN}
        self.file_path = PC_file_adres
        self.put_url = ''
        filename_on_disk = PC_file_adres.split('\\')[-1]
        self.params = {'path': '/' + dir_name + '/' + filename_on_disk , 'overwrite': 'true'}

    def upload(self):
      result = {}
      get_url = requests.get(self.PREPARE_UPLOAD_URL, params = self.params, headers = self.headers)
      self.downloadinfo = catch_request_error(get_url, 'YanGetLink')
      if self.downloadinfo['error']:
        return self.downloadinfo
      else:
        self.put_url = get_url.json().get('href')
        files = {'file': open(self.file_path, 'rb')}
        response2 = requests.put(self.put_url, files = files, headers=self.headers)
        self.downloadinfo = catch_request_error(response2, 'YanDownloadPhoto')
        if self.downloadinfo['error']:
          return self.downloadinfo
        else:
          if response2.status_code == 201:
            self.downloadinfo['user_massage'] = f'[Загрузка изображения YaDisk] Файл {self.file_path} был загружен без ошибок'
          elif response2.status_code == 202:
            self.downloadinfo['user_massage'] = f'[Загрузка изображения YaDisk] Файл принят {self.file_path} сервером, но еще не был перенесен непосредственно в Яндекс.Диск.'
          else:
            self.downloadinfo['user_massage'] = f'[Загрузка изображения YaDisk] {self.file_path} Undifined note'
          return self.downloadinfo


def main():
    print(
        "Входные данные для работы хранятся во вутреннем файле Data.txt. Описание структуры файла находится во внутреннем файле readme.txt. Проверьте входные данные и нажмите любую клавишу для продолжения.")
    input()
    AOuthData = get_input_data('Data.txt')
    VKdownload = DownloadPhotoFromVKInPS(AOuthData)
    if VKdownload.downloadinfo['error']:
      print(VKdownload.downloadinfo['user_massage'])
    else:
      dtime = str(datetime.datetime.now())
      VKdownload.download_photos_on_PC(dtime)
      print(VKdownload.downloads)

      result = create_YaDir(dtime, AOuthData)
      if result['downloadinfo']['error']:
          print(result['downloadinfo']['user_massage'])
      else:
        for filename in VKdownload.downloads:
          uploader = YaUploader(AOuthData, filename['adres'], result['dir'])
          YaResult = uploader.upload()
          print(uploader.downloadinfo)
    VKdownload.delite_rubbish()

main()
