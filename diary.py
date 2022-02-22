import requests
from bs4 import BeautifulSoup
from datetime import datetime
try:
    from url_helper import *
    from exceptions import *
except ImportError:
    from edu_parser.url_helper import *
    from edu_parser.exceptions import *


def get_timestamp(date):
    base_date = datetime.strptime('01.05.2019', '%d.%m.%Y')
    base_timestamp = 1556658000
    new_timestamp = base_timestamp + (date - base_date).days * 86400
    return new_timestamp


class DiaryGrade:
    def __init__(self, data):
        self.grade = data.div.string
        self.comment = data['title']

    def __repr__(self):
        return '({}, {})'.format(self.grade, self.comment)

    def __str__(self):
        return __repr__()


class DiarySubject:
    def __init__(self, data):
        self.data = {}

        self.time_start = data[0].contents[0]
        self.data['time_start'] = self.time_start

        self.time_end = data[0].contents[-1]
        self.data['time_end'] = self.time_end

        self.time = '{} - {}'.format(self.time_start, self.time_end)
        self.data['time'] = self.time

        self.name = data[1].string
        self.data['name'] = self.name

        if data[2].p is not None:
            self.homework = data[2].p.string
        else:
            self.homework = ''
        self.data['homework'] = self.homework

        if data[3].i is not None:
            self.comment = data[3].i.string
        else:
            self.comment = ''
        self.data['comment'] = self.comment

        if data[4].find('table', attrs={'class': 'marks'}) is not None:
            cols = data[4].tr.find_all('td')
            self.grades = [DiaryGrade(col) for col in cols]
            self.data['grades'] = self.grades
        else:
            self.grades = []
            self.data['grades'] = self.grades

    def __repr__(self):
        return str(self.data)

    def get_str(self):
        homework = self.homework
        if homework is None:
            homework = "Ничего не задано"
        return '_' + str(self.time) + '_ *' + str(self.name) + '* - `' + homework + '`'


class DiaryDay:
    def __init__(self, session, date, proxy):
        self.date = datetime.strptime(date, '%d.%m.%Y')
        self.date_str = date
        self.weekday = self.date.weekday()
        response = session.get(diary_day_url + str(get_timestamp(self.date)), proxies=proxy)

        if 'не найден' in response.text:
            raise LoginError('it appears that you are not logged in')

        html = BeautifulSoup(response.text, 'html.parser')
        main_table = html.find('table', attrs={'class': 'main'})
        rows = main_table.find_all('tr')

        self.subjects = []
        for row in rows[1:]:
            cols = row.find_all('td')
            try:
                cols[0]['title']
            except KeyError:
                self.subjects.append(DiarySubject(
                    [col for col in cols]
                ))

    def __repr__(self):
        return 'instance of DiaryDay class with date {}'.format(self.date_str)

    def __str__(self):
        return str(dict([
            ('weekday', self.weekday),
            ('date_str', self.date_str),
            ('subjects', self.subjects)
        ]))
        return '"weekday": {}, "date_str": "{}", "subjects": {}'.format(self.weekday, self.date_str, str(self.subjects))


class TermSubject:
    def __init__(self, data, grades_count):
        self.data = {}

        self.name = data[0].string
        self.data['name'] = self.name

        self.grades = []
        raw_grades = data[1:grades_count + 1]
        for raw_grade in raw_grades:
            grade = raw_grade.string
            if grade is not None:
                self.grades.append(int(grade))
        self.data['grades'] = str(self.grades)

        try:
            self.average_grade = float(data[grades_count + 1].string)
        except TypeError:
            self.average_grade = 0.0

        self.data['average_grade'] = self.average_grade

        self.final_grade = data[-1].string
        self.data['final_grade'] = self.final_grade

    def __repr__(self):
        return str(self.data)

    def __str__(self):
        return __repr__()

    def predict(self, new_grades):
        return (sum(self.grades) + sum(new_grades)) / (len(self.grades) + len(new_grades))


class DiaryTerm:
    def __init__(self, session, term, proxy):
        self.term_number = term
        response = session.get(term_url + term, proxies=proxy)

        if 'не найден' in response.text:
            raise LoginError('it appears that you are not logged in')

        html = BeautifulSoup(response.text, 'html.parser')
        main_table = html.find('table', attrs={'class': 'term-marks'})
        rows = main_table.find_all('tr')
        self.grades_count = int(rows[0].find_all('td')[1]['colspan'])
        self.subjects = {}

        for row in rows[1:-1]:
            cols = row.find_all('td')
            subject = TermSubject(
                [col for col in cols], self.grades_count
            )
            self.subjects[subject.name] = subject

    def get_subject(self, input_name):
        name = ''
        count = 0
        for key in self.subjects.keys():
            if input_name.lower() in key.lower():
                name = key
                count += 1
        if count > 1:
            return None
        return self.subjects.get(name)

    def __repr__(self):
        if self.term_number == '':
            return 'instance of DiaryTerm class for the current term'
        else:
            return 'instance of DiaryTerm class for the {} term'.format(self.term_number)

    def __str__(self):
        return str(dict([
            ('term_number', self.term_number),
            ('grades_count', self.grades_count),
            ('subjects', self.subjects)
        ]))
