import re
import sys
import subprocess

HEADERS = ['.TH']
HANGING_PARAGRAPHS = ['.TP', '.HP']
FLUSH_LEFT_PARAGRAPHS = ['.LP', '.PP', '.P', '.IP']
INTENTED_BLOCKS = ['.RS', '.RE']
SECTION_HEADINGS = ['.SH']
SECTION_SUBHEADINGS = ['.SS']
LINE_BREAK_AND_SPACING = ['.br', '.sp']
STYLES = ['.B', '.I', '.IR', '.RI', '.BI', '.IB', '.BR', '.RB']
LISTS = ['.nf', '.fi']
IGNORE = ['.pc', '.ie', '.el', '.\}', '.if']

unknown = set()

tagstack = []

tabulation = lambda: '\t' * (len(tagstack) + 1)


def writehtml(manfile, writer):
    writer('<!DOCTYPE html>\n')
    writer('<html>\n')
    writer('<head>\n')
    writer('\t<meta charset=\'UTF-8\'>\n')
    writer('\t<title>======</title>\n')
    writer('\t<link rel="stylesheet" href="styles.css">')
    writer('</head>\n')
    writer('<body>\n')
    for line in convertman(manfile):
        writer(line)
    writer('</body>\n')
    writer('</html>')


def convertman(file):
    for line in file:
        macros, content = parseline(line)
        yield convertline(macros, content)
    yield closetags(0)


def convertline(macros, content):
    result = ''

    if not macros and not content:
        result += tabulation() + '<br>\n'

    elif not macros:
        result += tabulation() + content + '\n'

    elif macros in IGNORE:
        return ''

    elif macros.startswith('.\\"') or \
            macros.startswith('\'\\"'):
        # result += tabulation() + '<!-- ' + content + ' -->\n'
        return ''

    elif macros in HEADERS:
        result += tabulation() + '<header>' + content + '</header>\n'

    elif macros in HANGING_PARAGRAPHS:
        result += closetags(3)
        result += tabulation() + '<p>\n'
        tagstack.append('p')
        result += tabulation() + '<span>\n'
        tagstack.append('left')
        return result

    elif macros in FLUSH_LEFT_PARAGRAPHS:
        result += closetags(3)
        result += tabulation() + '<p>\n'
        tagstack.append('p')

    elif macros in INTENTED_BLOCKS:
        result += closetags(5)
        if macros == '.RS':
            result += tabulation() + '<p class="intented">\n'
            tagstack.append('p')

    elif macros in SECTION_SUBHEADINGS:
        result += closetags(2)
        result += tabulation() + '<section>\n'
        tagstack.append('ssection')
        result += tabulation() + '<h4>' + content.strip('"') + '</h4>\n'
        result += tabulation() + '<p>\n'
        tagstack.append('p')

    elif macros in SECTION_HEADINGS:
        result += closetags(1)
        result += tabulation() + '<section>\n'
        tagstack.append('section')
        result += tabulation() + '<h3>' + content.strip('"') + '</h3>\n'
        result += tabulation() + '<p>\n'
        tagstack.append('p')

    elif macros in LISTS:

        if macros == '.nf':
            result += closetags(4)
            result += tabulation() + '<ul>\n'
            tagstack.append('ul')

        elif macros == '.fi':
            result += closetags(4)

        return result

    elif macros in LINE_BREAK_AND_SPACING:

        if macros == '.br':
            if content:
                result += tabulation() + content + '\n'
            result += tabulation() + '<br>\n'

    elif macros in STYLES:

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

        result += tabulation() + " ".join(content) + '\n'

    else:

        if macros not in unknown:
            print('Unknown macros: "' + macros + '"')
            unknown.add(macros)
        # result += tabulation() + macros + ' ' + content + '\n'

        return ''

    if tagstack:

        if tagstack[-1] == 'left':
            result += closetags(4)
            result += tabulation() + '<span>\n'
            tagstack.append('right')

        elif tagstack[-1] == 'ul':
            result = tabulation() + '<li>\n' + result
            result += tabulation() + '</li>\n'

    return result


def closetags(lvl):

    result = ''

    if tagstack:

        if lvl <= 6 and tagstack[-1] == 'p':
            tagstack.pop()
            result += tabulation() + '</p>\n'

        if lvl <= 5 and tagstack[-1] == 'li':
            tagstack.pop()
            result += tabulation() + '</li>\n'

        if lvl <= 4 and tagstack[-1] == 'ul':
            tagstack.pop()
            result += tabulation() + '</ul>\n'

        if lvl <= 4 and (tagstack[-1] == 'left' or tagstack[-1] == 'right'):
            tagstack.pop()
            result += tabulation() + '</span>\n'

        if lvl <= 3 and tagstack[-1] == 'p':
            tagstack.pop()
            result += tabulation() + '</p>\n'

        if lvl <= 2 and tagstack[-1] == 'ssection':
            tagstack.pop()
            result += tabulation() + '</section>\n'

        if lvl <= 1 and tagstack[-1] == 'section':
            tagstack.pop()
            result += tabulation() + '</section>\n'

    return result


def parseline(line):

    macros = None
    content = clearline(line.strip())
    match = re.match(r'^[\.\']\S+', line)

    if match:
        macros = match.group(0)
        content = clearline(line[len(macros) + 1:].strip())

    return macros, content


def clearline(line):

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


if __name__ == '__main__':

    # targ = 'ls'
    targ = ''

    if len(sys.argv) == 1:
        while not targ:
            targ = input("Input the command-name\nFor example 'python'\n")
    else:
        targ = sys.argv[1]

    place = subprocess.check_output(['man', '-w', targ]).decode().strip()
    man = subprocess.check_output(['zcat', place]).decode().splitlines()

    with open('index.html', 'w') as htmlfile:
        writehtml(man, htmlfile.write)
