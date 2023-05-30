1. Установка [python3.11.3](https://www.get-python.org/downloads/release/python-3113/)
2. Проверить в консоле 
```bash 
python3  
```
3. Создать виртуальное окружение в папке с проектом, пишем в консоле
```bash 
python3 -m venv venv  
```
Должна появиться дериктория venv

4. Активируем вертиульную среду, в консоле
```bash 
source venv/bin/activate 
```
5. Устновим зависимости
```bash 
pip install -r requirements.txt
```
6. Запуск скрипта с консоли
```bash 
python main.py --text "Химическое образование"
```
Чтоб обновить данные с ресурса 
```bash 
python main.py --text "Химическое образование" --refresh
```
