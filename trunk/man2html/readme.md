Man2HTML
========

What is it?
-----------
Man2HTML - программа, конвертирующая
man файл в HTML формат
Принимает unix-команду,
создает файл index.html в текущей директории
Использует стили из файла styles.css,
находящийся в текущей директории

How to run?
-----------
./man2html.py command

Availabe macroses
-----------------
+ HEADERS: .TH
+ HANGING_PARAGRAPHS: .TP, .HP
+ FLUSH\_LEFT\_PARAGRAPHS: .LP, .PP, .P, .IP
+ INTENTED_BLOCKS: .RS, .RE
+ SECTION_HEADINGS: .SH
+ SECTION_SUBHEADINGS: .SS
+ LINE\_BREAK: .br
+ STYLES: .B, .I, .IR, .RI, .BI, .IB, .BR, .RB
+ LISTS: .nf, .fi

Ignoring macroses:
------------------
+ .pc
+ .ie
+ .el
+ .\\}
+ .if

Author
------
Vikharev Slava CS-201
