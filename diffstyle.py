#!/usr/bin/env python

import difflib
import sys


def process(original, corrected):
    """
    Returns a list of violations that are found
    """
    original_lines = []
    corrected_lines = []
    gen = difflib.unified_diff(original, corrected, n=0)

    try:
        # Skip the first 2 lines of the diff output (the header lines)
        gen.next()
        gen.next()
    except StopIteration:
        # There was no diff output, no violations to return
        return []

    current_line = parse_starting_line_num(gen.next())

    all_violations = []

    for line in gen:
        if line[0] == "-":
            original_lines.append(line[1:])
        elif line[0] == "+":
            corrected_lines.append(line[1:])
        elif line[0] == "@":
            all_violations += process_chunk(
                current_line,
                original_lines,
                corrected_lines)

            original_lines = []
            corrected_lines = []
            current_line = parse_starting_line_num(line)
        else:
            raise RuntimeError("Impossible line: " + line)

    all_violations += process_chunk(
        current_line,
        original_lines,
        corrected_lines)

    return all_violations


class Violation(object):
    def __init__(self, line, col, text):
        self.line = line
        self.col = col
        self.text = text
        self.filename = None

    def __repr__(self):
        filenameStr = self.filename

        if not filenameStr:
            filenameStr = "<unknown>"

        if self.text:
            message = "Fix Style, should be: " + self.text
        else:
            message = "Invalid Whitespace"

        return filenameStr + ':' + \
            str(self.line) + ':' + \
            str(self.col) + ': ' + \
            message


def create_message(original_line, corrected_line):
    if original_line.strip() == corrected_line.strip():
        return "Fix Indentation/Whitespace"
    else:
        return corrected_line.strip()


def process_chunk(line_num, original_lines, corrected_lines):
    violations = []

    if len(original_lines) == len(corrected_lines):
        for i in xrange(0, len(original_lines)):
            column = string_diff_column(original_lines[i], corrected_lines[i])
            message = create_message(original_lines[i], corrected_lines[i])
            violations.append(Violation(line_num + i, column, message))

    elif len(original_lines) == 0:
        v = Violation(line_num, 1, "New line required here")
        violations.append(v)

    elif len(original_lines) < len(corrected_lines):
        for i in xrange(0, len(original_lines)):
            column = string_diff_column(original_lines[i], corrected_lines[i])
            message = create_message(original_lines[i], corrected_lines[i])
            violations.append(Violation(line_num + i, column, message))

    elif len(corrected_lines) == 0:
        for i in xrange(0, len(original_lines)):
            v = Violation(line_num + i, 1, "")
            violations.append(v)

    elif len(original_lines) > len(corrected_lines):
        for i in xrange(0, len(corrected_lines)):
            column = string_diff_column(original_lines[i], corrected_lines[i])
            message = create_message(original_lines[i], corrected_lines[i])
            violations.append(Violation(line_num + i, column, message))

    return violations


def parse_starting_line_num(line):
    """
    >>> parse_starting_line_num("@@ -7,2 +6 @@")
    7
    >>> parse_starting_line_num("@@ -12 +10 @@")
    12
    """
    startIndex = 4
    endIndex1 = line.find(',', startIndex)
    endIndex2 = line.find(' ', startIndex)
    if endIndex1 != -1:
        endIndex = endIndex1
    if endIndex2 != -1 and (endIndex1 == -1 or endIndex2 < endIndex):
        endIndex = endIndex2
    numStr = line[startIndex:endIndex]
    return int(numStr)


def string_diff_column(str1, str2):
    """
    >>> string_diff_column("ab1", "ab2")
    3
    >>> string_diff_column("ab1c3e", "ab2c4e")
    3
    >>> string_diff_column("abc", "abcd")
    3
    >>> string_diff_column("abcd", "abc")
    3
    >>> string_diff_column("a", "")
    1
    >>> string_diff_column("", "a")
    1
    >>> string_diff_column("", "")
    1
    """
    c = 1
    for i in xrange(0, min(len(str1), len(str2))):
        c = i
        if str1[i] != str2[i]:
            break

    if c >= len(str1) or c >= len(str2):
        c -= 1

    return c + 1


def read_file(filename):
    with open(filename) as f:
        return f.readlines()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Usage: " + sys.argv[0] + " FILE"
        sys.exit(1)

    original_filename = sys.argv[1]

    original_file = read_file(original_filename)

    if len(sys.argv) == 3:
        corrected_file = read_file(sys.argv[2])
    else:
        corrected_file = sys.stdin.readlines()

    violations = process(original_file, corrected_file)

    for v in violations:
        v.filename = original_filename
        print v

    if len(violations) == 0:
        # No violtaions: success!
        sys.exit(0)
    else:
        sys.exit(2)
