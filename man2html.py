import re
import sys
import subprocess

__all__ = ['Man2HTML']


class Man2HTML:
    HEADERS = ['.TH']
    HANGING_PARAGRAPHS = ['.TP', '.HP']
    FLUSH_LEFT_PARAGRAPHS = ['.LP', '.PP', '.P', '.IP']
    INTENTED_BLOCKS = ['.RS', '.RE']
    SECTION_HEADINGS = ['.SH']
    SECTION_SUBHEADINGS = ['.SS']
    LINE_BREAK = ['.br', '.sp']
    STYLES = ['.B', '.I', '.IR', '.RI', '.BI', '.IB', '.BR', '.RB']
    LISTS = ['.nf', '.fi']
    IGNORE = ['.pc', '.ie', '.el', '.\}', '.if']

    unknown = set()

    tagstack = []

    tabulation = lambda: '\t' * (len(Man2HTML.tagstack) + 1)

    @staticmethod
    def writehtml(manfile, writer):
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
        for line in Man2HTML.convertman(manfile):
            writer(line)
        writer('</body>\n')
        writer('</html>')

    @staticmethod
    def convertman(file):
        """
        Принимает
        файл

        Исполняет
        Пробегается по всем строкам файла и
        возвращает сконвертированную
        man строку в html формат
        """
        for line in file:
            macros, content = Man2HTML.parseline(line)
            yield Man2HTML.convertline(macros, content)
        yield Man2HTML.closetags(0)

    @staticmethod
    def parseline(line):
        """
        Принимает
        man строку

        Возвращает
        tuple из макроса и содержимого
        """
        macros = None
        content = Man2HTML.clearline(line.strip())
        match = re.match(r'^[\.\']\S+', line)

        if match:
            macros = match.group(0)
            content = Man2HTML.clearline(line[len(macros) + 1:].strip())

        return macros, content

    @staticmethod
    def convertline(macros, content):
        """
        Принимает
        макрос и содержимое

        Возвращает
        html строку
        """
        result = ''

        if not macros and not content:
            result += Man2HTML.tabulation() + '<br>\n'

        elif not macros:
            result += Man2HTML.tabulation() + content + '\n'

        elif macros in Man2HTML.IGNORE:
            return ''

        elif macros.startswith('.\\"') or macros.startswith('\'\\"'):
            # result += tabulation() + '<!-- ' + content + ' -->\n'
            return ''

        elif macros in Man2HTML.HEADERS:
            result += Man2HTML.tabulation() + \
                '<header>' + content + '</header>\n'

        elif macros in Man2HTML.HANGING_PARAGRAPHS:
            result += Man2HTML.closetags(3)
            result += Man2HTML.tabulation() + '<p>\n'
            Man2HTML.tagstack.append('p')
            result += Man2HTML.tabulation() + '<span>\n'
            Man2HTML.tagstack.append('left')
            return result

        elif macros in Man2HTML.FLUSH_LEFT_PARAGRAPHS:
            result += Man2HTML.closetags(3)
            result += Man2HTML.tabulation() + '<p>\n'
            Man2HTML.tagstack.append('p')

        elif macros in Man2HTML.INTENTED_BLOCKS:
            result += Man2HTML.closetags(5)
            if macros == '.RS':
                result += Man2HTML.tabulation() + '<p class="intented">\n'
                Man2HTML.tagstack.append('p')

        elif macros in Man2HTML.SECTION_SUBHEADINGS:
            result += Man2HTML.closetags(2)
            result += Man2HTML.tabulation() + '<section>\n'
            Man2HTML.tagstack.append('ssection')
            result += Man2HTML.tabulation() + \
                '<h4>' + content.strip('"') + '</h4>\n'
            result += Man2HTML.tabulation() + '<p>\n'
            Man2HTML.tagstack.append('p')

        elif macros in Man2HTML.SECTION_HEADINGS:
            result += Man2HTML.closetags(1)
            result += Man2HTML.tabulation() + '<section>\n'
            Man2HTML.tagstack.append('section')
            result += Man2HTML.tabulation() + \
                '<h3>' + content.strip('"') + '</h3>\n'
            result += Man2HTML.tabulation() + '<p>\n'
            Man2HTML.tagstack.append('p')

        elif macros in Man2HTML.LISTS:

            if macros == '.nf':
                result += Man2HTML.closetags(4)
                result += Man2HTML.tabulation() + '<ul>\n'
                Man2HTML.tagstack.append('ul')

            elif macros == '.fi':
                result += Man2HTML.closetags(4)

            return result

        elif macros in Man2HTML.LINE_BREAK:

            if macros == '.br':
                if content:
                    result += Man2HTML.tabulation() + content + '\n'
                result += Man2HTML.tabulation() + '<br>\n'

        elif macros in Man2HTML.STYLES:

            content = [i for i in re.split(r'\"+(?![^\<]*\>)', content.strip('"'))
                       if i.strip()]

            if len(content) == 1:
                content = re.split(r'\s+(?![^\<]*\>)', content[0].strip())

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

            result += Man2HTML.tabulation() + " ".join(content) + '\n'

        else:

            if macros not in Man2HTML.unknown:
                print('Unknown macros: "' + macros + '"')
                Man2HTML.unknown.add(macros)
            # result += tabulation() + macros + ' ' + content + '\n'

            return ''

        if Man2HTML.tagstack:

            if Man2HTML.tagstack[-1] == 'left':
                result += Man2HTML.closetags(4)
                result += Man2HTML.tabulation() + '<span>\n'
                Man2HTML.tagstack.append('right')

            elif Man2HTML.tagstack[-1] == 'ul':
                result = Man2HTML.tabulation() + '<li>\n' + result
                result += Man2HTML.tabulation() + '</li>\n'

        return result

    @staticmethod
    def closetags(lvl):
        """
        Принимает
        уровень вложенности,
        до которого нужно закрыть теги

        Возвращает
        строку, содержащую закрывающиеся теги
        """
        result = ''

        if Man2HTML.tagstack:

            if lvl <= 6 and Man2HTML.tagstack[-1] == 'p':
                Man2HTML.tagstack.pop()
                result += Man2HTML.tabulation() + '</p>\n'

            if lvl <= 5 and Man2HTML.tagstack[-1] == 'li':
                Man2HTML.tagstack.pop()
                result += Man2HTML.tabulation() + '</li>\n'

            if lvl <= 4 and Man2HTML.tagstack[-1] == 'ul':
                Man2HTML.tagstack.pop()
                result += Man2HTML.tabulation() + '</ul>\n'

            if lvl <= 4 and (Man2HTML.tagstack[-1] == 'left' or
                             Man2HTML.tagstack[-1] == 'right'):
                Man2HTML.tagstack.pop()
                result += Man2HTML.tabulation() + '</span>\n'

            if lvl <= 3 and Man2HTML.tagstack[-1] == 'p':
                Man2HTML.tagstack.pop()
                result += Man2HTML.tabulation() + '</p>\n'

            if lvl <= 2 and Man2HTML.tagstack[-1] == 'ssection':
                Man2HTML.tagstack.pop()
                result += Man2HTML.tabulation() + '</section>\n'

            if lvl <= 1 and Man2HTML.tagstack[-1] == 'section':
                Man2HTML.tagstack.pop()
                result += Man2HTML.tabulation() + '</section>\n'

        return result

    @staticmethod
    def clearline(line):
        """
        Принимает
        man строку

        Возвращает
        строку, с замененными эскейп-символами
        и с замененными ссылками и е-адресами
        на ссылки и е-адреса в формате html
        """
        line = re.sub(r'\\e', r'\\', line)
        line = re.sub(r'\\".*', '', line)
        line = re.sub(r'\\w\'(\w*)\'u', r'\1', line)
        line = re.sub(r'\\-', '-', line)
        line = re.sub(r'\\[c\|&\/du%]', '', line)
        line = re.sub(r'\\m\[.*?\]', '', line)
        line = re.sub(r'\\s[+-]\d+', '', line)
        line = re.sub(r'\\\s', '&nbsp;', line)
        line = re.sub(r'&(\w*\s)', r'&amp;\1', line)
        line = re.sub('<', '&lt;', line)
        line = re.sub('>', '&gt;', line)
        line = re.sub(r'\\\([lr]q', '"', line)
        line = re.sub(r'\\\([ac]q', '\'', line)
        line = re.sub(r'\\\*\(Aq', '', line)
        line = re.sub(r'(\\f\w)', r'\\fR\1', line)
        line = re.sub(r'\\fP', r'\\fR', line)
        line = re.sub(r'\\fB(.+?)(\\fR|$)', r'<b>\1</b>', line)
        line = re.sub(r'\\fI(.+?)(\\fR|$)', r'<u>\1</u>', line)
        line = re.sub(r'\\fR', '', line)
        line = re.sub(r'([a-zA-Z0-9_.+-]+@([a-zA-Z0-9-]+\.)+[a-zA-Z0-9-.]+)',
                      r'<a href="mailto:\1">\1</a>', line)
        line = re.sub(r'((https?|ftp|file):(\/){2,3}([\da-z\.-]+)\.?' +
                      '([a-z\.]{2,6})?([~#\/\w\.-]*)*\/?)',
                      r'<a href="\1">\1</a>', line)

        return line.strip()

    @staticmethod
    def check_options(args):
        if len(sys.argv) == 1:
            print('Type ./man2html.py --help for getting help')
            quit()

        if '--help' in args:
            print("""
        Man2HTML
        --------

        man2html.py (command | --file <file dir>)
                    [--out <file dir> | --print]

        Options:
            --help              - эта страница
            --file <file dir>   - man файл
            --out <file dir>    - html файл для вывода
            --print             - вывести html на экран
            """)
            quit()

        if '--out' not in args and '--print' not in args:
            print('Input --out <file dir> and\or --print option(s)')
            quit()

        options = {
            'command': None,
            'file': None,
            'out': [],
            'print': False
        }

        if '--file' in args:
            index = args.index('--file') + 1
            if len(args) < index:
                print('Please input file dir after --file option')
                quit()
            options['file'] = args[index]
        else:
            options['command'] = args[1]

        if '--out' in args:
            index = args.index('--out') + 1
            if len(args) < index:
                print('Please input file dir after --out option')
                quit()
            options['out'] = args[index]

        if '--print' in args:
            options['print'] = True

        return options


def main():

    options = Man2HTML.check_options(sys.argv)

    if options['file'] is not None:
        if options['out'] is not None:
            try:
                with open(options['file']) as manfile, \
                        open(options['out'], 'w') as htmlfile:
                    Man2HTML.writehtml(manfile, htmlfile.write)
                    if options['print']:
                        Man2HTML.writehtml(manfile, print)
            except IOError as e:
                print(e)
        else:
            try:
                with open(options['file']) as manfile:
                    Man2HTML.writehtml(manfile, print)
            except IOError as e:
                print(e)
        return

    try:
        place = subprocess \
            .check_output(['man', '-w', options['command']]) \
            .decode().strip()
        man = subprocess \
            .check_output(['zcat', place]) \
            .decode().splitlines()
        if options['out']:
            with open(options['out'], 'w') as htmlfile:
                Man2HTML.writehtml(man, htmlfile.write)
                if options['print']:
                    Man2HTML.writehtml(man, print)
        else:
            Man2HTML.writehtml(man, print)
    except IOError as e:
        print(e)


if __name__ == '__main__':
    main()
