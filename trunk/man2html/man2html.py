import re
import sys
import argparse
import subprocess

__all__ = ['Man2HTML']


class Man2HTML:
    HEADERS = ['.TH']
    HANGING_PARAGRAPHS = ['.TP', '.HP']
    FLUSH_LEFT_PARAGRAPHS = ['.LP', '.PP', '.P', '.IP']
    INTENDED_BLOCKS = ['.RS', '.RE']
    SECTION_HEADINGS = ['.SH']
    SECTION_SUBHEADINGS = ['.SS']
    LINE_BREAK = ['.br', '.sp']
    STYLES = ['.B', '.I', '.IR', '.RI', '.BI', '.IB', '.BR', '.RB']
    LISTS = ['.nf', '.fi']
    IGNORE = ['.pc', '.ie', '.el', '.\}', '.if']

    def __init__(self, man):
        self.man = man
        self.tags = []
        self.regex_list = self.get_regex_list()
        self.html = list(self.convert_man())

    def tabulation(self):
        return '\t' * (len(self.tags) + 1)

    def write_html(self, writer):
        """
        Принимает
        файл с man'ом и функцию

        Исполняет
        использует функцию writer
        для вывода html-текста
        """
        writer('<!DOCTYPE html>\n')
        writer('<html>\n')
        writer('<head>\n')
        writer('\t<meta charset=\'UTF-8\'>\n')
        writer('\t<title>======</title>\n')
        writer('\t<link rel="stylesheet" href="styles.css">')
        writer('</head>\n')
        writer('<body>\n')
        for line in self.html:
            writer(line)
        writer('</body>\n')
        writer('</html>\n')

    def convert_man(self):
        """
        Принимает
        файл

        Исполняет
        Пробегается по всем строкам файла и
        возвращает сконвертированную
        man строку в html формат
        """
        for line in self.man:
            macros, content = self.parse_line(line)
            yield self.convert_line(macros, content)
        yield self.close_tags(0)

    def parse_line(self, line):
        """
        Принимает
        man строку

        Возвращает
        tuple из макроса и содержимого
        """
        macros = None
        content = self.clear_line(line.strip())
        match = re.match(r'^[\.\']\S+', line)
        if match:
            macros = match.group(0)
            content = self.clear_line(line[len(macros) + 1:].strip())
        return macros, content

    def convert_line(self, macros, content):
        """
        Принимает
        макрос и содержимое

        Возвращает
        html строку
        """
        result = ''

        if not macros and not content:
            result += self.tabulation() + '<br>\n'

        elif not macros:
            result += self.tabulation() + content + '\n'

        elif macros in self.IGNORE:
            return ''

        elif macros.startswith('.\\"') or macros.startswith('\'\\"'):
            return ''

        elif macros in self.HEADERS:
            result += self.tabulation() + \
                      '<header>' + content + '</header>\n'

        elif macros in self.HANGING_PARAGRAPHS:
            result += self.close_tags(3)
            result += self.tabulation() + '<p>\n'
            self.tags.append('p')
            result += self.tabulation() + '<span>\n'
            self.tags.append('left')
            return result

        elif macros in self.FLUSH_LEFT_PARAGRAPHS:
            result += self.close_tags(3)
            result += self.tabulation() + '<p>\n'
            self.tags.append('p')

        elif macros in self.INTENDED_BLOCKS:
            result += self.close_tags(5)
            if macros == '.RS':
                result += self.tabulation() + '<p class="intended">\n'
                self.tags.append('p')

        elif macros in self.SECTION_SUBHEADINGS:
            result += self.close_tags(2)
            result += self.tabulation() + '<section>\n'
            self.tags.append('ssection')
            result += self.tabulation() + \
                      '<h4>' + content.strip('"') + '</h4>\n'
            result += self.tabulation() + '<p>\n'
            self.tags.append('p')

        elif macros in self.SECTION_HEADINGS:
            result += self.close_tags(1)
            result += self.tabulation() + '<section>\n'
            self.tags.append('section')
            result += self.tabulation() + \
                      '<h3>' + content.strip('"') + '</h3>\n'
            result += self.tabulation() + '<p>\n'
            self.tags.append('p')

        elif macros in self.LISTS:

            if macros == '.nf':
                result += self.close_tags(4)
                result += self.tabulation() + '<ul>\n'
                self.tags.append('ul')

            elif macros == '.fi':
                result += self.close_tags(4)

            return result

        elif macros in self.LINE_BREAK:
            if macros == '.br':
                if content:
                    result += self.tabulation() + content + '\n'
                result += self.tabulation() + '<br>\n'

        elif macros in self.STYLES:

            content = [i for i in
                       re.split(r'\"+(?![^<]*>)', content.strip('"'))
                       if i.strip()]

            if len(content) == 1:
                content = re.split(r'\s+(?![^<]*>)', content[0].strip())

            if macros == '.B':
                for i in range(0, len(content)):
                    content[i] = '<b>' + content[i] + '</b>'

            elif macros == '.I':
                for i in range(0, len(content)):
                    content[i] = '<u>' + content[i] + '</u>'

            elif macros == '.BI':
                for i in range(0, len(content), 2):
                    content[i] = '<b>' + content[i] + '</b>'
                for i in range(1, len(content), 2):
                    content[i] = '<u>' + content[i] + '</u>'

            elif macros == '.IB':
                for i in range(0, len(content), 2):
                    content[i] = '<u>' + content[i] + '</u>'
                for i in range(1, len(content), 2):
                    content[i] = '<b>' + content[i] + '</b>'

            elif macros == '.IR':
                for i in range(0, len(content), 2):
                    content[i] = '<u>' + content[i] + '</u>'

            elif macros == '.RI':
                for i in range(1, len(content), 2):
                    content[i] = '<u>' + content[i] + '</u>'

            elif macros == '.BR':
                for i in range(0, len(content), 2):
                    content[i] = '<b>' + content[i] + '</b>'

            elif macros == '.RB':
                for i in range(1, len(content), 2):
                    content[i] = '<b>' + content[i] + '</b>'

            result += self.tabulation() + " ".join(content) + '\n'

        else:
            return ''

        if self.tags:
            if self.tags[-1] == 'left':
                result += self.close_tags(4)
                result += self.tabulation() + '<span>\n'
                self.tags.append('right')
            elif self.tags[-1] == 'ul':
                result = self.tabulation() + '<li>\n' + result
                result += self.tabulation() + '</li>\n'
        return result

    def close_tags(self, lvl):
        """
        Принимает
        уровень вложенности,
        до которого нужно закрыть теги

        Возвращает
        строку, содержащую закрывающиеся теги
        """
        result = ''

        if self.tags:

            if lvl <= 6 and self.tags[-1] == 'p':
                self.tags.pop()
                result += self.tabulation() + '</p>\n'

            if lvl <= 5 and self.tags[-1] == 'li':
                self.tags.pop()
                result += self.tabulation() + '</li>\n'

            if lvl <= 4 and self.tags[-1] == 'ul':
                self.tags.pop()
                result += self.tabulation() + '</ul>\n'

            if lvl <= 4 and (self.tags[-1] == 'left' or
                             self.tags[-1] == 'right'):
                self.tags.pop()
                result += self.tabulation() + '</span>\n'

            if lvl <= 3 and self.tags[-1] == 'p':
                self.tags.pop()
                result += self.tabulation() + '</p>\n'

            if lvl <= 2 and self.tags[-1] == 'ssection':
                self.tags.pop()
                result += self.tabulation() + '</section>\n'

            if lvl <= 1 and self.tags[-1] == 'section':
                self.tags.pop()
                result += self.tabulation() + '</section>\n'

        return result

    def get_regex_list(self):
        return [
            (re.compile(r'\\e'), r'\\'),
            (re.compile(r'\\".*'), ''),
            (re.compile(r'\\w\'(\w*)\'u'), r'\1'),
            (re.compile(r'\\-'), '-'),
            (re.compile(r'\\[c\|&/du%]'), ''),
            (re.compile(r'\\m\[.*?\]'), ''),
            (re.compile(r'\\s[+-]\d+'), ''),
            (re.compile(r'\\\s'), '&nbsp;'),
            (re.compile(r'&(\w*\s)'), r'&amp;\1'),
            (re.compile(r'<'), '&lt;'),
            (re.compile(r'>'), '&gt;'),
            (re.compile(r'\\\([lr]q'), '"'),
            (re.compile(r'\\\([ac]q'), '\''),
            (re.compile(r'\\\*\(Aq'), ''),
            (re.compile(r'(\\f\w)'), r'\\fR\1'),
            (re.compile(r'\\fP'), r'\\fR'),
            (re.compile(r'\\fB(.+?)(\\fR|$)'), r'<b>\1</b>'),
            (re.compile(r'\\fI(.+?)(\\fR|$)'), r'<u>\1</u>'),
            (re.compile(r'\\fR'), ''),
            (re.compile(r'([a-zA-Z0-9_.+-]+@([a-zA-Z0-9-]+\.)+[a-zA-Z0-9-.]+)'),
             r'<a href="mailto:\1">\1</a>'),
            (re.compile(r'((https?|ftp|file):(/){2,3}([\da-z\.-]+)\.?'
                        '([a-z\.]{2,6})?([~#/\w\.-]*)*/?)'),
             r'<a href="\1">\1</a>')
        ]

    def clear_line(self, line):
        """
        Принимает
        man строку

        Возвращает
        строку, с замененными эскейп-символами
        и с замененными ссылками и е-адресами
        на ссылки и е-адреса в формате html
        """
        for regex, new in self.regex_list:
            line = regex.sub(new, line)
        return line.strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--command', type=str,
                        help='unix команда')
    parser.add_argument('-f', '--file', type=str,
                        help='man файл')
    parser.add_argument('-o', '--out', type=str,
                        help='html файл для вывода')
    parser.add_argument('-p', '--print', action='store_true',
                        help='вывести html на экран')
    args = parser.parse_args()

    in_file, out_file = None, None

    if args.command:
        try:
            place = subprocess \
                .check_output(['man', '-w', args.command]) \
                .decode().strip()
            in_file = subprocess \
                .check_output(['zcat', place]) \
                .decode().splitlines()
        except NameError as e:
            print(e)
            return
    elif args.file:
        try:
            in_file = open(args.file)
        except IOError as e:
            print(e)
            return
    else:
        print(parser.print_help())
        return

    if args.out:
        try:
            out_file = open(args.out, 'w')
        except IOError as e:
            print(e)
    else:
        out_file = sys.stdout

    manparser = Man2HTML(in_file)
    manparser.write_html(out_file.write)

    if args.print:
        manparser.write_html(sys.stdout.write)


if __name__ == '__main__':
    main()
