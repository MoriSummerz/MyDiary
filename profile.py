import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
try:
    from url_helper import *
    from exceptions import *
    from diary import *
except ImportError:
    from edu_parser.url_helper import *
    from edu_parser.exceptions import *
    from edu_parser.diary import *
import json


def check_login(f):
    def wrap(self, *args, **kwargs):
        if self.credentials['main_login'] not in self.session.get(index_url, proxies=self.proxy).text:
            self.logout()
            self.login()
        try:
            return f(self, *args, **kwargs)
        except LoginError:
            self.login()
            return f(self, *args, **kwargs)

    return wrap


class Profile:
    def login(self):
        if self.credentials.get('main_password') is None:
            raise CredentialsError('main_pass field is not found')
        elif self.credentials.get('main_login') is None:
            raise CredentialsError('main_login field is not found')

        # first get request to the main page
        headers = {
            'Host': 'edu.tatar.ru',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:66.0) Gecko/20100101 Firefox/66.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'close',
            'Upgrade-Insecure-Requests': '1'
        }
        self.session.get(login_url, headers=headers, proxies=self.proxy)

        # post login request
        headers = {
            'Host': 'edu.tatar.ru',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:66.0) Gecko/20100101 Firefox/66.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Referer': 'https://edu.tatar.ru/logon',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Content-Length': '53',
            'Connection': 'close',
            'Cookie': '_ga=GA1.2.1346337607.1556912647; _gid=GA1.2.404413009.1556912647; DNSID=0ac427a828f028ff97208a1dbd362fefbeb1fa06; __utma=146055648.1346337607.1556912647.1556913170.1556913170.1; __utmb=146055648.2.10.1556913170; __utmc=146055648; __utmz=146055648.1556913170.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); __utmt=1',
            'Upgrade-Insecure-Requests': '1'
        }
        self.session.post(login_url, data=self.credentials, headers=headers, proxies=self.proxy)

        # get request after login
        headers = {
            'Host': 'edu.tatar.ru',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:66.0) Gecko/20100101 Firefox/66.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Referer': 'https://edu.tatar.ru/logon',
            'Connection': 'close',
            'Cookie': '_ga=GA1.2.1346337607.1556912647; _gid=GA1.2.404413009.1556912647; DNSID=0ac427a828f028ff97208a1dbd362fefbeb1fa06; __utma=146055648.1346337607.1556912647.1556913170.1556913170.1; __utmb=146055648.2.10.1556913170; __utmc=146055648; __utmz=146055648.1556913170.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); __utmt=1',
            'Upgrade-Insecure-Requests': '1'
        }
        self.session.get(login_process_url, headers=headers, proxies=self.proxy)

        # finally get the needed data
        response = self.session.get(index_url, headers=headers)

        if 'Неверный логин или пароль' in response.text:
            raise CredentialsError('uncorrect credentials')

    def logout(self):
        headers = {
            'Host': 'edu.tatar.ru',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:66.0) Gecko/20100101 Firefox/66.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Referer': 'https://edu.tatar.ru/',
            'Connection': 'close',
            'Cookie': '_ga=GA1.2.1346337607.1556912647; _gid=GA1.2.404413009.1556912647; DNSID=0ac427a828f028ff97208a1dbd362fefbeb1fa06; __utma=146055648.1346337607.1556912647.1556913170.1556913170.1; __utmb=146055648.2.10.1556913170; __utmc=146055648; __utmz=146055648.1556913170.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); __utmt=1',
            'Upgrade-Insecure-Requests': '1'
        }
        self.session.get(logout_url, headers=headers, proxies=self.proxy)
        self.session.get(index_url, headers=headers, proxies=self.proxy)
        self.session.get(login_url, headers=headers, proxies=self.proxy)

    def __init__(self, user, proxy={}):
        self.proxy = proxy
        self.session = requests.session()
        self.credentials = user
        self.grades_cache = {}

        response = self.session.get(index_url, proxies=self.proxy)
        if 'Войти через ЕСИА' in response.text:
            self.login()
            response = self.session.get(index_url, proxies=self.proxy)

        html = BeautifulSoup(response.text, 'html.parser')
        raw_data = {}
        user_table = html.find('table', attrs={'class': 'tableEx'})
        rows = user_table.find_all('tr')

        for row in rows:
            cols = row.findAll('td')
            raw_data[cols[0]] = cols[1]

        self.data = {}

        for attr, value in raw_data.items():
            attr = attr.string
            if 'Имя' in attr:
                self.name = value.string
                self.data['name'] = self.name
            elif 'Логин' in attr:
                self.login = value.string
                self.data['login'] = self.login
            elif 'Школа' in attr:
                self.school = value.string
                self.data['school'] = self.school
            elif 'Должность' in attr:
                self.position = value.string
                self.data['position'] = self.position
            elif 'рождения' in attr:
                self.birthday = value.string
                self.data['birthday'] = self.birthday
            elif 'Пол' in attr:
                self.gender = value.string
                self.data['gender'] = self.gender
            elif 'Сертификата' in attr:
                self.cert = value.string
                self.data['cert'] = self.cert

        try:
            with open('/edu/parser/grades.json', 'r') as f:
                self.grades_cache = json.loads(f.read())
        except:
            self.grades_cache = {}

        self.logout()

    def change_proxy(self, new_proxy={}):
        self.logout()
        self.proxy = new_proxy

    @check_login
    def diary_term(self, term='', draw=False, draw_path='grades.png'):
        import matplotlib.pyplot as plt
        import matplotlib

        diary = DiaryTerm(self.session, term, self.proxy)
        if not draw:
            return diary
        fig, ax = plt.subplots(figsize=(20, 6))
        fig.tight_layout()
        plt.axis('tight')
        plt.axis('off')
        plt.grid('off')
        cols = ['Предмет', *[str(i) for i in range(1, diary.grades_count + 1)], 'Средний', 'Итоговый']
        cell_text = []
        cell_colours = []
        for key in sorted(diary.subjects.keys()):
            value = diary.subjects[key]
            if 'ОБЖ' in key:
                key = 'ОБЖ'
            key = key.split('(')[0]

            grade_colors = {
                5: (0.18, 0.8, 0.443),
                4: (0.572, 0.956, 0.258),
                3: (0.945, 0.768, 0.058),
                2: (0.901, 0.494, 0.133),
                1: (0.905, 0.298, 0.235)
            }
            color = [(0.925, 0.941, 0.945)]
            grades = value.grades
            color += [grade_colors.get(int(i)) for i in grades]
            if len(grades) < diary.grades_count:
                color += [(0.925, 0.941, 0.945)] * (diary.grades_count - len(grades))
                grades += [''] * (diary.grades_count - len(grades))

            color.append(grade_colors.get(round(value.average_grade)) if grade_colors.get(
                round(value.average_grade)) is not None else (1, 1, 1))
            final_grade = 0 if value.final_grade is None or value.final_grade == '\n' else value.final_grade
            color.append(grade_colors.get(int(final_grade)) if grade_colors.get(int(final_grade)) is not None else (
                0.925, 0.941, 0.945))
            cell_text.append([key, *grades, value.average_grade, final_grade])
            cell_colours.append(color)

        the_table = plt.table(
            cellText=cell_text,
            cellColours=cell_colours,
            colLabels=cols,
            colWidths=[0.125] + [0.015] * diary.grades_count + [0.055, 0.055],
            loc='center'
        )
        plt.gcf().canvas.draw()
        points = the_table.get_window_extent(plt.gcf()._cachedRenderer).get_points()
        points[0, :] -= 10
        points[1, :] += 10
        nbbox = matplotlib.transforms.Bbox.from_extents(points / plt.gcf().dpi)
        plt.savefig(draw_path, bbox_inches=nbbox)
        plt.clf()
        del fig
        del ax
        del matplotlib
        del plt
        return diary

    @check_login
    def diary_day(self, date=datetime.today().strftime('%d.%m.%Y')):
        return DiaryDay(self.session, date, self.proxy)

    def diary_week(self, delta=0):
        date_text = datetime.today().strftime('%d.%m.%Y')
        date = datetime.strptime(date_text, '%d.%m.%Y') + timedelta(days=7 * delta)
        dates = [date + timedelta(days=i) for i in range(0 - date.weekday(), 7 - date.weekday())]
        return [self.diary_day(i.strftime('%d.%m.%Y'), ) for i in dates[:-1]]

    def save_grades(self, diary=None):
        if diary is None:
            diary = self.diary_term()
        for name, subject in diary.subjects.items():
            self.grades_cache[name] = subject.grades

        with open('/edu/parser/grades.json', 'w') as f:
            f.write(json.dumps(self.grades_cache))

    def check_grades(self):
        diary = self.diary_term()
        new_grades = {}
        for name, subject in diary.subjects.items():
            if name not in self.grades_cache:
                self.grades_cache[name] = []

            if len(subject.grades) > len(self.grades_cache[name]):
                new_grades[name] = subject.grades[len(self.grades_cache[name]):]

        self.save_grades(diary)
        return new_grades

    def __repr__(self):
        return 'instance of Profile class with login {}'.format(self.login)

    def __str__(self):
        return str(self.data)
