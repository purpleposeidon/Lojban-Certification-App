#!/usr/bin/python
# -*- coding: utf-8 -*-


import sys
import io
import cgi
import random
import time

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
    if self.comment: comment = "<span class=\"remark\">{0}</span>".format(self.comment)
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
      if comment: comment = "<span class=\"remark\">{0}</span>".format(comment)
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
    self.variables = {'TITLE':"Lojban Test", 'DATE': time.asctime()}
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
      if ':' in l and (l.split(':')[0].upper() == 'SET'):
        #SET:VARIABLENAME whatever value
        v = l.split(':', 1)[1]
        var, val = v.strip().split(' ', 1)
        self.variables[var] = val.strip()
        #sys.stderr.write(' '.join(['set', var, 'to', val])+'\n')
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

def main(fd):
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
.remark {
  display: none;
}
.shownremark {
  background-color: white;
  border: 2px solid black;
  color: black;
  position: relative;
  top: 7px;
  left: 3em;
  padding: 2px;
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
.good {
  border-color: rgb(0, 127, 0);
  border-width: thick;
  border-style: solid;
}
.bad {
  border-color: rgb(127, 0, 0);
  border-width: thick;
  border-style: solid;
}
  </style> 
  <script type="text/javascript">
/* <![CDATA[ */
function grade() {
  var sa = document.getElementById("sa").checked;
  var i, inputs;
  questions = document.getElementsByClassName("question");
  var total = questions.length;
  var right = 0;
  var unmarked = 0;
  i = total;
  
  //For each question...
  while (i) {
    i -= 1;
    
    var answers = questions[i].getElementsByTagName("li");
    var n = answers.length;
    var marked = false;
    
    // Show the correct item
    var correct_answer = questions[i].getElementsByClassName("correct")[0];
    if (sa) {
      correct_answer.style.backgroundColor = "pink";
    }
    else {
      correct_answer.style.backgroundColor = "";
    }

    
    //For each answer...
    while (n) {
      var right_answer = false;
      n -= 1;
      var style = answers[n].style;
      
      if (answers[n].getElementsByTagName("input")[0].checked) {
        if (answers[n].className == "correct") {
          style.color = "green"
          style.backgroundColor = "";
          right += 1;
          right_answer = true;
          //correct_answer.style.backgroundColor = "";
        }
        else {
          style.color = "red";
          style.backgroundColor = "black";
        }
        style.fontWeight = "bold";
        marked = true;
        var remark = answers[n].getElementsByClassName("remark");
        if (remark.length) {
          remark[0].className = "shownremark"
        }
      }
      else {
        var remark = answers[n].getElementsByClassName("shownremark");
        if (remark.length) {
          remark[0].className = "remark"
        }
        style.color = "";
        style.fontWeight = "";
        if (answers[n] != correct_answer) {
          style.backgroundColor = "";
        }
      }
    }
    
    //Didn't answer the question
    if (!marked) {
      questions[i].style.backgroundColor = "yellow";
      unmarked += 1;
    }
    else {
      questions[i].style.backgroundColor = "";
    }
  }
  // Show the peep's score
  var score;
  score = right + "/" + total;
  if (unmarked) {
    score += " (" + unmarked + " unmarked)"
  }
  document.getElementById("results").innerHTML = score
}

/* ]]> */
  </script>
</head>
<body>
%s
%s
</ol>
%s
<div>
  <input type="button" onclick="grade();" value="Grade" /> <label for="sa"><input type="checkbox" id="sa" />Show correct answers</label>
  <br/>
  <span>Your score: <b id="results">Ungraded</b></span>
</div>
</body>
</html>""" % (buff.variables.get('TITLE', 'Lojban Test'), buff.variables.get("HEADER", ''), buff.stdout.read(), buff.variables.get("FOOTER", '')))

if __name__ == '__main__':
  if len(sys.argv) == 1:
    sys.stderr.write("""Usage:
    build.py file1 file2 file3...
""")
    raise SystemExit(-1)
  for file_name in sys.argv[1:]:
    r = main(open(file_name, 'r'))
    if not r:
      raise SystemExit(r)
  raise SystemExit(0)
