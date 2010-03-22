#!/usr/bin/python


import sys
import io
import cgi
import random


sample = io.StringIO("""
SECTION: Lojban Vocabulary
  This part tests your vocabulary.
GROUP: Translate the number
QUESTION: BEEFB1B (hexadecimal)
  * li feireireivaifeipafei //Uh, probably not really correct, probably needs a base...
  + li recicivosomucireci
      No! What is it in hexadecimal?
  + na namcu
      It is a number in base 16.
  + lo broda
  + la .bifbib
QUESTION: 23
  * li reci
  + li soci
  + reci
  + li pano
  + la tutri
  + 23

GROUP: Pick the definition for the gismu
QUESTION: broda
  * gismu variable
  * anything
  + run
  + walk
  + go
  + sleep
  + talk
  + read
QUESTION: cusku
  * say
  * express
  + walk
  + greet


SECTION: Lojban Grammar
  This part tests your knowledge of Lojban grammar
GROUP: Pick the correct terminator
QUESTION: lo broda __ barda
  * cu
  * ku
  + be'o
  + kei
  + vau
  + fa'o
QUESTION: viska fa lo mamta be la timos __ lo mi patfu 
  * be'o
  * ku
  + kei
  + va'o
  + dau
  + vau
  + .i
GROUP: Which terminator is unnecessary?
  (You can click on the underlined portion to give your answer)
QUESTION: lo mlatu be lo do +mamta:that's not a terminator!+ +cu:very necessary+ barda *vau:And we all know why!*
QUESTION: se nu lo prenu *ku* lo rokci be mi +be'o+ na du +kei+ ta
//QUESTION: doi lo pendo be lo tarci +do'u+ xamgu nuzba +.i:not a terminator!+
""")

def section(buff):
  head, value = buff.next().split(':', 1)
  global OPEN_GROUP
  if OPEN_GROUP:
    buff.write("</ol>")
    OPEN_GROUP = False
  buff.write("<h1>{0}</h1>".format(value.strip()))
  while 1:
    l = buff.next()
    if l and l[0] == ' ':
      buff.write("<p>{0}</p>".format(l.strip()))
    else:
      buff.back()
      break

OPEN_GROUP = False
def group(buff):
  global OPEN_GROUP
  if OPEN_GROUP:
    buff.write("</ol>")
  head, value = buff.next().split(':', 1)
  buff.write("<h2>{0}</h2>".format(value.strip()))
  OPEN_GROUP = True

  while 1:
    l = buff.next()
    if l and l[0] == ' ':
      buff.write("<p>{0}</p>".format(l.strip()))
    else:
      buff.back()
      break
  buff.write("<ol class=\"testquestions\">")

class Option:
  def __init__(self, buff):
    val = buff.next() #.strip()
    whitespace = len(val) - len(val.lstrip())
    val = val.strip()
    if not val[0] in '*+':
      raise SyntaxError("Option must start with either a * or a +")
    self.correct = val[0] == '*'
    self.value = val[1:].lstrip()
    comment = buff.next()
    if comment[whitespace:] and comment[whitespace:][0] == ' ':
      self.comment = comment.strip()
    else:
      self.comment = None
      buff.back()
  def format(self, q_count, a_count):
    if self.correct: style = 'correct'
    else: style = "wrong"
    if self.comment: comment = "<div class=\"comment\">{0}</div>".format(self.comment)
    else: comment = ''
    return "\t\t<li class=\"{2}\"><input type=\"radio\" name=\"q{0}\" id=\"q{0}a{1}\"/> <label for=\"q{0}a{1}\">{3}</label>{4}</li>".format(q_count, a_count, style, self.value, comment)



def get_options(buff):
  correct = []
  wrong = []
  while 1:
    l = buff.next()
    buff.back()
    if l and l[0] == ' ':
      op = Option(buff)
      if op.correct:
        correct.append(op)
      else:
        wrong.append(op)
    else: break
  return correct, wrong

MAX_OPTIONS = 4
QCOUNT = 0
def question(buff):
  global QCOUNT
  QCOUNT += 1
  head, value = buff.next().split(':', 1)
  if '*'.count(head) >= 2:
    if '*'.count(head) % 2:
      raise SyntaxError("There should be an even number of *'s and stuff you know man?")
  if '+'.count(head) >= 2:
    if '+'.count(head) % 2:
      raise SyntaxError("There should be an even number of +'s and stuff you know man?")
  if '*' in value:
    #It's a pick-the-bad-bit question
    in_option = False
    in_option_comment = False
    out = ''
    options = []
    comments = []
    corrects = []
    a_count = 0
    for c in value:
      if c in '+*':
        if in_option:
          in_option = False
          in_option_comment = False
          out += "</label>"
        else:
          in_option = c
          corrects.append(c == '*')
          options.append('')
          comments.append('')
          a_count += 1
          out += "<label for=\"q{0}a{1}\">".format(QCOUNT, a_count)
      else:
        if in_option:
          if in_option_comment:
            comments[-1] += c
          else:
            if c == ':':
              in_option_comment = True
            else:
              options[-1] += c
              out += c
        else:
          out += c
    buff.write("<li class=\"question\">{0}".format(out.strip()))
    buff.write("\t<ol>")
    a_count = 0
    for option, comment, correct in zip(options, comments, corrects):
      a_count += 1
      if correct: style = "correct"
      else: style = "wrong"
      if comment: comment = "<div class=\"comment\">{0}</div>".format(comment)
      else: comment = ''
      buff.write("\t\t<li class=\"{0}\"><input type=\"radio\" name=\"q{1}\" id=\"q{1}a{2}\" /><label for=\"q{1}a{2}\">{3}</label>{4}</li>".format(style, QCOUNT, a_count, option, comment))
    buff.write("\t</ol>")
    buff.write("\t</li>")
  else:
    while '__' in value:
      value = value.replace('__', '_')
    value = value.replace('_', '_'*4)
    buff.write("<li class=\"question\">{0}".format(value.strip()))
    buff.write("\t<ol class=\"answers\">")
    right, wrong = get_options(buff)
    assert right
    options = [random.choice(right)]
    if wrong:
      random.shuffle(wrong)
    options += wrong[:MAX_OPTIONS-1]
    random.shuffle(options)
    a_count = 0
    for o in options:
      a_count += 1
      buff.write(o.format(QCOUNT, a_count))
    buff.write("\t</ol>")
    buff.write("</li>")


class Buffer:
  def __init__(self, fd):
    self.fd = fd
    self.lines = []
    self.index = -1
    self.stdout = io.StringIO('')
    self.variables = {'TITLE':"Lojban Test"}
  def write(self, val):
    self.stdout.write(unicode(val).replace('\t', ' '*4)+'\n')
  def next(self):
    self.index += 1
    while self.fd and len(self.lines) <= self.index:
      l = self.fd.readline()
      l = cgi.escape(l.replace('\t', ' '*4)) #Escape html characters and expand tabs
      if '//' in l:
        #Strip out comments
        l = l[:l.index('//')]
      if ':' in l and l.split(':')[0].upper() == 'SET':
        #SET:VARIABLENAME whatever value
        v = l.split(':', 1)[1]
        var, val = v.split(' ', 0)
        self.variables[var] = val.strip()
        continue
      for key, val in self.variables.items():
        l = l.replace(key, val)
      if l == '':
        self.fd = None
        break
      self.lines.append(l)
    try:
      l = self.lines[self.index]
      return l
    except:
      raise EOFError
  def back(self):
    self.index -= 1

def main():
  fd = sample
  buff = Buffer(fd)
  while 1:
    try:
      line = buff.next()
    except EOFError:
      break
    type_ = line.split(':')[0].strip().upper()
    if type_:
      buff.back()
      {"SECTION":section, "GROUP":group, "QUESTION":question}[type_](buff)
  buff.stdout.seek(0)
  print("""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd"> 
<html xmlns="http://www.w3.org/1999/xhtml"> 
<head> 
  <meta http-equiv="Content-Type" content="text/html;charset=utf-8" /> 
  <title>%s</title>
  <style type="text/css"> 
    .answers li { 
      list-style-type: lower-alpha; 
      padding-right: 0px;
    } 

    label { 
      cursor: pointer;
    }
    .question > label {
      text-decoration: underline; 
    }
    .comment {
      display: none;
    }
    input[type="radio"] {
      position: relative;
      /*left: -.5em;*/
    }
    h1 {
      margin-top: 3em;
    }
    h1:first-child {
      margin-top: 1em;
    }
    h2 {
      font-size: large;
      margin-top: 2em;
      margin-left: 1em;
    }
    p {
      margin-left: 5em;
    }
    ol.testquestions {
      margin-left: 2em;
    }
    ol.testquestions > li {
      margin-top: .5em;
    }
  </style> 
</head>
<body>
%s
%s
</ol>
%s
</body>
</html>""" % (buff.variables.get('TITLE', 'Lojban Test'), buff.variables.get("HEADER", ''), buff.stdout.read(), buff.variables.get("FOOTER", '')))

if __name__ == '__main__':
  r = main()
  raise SystemExit(r)
