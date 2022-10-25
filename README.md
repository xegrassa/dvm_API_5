# Сравниваем вакансии программистов

Приложение собирает информацию о вакансиях программистов разных языков с сайтов HH и SuperJob. И выводит таблицу средних зарплат вакансий 

## Как установить

Клонируйте проект и установите зависимости командами ниже.

```
git clone https://github.com/xegrassa/dvm_API_5.git
cd dvm_API_5
pip install -r requirements.txt
```

Для работы в корне проекта создайте файл **.env** и получить [SuperJob TOKEN](https://api.superjob.ru/)
```
SJ_TOKEN=Ваш_токен_от_SJ
```

## Цель проекта

Код написан в образовательных целях на онлайн-курсе для веб-разработчиков [dvmn.org](https://dvmn.org/).

## Запуск

Находясь в корне проекта запустите проект командой
```
python main.py
```

## Результат работы:
- В корне проекта создастся директория **images** в которую будут скачаны фотографии 
- Изображения отправлены в канал телеграмма

## Зависимости

* [Python 3.10](https://www.python.org/)
* [Requests](https://docs.python-requests.org/en/latest/)
* [terminaltables](https://github.com/matthewdeanmartin/terminaltables)