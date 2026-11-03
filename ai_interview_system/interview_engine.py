# -------------------------------
# interview_engine.py - question bank, answer grading, report-card text
# -------------------------------
import random
import re

# keywords are matched as lowercase substrings ("inherit" matches "inheritance")
# ---------------------------------------------------------------------
# MCQ question bank.  'o' = options, 'a' = index of the correct option, 'e' = explanation
# ---------------------------------------------------------------------
HR_QUESTIONS = [
    {'q': 'A teammate misses a deadline that affects your work. What is the best first step?',
     'o': ['Report them to the manager immediately', 'Talk to them privately to understand the problem and offer help',
           'Do their part silently and say nothing', 'Complain about it in the team chat'], 'a': 1,
     'e': 'Speak to the person first, understand the cause and work out a solution together.'},
    {'q': 'You are given a task with a tool you have never used. What do you do?',
     'o': ['Refuse because it is not your skill', 'Wait until someone teaches you', 'Learn the basics quickly, try, and ask for help where stuck',
           'Pass the task to a colleague'], 'a': 2,
     'e': 'Showing initiative to learn fast while asking for help when needed is what employers look for.'},
    {'q': 'Which is the best answer to "What is your greatest weakness?"',
     'o': ['I have no weaknesses', 'I work too hard', 'I used to struggle with public speaking, so I now practise by presenting in team meetings',
           'I do not like being told what to do'], 'a': 2,
     'e': 'Pick a genuine weakness and show the concrete steps you are taking to improve it.'},
    {'q': 'Your manager gives you critical feedback on your work. How should you respond?',
     'o': ['Defend yourself and explain why you were right', 'Listen, ask clarifying questions and act on it', 'Ignore it if you disagree',
           'Take it personally and stay silent'], 'a': 1,
     'e': 'Constructive feedback is an opportunity to improve; listen, clarify and act.'},
    {'q': 'Two deadlines clash on the same day. What is the most professional approach?',
     'o': ['Work on the one you like more', 'Prioritise by urgency and impact, and inform stakeholders early',
           'Finish both poorly rather than telling anyone', 'Wait to see which one the manager asks about'], 'a': 1,
     'e': 'Prioritise, communicate early and negotiate timelines.'},
    {'q': 'Why do companies ask "Tell me about yourself"?',
     'o': ['To hear your life story in detail', 'To see how you summarise your skills, experience and goals relevant to the role',
           'To test your memory', 'To find personal weaknesses'], 'a': 1,
     'e': 'It is a chance to give a short, relevant summary of education, skills, projects and goals.'},
]

TECH_QUESTIONS = {
    'python': [
        {'q': 'Which of these data types is immutable in Python?', 'o': ['list', 'dict', 'tuple', 'set'], 'a': 2, 'e': 'Tuples cannot be changed after creation; lists, dicts and sets can.'},
        {'q': 'What does the "yield" keyword do?', 'o': ['Ends the program', 'Turns a function into a generator that produces values lazily', 'Imports a module', 'Raises an exception'], 'a': 1, 'e': 'yield makes a generator function that returns values one at a time.'},
        {'q': 'What is the output of print(type([]))?', 'o': ["<class 'tuple'>", "<class 'list'>", "<class 'dict'>", "<class 'array'>"], 'a': 1, 'e': '[] is an empty list literal.'},
        {'q': 'Which block always runs, whether or not an exception occurs?', 'o': ['try', 'except', 'else', 'finally'], 'a': 3, 'e': 'finally always executes, used for clean-up.'},
        {'q': 'What is a decorator in Python?', 'o': ['A function that wraps another function to add behaviour', 'A type of loop', 'A comment style', 'A class attribute'], 'a': 0, 'e': 'Decorators wrap functions and are applied with the @ syntax.'},
        {'q': 'What is the output of print(10 // 3)?', 'o': ['3.33', '3', '4', '1'], 'a': 1, 'e': '// is floor division.'},
        {'q': 'Which keyword is used to define a function?', 'o': ['function', 'func', 'def', 'lambda only'], 'a': 2, 'e': 'Functions are defined with def.'},
        {'q': 'What does copy.deepcopy() do differently from copy.copy()?', 'o': ['Nothing', 'Also copies nested objects recursively', 'Only copies the first element', 'Deletes the original'], 'a': 1, 'e': 'Deep copy duplicates nested objects; shallow copy shares them.'},
        {'q': 'What does the GIL in CPython do?', 'o': ['Lets many threads run bytecode at once', 'Allows only one thread to execute Python bytecode at a time', 'Speeds up I/O', 'Garbage collects memory'], 'a': 1, 'e': 'The Global Interpreter Lock allows one thread at a time to run bytecode.'},
    ],
    'java': [
        {'q': 'Which is NOT one of the four pillars of OOP?', 'o': ['Encapsulation', 'Compilation', 'Polymorphism', 'Abstraction'], 'a': 1, 'e': 'The pillars are encapsulation, inheritance, polymorphism and abstraction.'},
        {'q': 'What does == compare for objects in Java?', 'o': ['Contents', 'References (memory addresses)', 'Hash codes only', 'Class names'], 'a': 1, 'e': '== compares references; equals() compares content when overridden.'},
        {'q': 'Which keyword is used to inherit a class?', 'o': ['implements', 'inherits', 'extends', 'super'], 'a': 2, 'e': 'A class extends another class; it implements interfaces.'},
        {'q': 'What is the default value of a boolean field in Java?', 'o': ['true', 'false', 'null', '0'], 'a': 1, 'e': 'Boolean fields default to false.'},
        {'q': 'Which collection does NOT allow duplicate elements?', 'o': ['ArrayList', 'LinkedList', 'HashSet', 'Vector'], 'a': 2, 'e': 'A Set stores unique elements only.'},
        {'q': 'What does the JVM garbage collector do?', 'o': ['Compiles code', 'Frees memory of unreachable objects', 'Formats source code', 'Closes network sockets'], 'a': 1, 'e': 'It automatically reclaims heap memory of objects no longer referenced.'},
        {'q': 'The entry point of a Java application is:', 'o': ['start()', 'run()', 'public static void main(String[] args)', 'init()'], 'a': 2, 'e': 'The JVM starts execution at the main method.'},
        {'q': 'What is the output of System.out.println(1 + 2 + "3")?', 'o': ['33', '123', '6', 'Error'], 'a': 0, 'e': '1+2 = 3 first, then concatenated with "3" -> "33".'},
        {'q': 'An interface in Java can contain:', 'o': ['Only instance variables', 'Method declarations (contracts) that classes implement', 'Constructors', 'Only main methods'], 'a': 1, 'e': 'Interfaces define contracts that implementing classes must fulfil.'},
    ],
    'php': [
        {'q': 'What does PHP stand for?', 'o': ['Personal Home Page', 'PHP: Hypertext Preprocessor', 'Pre Hypertext Processor', 'Private Hosting Platform'], 'a': 1, 'e': 'PHP is a recursive acronym: PHP: Hypertext Preprocessor.'},
        {'q': 'Which symbol starts a variable name in PHP?', 'o': ['#', '@', '$', '&'], 'a': 2, 'e': 'All PHP variables start with $.'},
        {'q': 'What is the difference between include and require?', 'o': ['None', 'require causes a fatal error if the file is missing, include only a warning', 'include is faster', 'require is only for classes'], 'a': 1, 'e': 'include warns and continues; require stops the script.'},
        {'q': 'Which function starts a session?', 'o': ['session_begin()', 'start_session()', 'session_start()', 'new_session()'], 'a': 2, 'e': 'session_start() creates or resumes a session.'},
        {'q': 'How should you prevent SQL injection?', 'o': ['Use prepared statements with bound parameters', 'Concatenate user input into the query', 'Hide the database name', 'Use GET instead of POST'], 'a': 0, 'e': 'Prepared statements (PDO / MySQLi) keep data separate from SQL.'},
        {'q': 'What is the difference between == and === ?', 'o': ['No difference', '=== also compares the type', '== also compares the type', '=== is assignment'], 'a': 1, 'e': '=== is strict: value and type must match.'},
        {'q': 'Which superglobal contains data submitted by an HTML form using POST?', 'o': ['$_GET', '$_POST', '$_FORM', '$_DATA'], 'a': 1, 'e': '$_POST holds data sent in the HTTP request body.'},
        {'q': 'Which of these is an associative array?', 'o': ['[1, 2, 3]', "['name' => 'Ravi', 'age' => 21]", 'array(5)', 'None of these'], 'a': 1, 'e': 'Associative arrays use named keys.'},
        {'q': 'What is the output of echo 2 ** 3; ?', 'o': ['6', '8', '9', 'Error'], 'a': 1, 'e': '** is the exponent operator.'},
    ],
    'general': [
        {'q': 'What is the main difference between a process and a thread?', 'o': ['Threads share the memory of their process, processes have separate memory', 'They are the same', 'Processes are lighter than threads', 'Threads cannot run in parallel'], 'a': 0, 'e': 'Threads live inside a process and share its memory.'},
        {'q': 'Which of these is a NoSQL database?', 'o': ['MySQL', 'PostgreSQL', 'MongoDB', 'Oracle'], 'a': 2, 'e': 'MongoDB is a document (NoSQL) database.'},
        {'q': 'Which HTTP method is normally used to create a new resource in a REST API?', 'o': ['GET', 'POST', 'DELETE', 'HEAD'], 'a': 1, 'e': 'POST creates; GET reads; PUT/PATCH update; DELETE removes.'},
        {'q': 'What does SQL JOIN do?', 'o': ['Deletes duplicate rows', 'Combines rows from two or more tables based on a related column', 'Creates a new database', 'Encrypts data'], 'a': 1, 'e': 'JOIN links tables through related columns.'},
        {'q': 'Which data structure works on First-In-First-Out (FIFO)?', 'o': ['Stack', 'Queue', 'Tree', 'Graph'], 'a': 1, 'e': 'A queue removes the oldest element first.'},
        {'q': 'What is the time complexity of binary search on a sorted array?', 'o': ['O(n)', 'O(log n)', 'O(n log n)', 'O(1)'], 'a': 1, 'e': 'Binary search halves the search space each step.'},
        {'q': 'What does Git "commit" do?', 'o': ['Uploads code to the internet', 'Records a snapshot of staged changes in the local repository', 'Deletes the repository', 'Merges two branches'], 'a': 1, 'e': 'A commit saves staged changes to local history.'},
        {'q': 'Which of these best describes a REST API?', 'o': ['A database engine', 'Stateless HTTP-based interface working on resources / URLs', 'A programming language', 'A web browser'], 'a': 1, 'e': 'REST uses HTTP verbs on resources and is stateless.'},
    ],
}

N_HR = 2
N_TECH = 8
MARKS_PER_Q = 5            # 10 questions x 5 = 50 marks


def pick_questions(subject, hr=N_HR, tech=N_TECH):
    """Random MCQs with shuffled options. The correct index is stored server-side only."""
    pool = TECH_QUESTIONS.get(subject, TECH_QUESTIONS['general'])
    picked = [('HR', q) for q in random.sample(HR_QUESTIONS, hr)]
    picked += [(subject.capitalize(), q) for q in random.sample(pool, min(tech, len(pool)))]
    out = []
    for typ, q in picked:
        order = list(range(len(q['o'])))
        random.shuffle(order)
        out.append({'type': typ, 'q': q['q'], 'o': [q['o'][i] for i in order],
                    'a': order.index(q['a']), 'e': q['e']})
    return out


def grade_mcq(question, choice):
    """choice = selected option index or None. Returns dict(marks, correct, choice, ans, comment)."""
    ans = question['a']
    if choice is None or choice == '':
        return {'marks': 0.0, 'correct': False, 'choice': None, 'ans': ans, 'comment': 'Not answered.'}
    choice = int(choice)
    ok = choice == ans
    return {'marks': float(MARKS_PER_Q) if ok else 0.0, 'correct': ok, 'choice': choice, 'ans': ans,
            'comment': 'Correct!' if ok else 'Incorrect.'}


def grade_letter(pct):
    for cut, g in ((90, 'A+'), (80, 'A'), (70, 'B+'), (60, 'B'), (50, 'C'), (40, 'D')):
        if pct >= cut:
            return g
    return 'F'


def build_feedback(interview_pct, personality, answers, integrity_flags):
    strengths, improve = [], []
    right = [a for a in answers if a.get('correct')]
    wrong = [a for a in answers if not a.get('correct') and a.get('choice') is not None]
    skipped = [a for a in answers if a.get('choice') is None]
    if interview_pct >= 70:
        strengths.append(f'Strong technical knowledge - {len(right)} of {len(answers)} questions correct.')
    elif interview_pct < 50:
        improve.append('Revise the core concepts of your subject; less than half of the answers were correct.')
    by_type = {}
    for a in answers:
        d = by_type.setdefault(a['type'], [0, 0])
        d[1] += 1
        d[0] += 1 if a.get('correct') else 0
    for typ, (c, n) in by_type.items():
        if n and c / n >= 0.75:
            strengths.append(f'Good {typ} section: {c}/{n} correct.')
        elif n and c / n < 0.5:
            improve.append(f'{typ} section needs work: {c}/{n} correct - study the explanations below.')
    if skipped:
        improve.append(f'{len(skipped)} question(s) were left unanswered.')
    for t in personality.get('traits', []):
        (improve if any(w in t for w in ('tension', 'stress', 'away', 'unsure', 'could')) else strengths).append(t + '.')
    if integrity_flags:
        improve.append('Integrity alerts were recorded: ' + '; '.join(integrity_flags) + '.')
    return strengths, improve
