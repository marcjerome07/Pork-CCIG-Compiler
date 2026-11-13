"""Pork CCig lexical analyzer: one DFA, states 0-299, written as if/elif transitions.

    tokens, errors = tokenize(source)

Run this file directly for a demonstration:

    py backend/lexer/dfa_lexer.py
"""

from dataclasses import dataclass

SPACE = "space"
TAB = "tab"
NEWLINE = "newline"
IDENTIFIER = "id"
MEAT_LITERAL = "meat_lit"
SAUCE_LITERAL = "sauce_lit"
CHOP_LITERAL = "chop_lit"
RECIPE_LITERAL = "recipe_lit"
SINGLE_LINE_COMMENT = "Single-Line Comment"
MULTI_LINE_COMMENT = "Multi-Line Comment"

EOF = ""
NO_TRANSITION = -1
NOT_FINAL = ""

# Character classes
WHITESPACE = " \t\n"
DIGITS = "0123456789"
LOWERCASE = "abcdefghijklmnopqrstuvwxyz"
UPPERCASE = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
ALPHA = LOWERCASE + UPPERCASE
ALPHA_ID = ALPHA + "_"
ALPHA_NUM = DIGITS + ALPHA_ID
OPERATORS = "+-*/%<>=!&|"
UNAVAILABLE = "$?@^"
PRINTABLE = "".join(chr(code) for code in range(32, 127))
ESCAPE_SEQ = "nt'\"\\0"
ASCII1 = PRINTABLE.replace("\\", "").replace("'", "")
ASCII2 = PRINTABLE.replace("\\", "").replace('"', "")
ASCII3 = PRINTABLE
ASCII4 = PRINTABLE.replace(" ", "")

# Delimiter sets
DELIM1 = ";" + WHITESPACE
DELIM2 = ":" + WHITESPACE
DELIM3 = "{" + WHITESPACE
DELIM4 = "(" + WHITESPACE
DELIM5 = ",({;" + WHITESPACE
DELIM6 = OPERATORS + "})]:;," + WHITESPACE
DELIM7 = ALPHA_NUM + "+-!{('\"" + WHITESPACE
DELIM8 = ALPHA_NUM + "+-!('\"" + WHITESPACE
DELIM9 = ALPHA_NUM + "-!('\"" + WHITESPACE
DELIM10 = ALPHA_ID + "()],;" + WHITESPACE
DELIM11 = ALPHA_NUM + "+-!(" + WHITESPACE
DELIM13 = ALPHA_NUM + "+-!{(/'\"" + WHITESPACE
DELIM14 = ALPHA_ID + "};," + WHITESPACE
DELIM15 = ALPHA_NUM + "-+!()'\"" + WHITESPACE
DELIM16 = OPERATORS + "{)[].,:;" + WHITESPACE
DELIM17 = ALPHA_NUM + "+-!(]'\"" + WHITESPACE
DELIM18 = OPERATORS + ")[],;" + WHITESPACE
DELIM19 = ALPHA_NUM + "{+-&'\"" + WHITESPACE
DELIM20 = ALPHA_NUM + "}+-" + WHITESPACE
DELIM21 = OPERATORS + "()[].,;" + WHITESPACE
DELIM22 = OPERATORS + ")]},:;" + WHITESPACE
DELIM23 = OPERATORS + "):]},;" + WHITESPACE
DELIM25 = ALPHA_NUM + OPERATORS + "{}()[]:;,'\"" + WHITESPACE


def has(chars, ch):
    return ch != EOF and ch in chars


def start_transition(ch):
    if ch == "a":
        return 1
    elif ch == "c":
        return 7
    elif ch == "d":
        return 22
    elif ch == "e":
        return 32
    elif ch == "f":
        return 42
    elif ch == "i":
        return 51
    elif ch == "m":
        return 54
    elif ch == "p":
        return 63
    elif ch == "r":
        return 68
    elif ch == "s":
        return 75
    elif ch == "t":
        return 105
    elif ch == "w":
        return 111
    elif ch == "y":
        return 117
    elif has(ALPHA_ID, ch):
        return 200
    elif has(DIGITS, ch):
        return 240
    elif ch == "=":
        return 127
    elif ch == "+":
        return 131
    elif ch == "-":
        return 137
    elif ch == "*":
        return 143
    elif ch == "/":
        return 147
    elif ch == "%":
        return 151
    elif ch == ">":
        return 155
    elif ch == "<":
        return 159
    elif ch == "!":
        return 163
    elif ch == "&":
        return 167
    elif ch == "|":
        return 171
    elif ch == "{":
        return 174
    elif ch == "}":
        return 176
    elif ch == "(":
        return 178
    elif ch == ")":
        return 180
    elif ch == "[":
        return 182
    elif ch == "]":
        return 184
    elif ch == ".":
        return 186
    elif ch == ",":
        return 188
    elif ch == ":":
        return 190
    elif ch == ";":
        return 192
    elif ch == " ":
        return 194
    elif ch == "\t":
        return 196
    elif ch == "\n":
        return 198
    elif ch == "'":
        return 285
    elif ch == '"':
        return 290
    return NO_TRANSITION


def keyword_transition(state, ch):
    # again
    if state == 1:
        if ch == "g":
            return 2
        elif has(ALPHA_NUM, ch):
            return 202
        elif ch == EOF or has(DELIM21, ch):
            return 201
    elif state == 2:
        if ch == "a":
            return 3
        elif has(ALPHA_NUM, ch):
            return 204
        elif ch == EOF or has(DELIM21, ch):
            return 203
    elif state == 3:
        if ch == "i":
            return 4
        elif has(ALPHA_NUM, ch):
            return 206
        elif ch == EOF or has(DELIM21, ch):
            return 205
    elif state == 4:
        if ch == "n":
            return 5
        elif has(ALPHA_NUM, ch):
            return 208
        elif ch == EOF or has(DELIM21, ch):
            return 207
    elif state == 5:
        if ch == EOF or has(DELIM1, ch):
            return 6
        elif has(ALPHA_NUM, ch):
            return 210
    # case, chop, cooked
    elif state == 7:
        if ch == "a":
            return 8
        elif ch == "h":
            return 12
        elif ch == "o":
            return 16
        elif has(ALPHA_NUM, ch):
            return 202
        elif ch == EOF or has(DELIM21, ch):
            return 201
    elif state == 8:
        if ch == "s":
            return 9
        elif has(ALPHA_NUM, ch):
            return 204
        elif ch == EOF or has(DELIM21, ch):
            return 203
    elif state == 9:
        if ch == "e":
            return 10
        elif has(ALPHA_NUM, ch):
            return 206
        elif ch == EOF or has(DELIM21, ch):
            return 205
    elif state == 10:
        if ch == EOF or has(DELIM2, ch):
            return 11
        elif has(ALPHA_NUM, ch):
            return 208
    elif state == 12:
        if ch == "o":
            return 13
        elif has(ALPHA_NUM, ch):
            return 204
        elif ch == EOF or has(DELIM21, ch):
            return 203
    elif state == 13:
        if ch == "p":
            return 14
        elif has(ALPHA_NUM, ch):
            return 206
        elif ch == EOF or has(DELIM21, ch):
            return 205
    elif state == 14:
        if ch == EOF or has(WHITESPACE, ch):
            return 15
        elif has(ALPHA_NUM, ch):
            return 208
    elif state == 16:
        if ch == "o":
            return 17
        elif has(ALPHA_NUM, ch):
            return 204
        elif ch == EOF or has(DELIM21, ch):
            return 203
    elif state == 17:
        if ch == "k":
            return 18
        elif has(ALPHA_NUM, ch):
            return 206
        elif ch == EOF or has(DELIM21, ch):
            return 205
    elif state == 18:
        if ch == "e":
            return 19
        elif has(ALPHA_NUM, ch):
            return 208
        elif ch == EOF or has(DELIM21, ch):
            return 207
    elif state == 19:
        if ch == "d":
            return 20
        elif has(ALPHA_NUM, ch):
            return 210
        elif ch == EOF or has(DELIM21, ch):
            return 209
    elif state == 20:
        if ch == EOF or has(WHITESPACE, ch):
            return 21
        elif has(ALPHA_NUM, ch):
            return 212
    # default, do
    elif state == 22:
        if ch == "e":
            return 23
        elif ch == "o":
            return 30
        elif has(ALPHA_NUM, ch):
            return 202
        elif ch == EOF or has(DELIM21, ch):
            return 201
    elif state == 23:
        if ch == "f":
            return 24
        elif has(ALPHA_NUM, ch):
            return 204
        elif ch == EOF or has(DELIM21, ch):
            return 203
    elif state == 24:
        if ch == "a":
            return 25
        elif has(ALPHA_NUM, ch):
            return 206
        elif ch == EOF or has(DELIM21, ch):
            return 205
    elif state == 25:
        if ch == "u":
            return 26
        elif has(ALPHA_NUM, ch):
            return 208
        elif ch == EOF or has(DELIM21, ch):
            return 207
    elif state == 26:
        if ch == "l":
            return 27
        elif has(ALPHA_NUM, ch):
            return 210
        elif ch == EOF or has(DELIM21, ch):
            return 209
    elif state == 27:
        if ch == "t":
            return 28
        elif has(ALPHA_NUM, ch):
            return 212
        elif ch == EOF or has(DELIM21, ch):
            return 211
    elif state == 28:
        if ch == EOF or has(DELIM2, ch):
            return 29
        elif has(ALPHA_NUM, ch):
            return 214
    elif state == 30:
        if ch == EOF or has(DELIM3, ch):
            return 31
        elif has(ALPHA_NUM, ch):
            return 204
    # else, empty
    elif state == 32:
        if ch == "l":
            return 33
        elif ch == "m":
            return 37
        elif has(ALPHA_NUM, ch):
            return 202
        elif ch == EOF or has(DELIM21, ch):
            return 201
    elif state == 33:
        if ch == "s":
            return 34
        elif has(ALPHA_NUM, ch):
            return 204
        elif ch == EOF or has(DELIM21, ch):
            return 203
    elif state == 34:
        if ch == "e":
            return 35
        elif has(ALPHA_NUM, ch):
            return 206
        elif ch == EOF or has(DELIM21, ch):
            return 205
    elif state == 35:
        if ch == EOF or has(DELIM3, ch):
            return 36
        elif has(ALPHA_NUM, ch):
            return 208
    elif state == 37:
        if ch == "p":
            return 38
        elif has(ALPHA_NUM, ch):
            return 204
        elif ch == EOF or has(DELIM21, ch):
            return 203
    elif state == 38:
        if ch == "t":
            return 39
        elif has(ALPHA_NUM, ch):
            return 206
        elif ch == EOF or has(DELIM21, ch):
            return 205
    elif state == 39:
        if ch == "y":
            return 40
        elif has(ALPHA_NUM, ch):
            return 208
        elif ch == EOF or has(DELIM21, ch):
            return 207
    elif state == 40:
        if ch == EOF or has(WHITESPACE, ch):
            return 41
        elif has(ALPHA_NUM, ch):
            return 210
    # fixed, for
    elif state == 42:
        if ch == "i":
            return 43
        elif ch == "o":
            return 48
        elif has(ALPHA_NUM, ch):
            return 202
        elif ch == EOF or has(DELIM21, ch):
            return 201
    elif state == 43:
        if ch == "x":
            return 44
        elif has(ALPHA_NUM, ch):
            return 204
        elif ch == EOF or has(DELIM21, ch):
            return 203
    elif state == 44:
        if ch == "e":
            return 45
        elif has(ALPHA_NUM, ch):
            return 206
        elif ch == EOF or has(DELIM21, ch):
            return 205
    elif state == 45:
        if ch == "d":
            return 46
        elif has(ALPHA_NUM, ch):
            return 208
        elif ch == EOF or has(DELIM21, ch):
            return 207
    elif state == 46:
        if ch == EOF or has(WHITESPACE, ch):
            return 47
        elif has(ALPHA_NUM, ch):
            return 210
    elif state == 48:
        if ch == "r":
            return 49
        elif has(ALPHA_NUM, ch):
            return 204
        elif ch == EOF or has(DELIM21, ch):
            return 203
    elif state == 49:
        if ch == EOF or has(DELIM4, ch):
            return 50
        elif has(ALPHA_NUM, ch):
            return 206
    # if
    elif state == 51:
        if ch == "f":
            return 52
        elif has(ALPHA_NUM, ch):
            return 202
        elif ch == EOF or has(DELIM21, ch):
            return 201
    elif state == 52:
        if ch == EOF or has(DELIM4, ch):
            return 53
        elif has(ALPHA_NUM, ch):
            return 204
    # meat, menu
    elif state == 54:
        if ch == "e":
            return 55
        elif has(ALPHA_NUM, ch):
            return 202
        elif ch == EOF or has(DELIM21, ch):
            return 201
    elif state == 55:
        if ch == "a":
            return 56
        elif ch == "n":
            return 60
        elif has(ALPHA_NUM, ch):
            return 204
        elif ch == EOF or has(DELIM21, ch):
            return 203
    elif state == 56:
        if ch == "t":
            return 57
        elif has(ALPHA_NUM, ch):
            return 206
        elif ch == EOF or has(DELIM21, ch):
            return 205
    elif state == 57:
        if ch == EOF or has(WHITESPACE, ch):
            return 58
        elif has(ALPHA_NUM, ch):
            return 208
    elif state == 59:  # alias of 55
        if ch == "a":
            return 56
        elif ch == "n":
            return 60
        elif has(ALPHA_NUM, ch):
            return 204
        elif ch == EOF or has(DELIM21, ch):
            return 203
    elif state == 60:
        if ch == "u":
            return 61
        elif has(ALPHA_NUM, ch):
            return 206
        elif ch == EOF or has(DELIM21, ch):
            return 205
    elif state == 61:
        if ch == EOF or has(WHITESPACE, ch):
            return 62
        elif has(ALPHA_NUM, ch):
            return 208
    # pork
    elif state == 63:
        if ch == "o":
            return 64
        elif has(ALPHA_NUM, ch):
            return 202
        elif ch == EOF or has(DELIM21, ch):
            return 201
    elif state == 64:
        if ch == "r":
            return 65
        elif has(ALPHA_NUM, ch):
            return 204
        elif ch == EOF or has(DELIM21, ch):
            return 203
    elif state == 65:
        if ch == "k":
            return 66
        elif has(ALPHA_NUM, ch):
            return 206
        elif ch == EOF or has(DELIM21, ch):
            return 205
    elif state == 66:
        if ch == EOF or has(DELIM5, ch):
            return 67
        elif has(ALPHA_NUM, ch):
            return 208
    # recipe
    elif state == 68:
        if ch == "e":
            return 69
        elif has(ALPHA_NUM, ch):
            return 202
        elif ch == EOF or has(DELIM21, ch):
            return 201
    elif state == 69:
        if ch == "c":
            return 70
        elif has(ALPHA_NUM, ch):
            return 204
        elif ch == EOF or has(DELIM21, ch):
            return 203
    elif state == 70:
        if ch == "i":
            return 71
        elif has(ALPHA_NUM, ch):
            return 206
        elif ch == EOF or has(DELIM21, ch):
            return 205
    elif state == 71:
        if ch == "p":
            return 72
        elif has(ALPHA_NUM, ch):
            return 208
        elif ch == EOF or has(DELIM21, ch):
            return 207
    elif state == 72:
        if ch == "e":
            return 73
        elif has(ALPHA_NUM, ch):
            return 210
        elif ch == EOF or has(DELIM21, ch):
            return 209
    elif state == 73:
        if ch == EOF or has(WHITESPACE, ch):
            return 74
        elif has(ALPHA_NUM, ch):
            return 212
    # sauce, serve, serveback, stop, switch
    elif state == 75:
        if ch == "a":
            return 76
        elif ch == "e":
            return 81
        elif ch == "t":
            return 95
        elif ch == "w":
            return 99
        elif has(ALPHA_NUM, ch):
            return 202
        elif ch == EOF or has(DELIM21, ch):
            return 201
    elif state == 76:
        if ch == "u":
            return 77
        elif has(ALPHA_NUM, ch):
            return 204
        elif ch == EOF or has(DELIM21, ch):
            return 203
    elif state == 77:
        if ch == "c":
            return 78
        elif has(ALPHA_NUM, ch):
            return 206
        elif ch == EOF or has(DELIM21, ch):
            return 205
    elif state == 78:
        if ch == "e":
            return 79
        elif has(ALPHA_NUM, ch):
            return 208
        elif ch == EOF or has(DELIM21, ch):
            return 207
    elif state == 79:
        if ch == EOF or has(WHITESPACE, ch):
            return 80
        elif has(ALPHA_NUM, ch):
            return 210
    elif state == 81:
        if ch == "r":
            return 82
        elif has(ALPHA_NUM, ch):
            return 204
        elif ch == EOF or has(DELIM21, ch):
            return 203
    elif state == 82:
        if ch == "v":
            return 83
        elif has(ALPHA_NUM, ch):
            return 206
        elif ch == EOF or has(DELIM21, ch):
            return 205
    elif state == 83:
        if ch == "e":
            return 84
        elif has(ALPHA_NUM, ch):
            return 208
        elif ch == EOF or has(DELIM21, ch):
            return 207
    elif state == 84:
        if ch == "b":
            return 90
        elif ch == EOF or has(DELIM4, ch):
            return 85
        elif has(ALPHA_NUM, ch):
            return 210
    elif state == 86:  # alias of 81
        if ch == "r":
            return 87
        elif has(ALPHA_NUM, ch):
            return 204
        elif ch == EOF or has(DELIM21, ch):
            return 203
    elif state == 87:  # alias of 82
        if ch == "v":
            return 88
        elif has(ALPHA_NUM, ch):
            return 206
        elif ch == EOF or has(DELIM21, ch):
            return 205
    elif state == 88:  # alias of 83
        if ch == "e":
            return 89
        elif has(ALPHA_NUM, ch):
            return 208
        elif ch == EOF or has(DELIM21, ch):
            return 207
    elif state == 89:  # alias of 84
        if ch == "b":
            return 90
        elif ch == EOF or has(DELIM4, ch):
            return 85
        elif has(ALPHA_NUM, ch):
            return 210
    elif state == 90:
        if ch == "a":
            return 91
        elif has(ALPHA_NUM, ch):
            return 212
        elif ch == EOF or has(DELIM21, ch):
            return 211
    elif state == 91:
        if ch == "c":
            return 92
        elif has(ALPHA_NUM, ch):
            return 214
        elif ch == EOF or has(DELIM21, ch):
            return 213
    elif state == 92:
        if ch == "k":
            return 93
        elif has(ALPHA_NUM, ch):
            return 216
        elif ch == EOF or has(DELIM21, ch):
            return 215
    elif state == 93:
        if ch == EOF or has(WHITESPACE, ch):
            return 94
        elif has(ALPHA_NUM, ch):
            return 218
    elif state == 95:
        if ch == "o":
            return 96
        elif has(ALPHA_NUM, ch):
            return 204
        elif ch == EOF or has(DELIM21, ch):
            return 203
    elif state == 96:
        if ch == "p":
            return 97
        elif has(ALPHA_NUM, ch):
            return 206
        elif ch == EOF or has(DELIM21, ch):
            return 205
    elif state == 97:
        if ch == EOF or has(DELIM1, ch):
            return 98
        elif has(ALPHA_NUM, ch):
            return 208
    elif state == 99:
        if ch == "i":
            return 100
        elif has(ALPHA_NUM, ch):
            return 204
        elif ch == EOF or has(DELIM21, ch):
            return 203
    elif state == 100:
        if ch == "t":
            return 101
        elif has(ALPHA_NUM, ch):
            return 206
        elif ch == EOF or has(DELIM21, ch):
            return 205
    elif state == 101:
        if ch == "c":
            return 102
        elif has(ALPHA_NUM, ch):
            return 208
        elif ch == EOF or has(DELIM21, ch):
            return 207
    elif state == 102:
        if ch == "h":
            return 103
        elif has(ALPHA_NUM, ch):
            return 210
        elif ch == EOF or has(DELIM21, ch):
            return 209
    elif state == 103:
        if ch == EOF or has(DELIM4, ch):
            return 104
        elif has(ALPHA_NUM, ch):
            return 212
    # taste
    elif state == 105:
        if ch == "a":
            return 106
        elif has(ALPHA_NUM, ch):
            return 202
        elif ch == EOF or has(DELIM21, ch):
            return 201
    elif state == 106:
        if ch == "s":
            return 107
        elif has(ALPHA_NUM, ch):
            return 204
        elif ch == EOF or has(DELIM21, ch):
            return 203
    elif state == 107:
        if ch == "t":
            return 108
        elif has(ALPHA_NUM, ch):
            return 206
        elif ch == EOF or has(DELIM21, ch):
            return 205
    elif state == 108:
        if ch == "e":
            return 109
        elif has(ALPHA_NUM, ch):
            return 208
        elif ch == EOF or has(DELIM21, ch):
            return 207
    elif state == 109:
        if ch == EOF or has(DELIM4, ch):
            return 110
        elif has(ALPHA_NUM, ch):
            return 210
    # while
    elif state == 111:
        if ch == "h":
            return 112
        elif has(ALPHA_NUM, ch):
            return 202
        elif ch == EOF or has(DELIM21, ch):
            return 201
    elif state == 112:
        if ch == "i":
            return 113
        elif has(ALPHA_NUM, ch):
            return 204
        elif ch == EOF or has(DELIM21, ch):
            return 203
    elif state == 113:
        if ch == "l":
            return 114
        elif has(ALPHA_NUM, ch):
            return 206
        elif ch == EOF or has(DELIM21, ch):
            return 205
    elif state == 114:
        if ch == "e":
            return 115
        elif has(ALPHA_NUM, ch):
            return 208
        elif ch == EOF or has(DELIM21, ch):
            return 207
    elif state == 115:
        if ch == EOF or has(DELIM4, ch):
            return 116
        elif has(ALPHA_NUM, ch):
            return 210
    # yummy, yuck
    elif state == 117:
        if ch == "u":
            return 118
        elif has(ALPHA_NUM, ch):
            return 202
        elif ch == EOF or has(DELIM21, ch):
            return 201
    elif state == 118:
        if ch == "m":
            return 119
        elif ch == "c":
            return 124
        elif has(ALPHA_NUM, ch):
            return 204
        elif ch == EOF or has(DELIM21, ch):
            return 203
    elif state == 119:
        if ch == "m":
            return 120
        elif has(ALPHA_NUM, ch):
            return 206
        elif ch == EOF or has(DELIM21, ch):
            return 205
    elif state == 120:
        if ch == "y":
            return 121
        elif has(ALPHA_NUM, ch):
            return 208
        elif ch == EOF or has(DELIM21, ch):
            return 207
    elif state == 121:
        if ch == EOF or has(DELIM6, ch):
            return 122
        elif has(ALPHA_NUM, ch):
            return 210
    elif state == 123:  # alias of 118
        if ch == "m":
            return 119
        elif ch == "c":
            return 124
        elif has(ALPHA_NUM, ch):
            return 204
        elif ch == EOF or has(DELIM21, ch):
            return 203
    elif state == 124:
        if ch == "k":
            return 125
        elif has(ALPHA_NUM, ch):
            return 206
        elif ch == EOF or has(DELIM21, ch):
            return 205
    elif state == 125:
        if ch == EOF or has(DELIM6, ch):
            return 126
        elif has(ALPHA_NUM, ch):
            return 208
    return NO_TRANSITION


def symbol_transition(state, ch):
    # =, ==
    if state == 127:
        if ch == "=":
            return 129
        elif ch == EOF or has(DELIM7, ch):
            return 128
    elif state == 129:
        if ch == EOF or has(DELIM8, ch):
            return 130
    # +, ++, +=
    elif state == 131:
        if ch == "+":
            return 133
        elif ch == "=":
            return 135
        elif ch == EOF or has(DELIM9, ch):
            return 132
    elif state == 133:
        if ch == EOF or has(DELIM10, ch):
            return 134
    elif state == 135:
        if ch == EOF or has(DELIM11, ch):
            return 136
    # -, --, -=
    elif state == 137:
        if ch == "-":
            return 139
        elif ch == "=":
            return 141
        elif has(DIGITS, ch):
            return 240
        elif ch == EOF or has(DELIM11, ch):
            return 138
    elif state == 139:
        if ch == EOF or has(DELIM10, ch):
            return 140
    elif state == 141:
        if ch == EOF or has(DELIM11, ch):
            return 142
    # *, *=
    elif state == 143:
        if ch == "=":
            return 145
        elif ch == EOF or has(DELIM11, ch):
            return 144
    elif state == 145:
        if ch == EOF or has(DELIM11, ch):
            return 146
    # /, /=
    elif state == 147:
        if ch == "=":
            return 149
        elif ch == "/":
            return 294
        elif ch == "*":
            return 296
        elif ch == EOF or has(DELIM11, ch):
            return 148
    elif state == 149:
        if ch == EOF or has(DELIM11, ch):
            return 150
    # %, %=
    elif state == 151:
        if ch == "=":
            return 153
        elif ch == EOF or has(DELIM11, ch):
            return 152
    elif state == 153:
        if ch == EOF or has(DELIM11, ch):
            return 154
    # >, >=
    elif state == 155:
        if ch == "=":
            return 157
        elif ch == EOF or has(DELIM8, ch):
            return 156
    elif state == 157:
        if ch == EOF or has(DELIM8, ch):
            return 158
    # <, <=
    elif state == 159:
        if ch == "=":
            return 161
        elif ch == EOF or has(DELIM8, ch):
            return 160
    elif state == 161:
        if ch == EOF or has(DELIM8, ch):
            return 162
    # !, !=
    elif state == 163:
        if ch == "=":
            return 165
        elif ch == EOF or has(DELIM8, ch):
            return 164
    elif state == 165:
        if ch == EOF or has(DELIM8, ch):
            return 166
    # &, &&
    elif state == 167:
        if ch == "&":
            return 169
        elif ch == EOF or has(DELIM8, ch):
            return 168
    elif state == 169:
        if ch == EOF or has(DELIM8, ch):
            return 170
    # ||
    elif state == 171:
        if ch == "|":
            return 172
    elif state == 172:
        if ch == EOF or has(DELIM8, ch):
            return 173
    # { } ( ) [ ]
    elif state == 174:
        if ch == EOF or has(DELIM13, ch):
            return 175
    elif state == 176:
        if ch == EOF or has(DELIM14, ch):
            return 177
    elif state == 178:
        if ch == EOF or has(DELIM15, ch):
            return 179
    elif state == 180:
        if ch == EOF or has(DELIM16, ch):
            return 181
    elif state == 182:
        if ch == EOF or has(DELIM17, ch):
            return 183
    elif state == 184:
        if ch == EOF or has(DELIM18, ch):
            return 185
    # . , : ;
    elif state == 186:
        if ch == EOF or has(ALPHA_ID, ch):
            return 187
    elif state == 188:
        if ch == EOF or has(DELIM19, ch):
            return 189
    elif state == 190:
        if ch == EOF or has(WHITESPACE, ch):
            return 191
    elif state == 192:
        if ch == EOF or has(DELIM20, ch):
            return 193
    # space, tab, newline
    elif state == 194:
        if ch == EOF or has(DELIM25, ch):
            return 195
    elif state == 196:
        if ch == EOF or has(DELIM25, ch):
            return 197
    elif state == 198:
        if ch == EOF or has(DELIM25, ch):
            return 199
    return NO_TRANSITION


def identifier_transition(state, ch):
    # id
    if state == 200:
        if has(ALPHA_NUM, ch):
            return 202
        elif ch == EOF or has(DELIM21, ch):
            return 201
    elif state == 202:
        if has(ALPHA_NUM, ch):
            return 204
        elif ch == EOF or has(DELIM21, ch):
            return 203
    elif state == 204:
        if has(ALPHA_NUM, ch):
            return 206
        elif ch == EOF or has(DELIM21, ch):
            return 205
    elif state == 206:
        if has(ALPHA_NUM, ch):
            return 208
        elif ch == EOF or has(DELIM21, ch):
            return 207
    elif state == 208:
        if has(ALPHA_NUM, ch):
            return 210
        elif ch == EOF or has(DELIM21, ch):
            return 209
    elif state == 210:
        if has(ALPHA_NUM, ch):
            return 212
        elif ch == EOF or has(DELIM21, ch):
            return 211
    elif state == 212:
        if has(ALPHA_NUM, ch):
            return 214
        elif ch == EOF or has(DELIM21, ch):
            return 213
    elif state == 214:
        if has(ALPHA_NUM, ch):
            return 216
        elif ch == EOF or has(DELIM21, ch):
            return 215
    elif state == 216:
        if has(ALPHA_NUM, ch):
            return 218
        elif ch == EOF or has(DELIM21, ch):
            return 217
    elif state == 218:
        if has(ALPHA_NUM, ch):
            return 220
        elif ch == EOF or has(DELIM21, ch):
            return 219
    elif state == 220:
        if has(ALPHA_NUM, ch):
            return 222
        elif ch == EOF or has(DELIM21, ch):
            return 221
    elif state == 222:
        if has(ALPHA_NUM, ch):
            return 224
        elif ch == EOF or has(DELIM21, ch):
            return 223
    elif state == 224:
        if has(ALPHA_NUM, ch):
            return 226
        elif ch == EOF or has(DELIM21, ch):
            return 225
    elif state == 226:
        if has(ALPHA_NUM, ch):
            return 228
        elif ch == EOF or has(DELIM21, ch):
            return 227
    elif state == 228:
        if has(ALPHA_NUM, ch):
            return 230
        elif ch == EOF or has(DELIM21, ch):
            return 229
    elif state == 230:
        if has(ALPHA_NUM, ch):
            return 232
        elif ch == EOF or has(DELIM21, ch):
            return 231
    elif state == 232:
        if has(ALPHA_NUM, ch):
            return 234
        elif ch == EOF or has(DELIM21, ch):
            return 233
    elif state == 234:
        if has(ALPHA_NUM, ch):
            return 236
        elif ch == EOF or has(DELIM21, ch):
            return 235
    elif state == 236:
        if has(ALPHA_NUM, ch):
            return 238
        elif ch == EOF or has(DELIM21, ch):
            return 237
    elif state == 238:
        if ch == EOF or has(DELIM21, ch):
            return 239
    return NO_TRANSITION


def number_transition(state, ch):
    # meat_lit
    if state == 240:
        if has(DIGITS, ch):
            return 242
        elif ch == ".":
            return 270
        elif ch == EOF or has(DELIM22, ch):
            return 241
    elif state == 242:
        if has(DIGITS, ch):
            return 244
        elif ch == ".":
            return 270
        elif ch == EOF or has(DELIM22, ch):
            return 243
    elif state == 244:
        if has(DIGITS, ch):
            return 246
        elif ch == ".":
            return 270
        elif ch == EOF or has(DELIM22, ch):
            return 245
    elif state == 246:
        if has(DIGITS, ch):
            return 248
        elif ch == ".":
            return 270
        elif ch == EOF or has(DELIM22, ch):
            return 247
    elif state == 248:
        if has(DIGITS, ch):
            return 250
        elif ch == ".":
            return 270
        elif ch == EOF or has(DELIM22, ch):
            return 249
    elif state == 250:
        if has(DIGITS, ch):
            return 252
        elif ch == ".":
            return 270
        elif ch == EOF or has(DELIM22, ch):
            return 251
    elif state == 252:
        if has(DIGITS, ch):
            return 254
        elif ch == ".":
            return 270
        elif ch == EOF or has(DELIM22, ch):
            return 253
    elif state == 254:
        if has(DIGITS, ch):
            return 256
        elif ch == ".":
            return 270
        elif ch == EOF or has(DELIM22, ch):
            return 255
    elif state == 256:
        if has(DIGITS, ch):
            return 258
        elif ch == ".":
            return 270
        elif ch == EOF or has(DELIM22, ch):
            return 257
    elif state == 258:
        if has(DIGITS, ch):
            return 260
        elif ch == ".":
            return 270
        elif ch == EOF or has(DELIM22, ch):
            return 259
    elif state == 260:
        if has(DIGITS, ch):
            return 262
        elif ch == ".":
            return 270
        elif ch == EOF or has(DELIM22, ch):
            return 261
    elif state == 262:
        if has(DIGITS, ch):
            return 264
        elif ch == ".":
            return 270
        elif ch == EOF or has(DELIM22, ch):
            return 263
    elif state == 264:
        if has(DIGITS, ch):
            return 266
        elif ch == ".":
            return 270
        elif ch == EOF or has(DELIM22, ch):
            return 265
    elif state == 266:
        if has(DIGITS, ch):
            return 268
        elif ch == ".":
            return 270
        elif ch == EOF or has(DELIM22, ch):
            return 267
    elif state == 268:
        if ch == ".":
            return 270
        elif ch == EOF or has(DELIM22, ch):
            return 269
    # sauce_lit
    elif state == 270:
        if has(DIGITS, ch):
            return 271
    elif state == 271:
        if has(DIGITS, ch):
            return 273
        elif ch == EOF or has(DELIM22, ch):
            return 272
    elif state == 273:
        if has(DIGITS, ch):
            return 275
        elif ch == EOF or has(DELIM22, ch):
            return 274
    elif state == 275:
        if has(DIGITS, ch):
            return 277
        elif ch == EOF or has(DELIM22, ch):
            return 276
    elif state == 277:
        if has(DIGITS, ch):
            return 279
        elif ch == EOF or has(DELIM22, ch):
            return 278
    elif state == 279:
        if has(DIGITS, ch):
            return 281
        elif ch == EOF or has(DELIM22, ch):
            return 280
    elif state == 281:
        if has(DIGITS, ch):
            return 283
        elif ch == EOF or has(DELIM22, ch):
            return 282
    elif state == 283:
        if ch == EOF or has(DELIM22, ch):
            return 284
    return NO_TRANSITION


def literal_transition(state, ch):
    # chop_lit
    if state == 285:
        if ch == "\\":
            return 286
        elif has(ASCII1, ch):
            return 287
    elif state == 286:
        if has(ESCAPE_SEQ, ch):
            return 287
    elif state == 287:
        if ch == "'":
            return 288
    elif state == 288:
        if ch == EOF or has(DELIM22, ch):
            return 289
    # recipe_lit
    elif state == 290:
        if ch == "\\":
            return 291
        elif ch == '"':
            return 292
        elif has(ASCII2, ch):
            return 290
    elif state == 291:
        if has(ESCAPE_SEQ, ch):
            return 290
    elif state == 292:
        if ch == EOF or has(DELIM23, ch):
            return 293
    # Single-Line Comment
    elif state == 294:
        if ch == EOF or ch == "\n":
            return 295
        elif has(ASCII3, ch) or ch == "\t":
            return 294
    # Multi-Line Comment
    elif state == 296:
        if ch == "*":
            return 297
        elif has(ASCII4, ch) or has(WHITESPACE, ch):
            return 296
    elif state == 297:
        if ch == "/":
            return 298
        elif ch == "*":
            return 297
        elif has(ASCII4, ch) or has(WHITESPACE, ch):
            return 296
    elif state == 298:
        if ch == EOF or has(WHITESPACE, ch):
            return 299
    return NO_TRANSITION


def token_type(state):
    if state == 6:
        return "again"
    elif state == 11:
        return "case"
    elif state == 15:
        return "chop"
    elif state == 21:
        return "cooked"
    elif state == 29:
        return "default"
    elif state == 31:
        return "do"
    elif state == 36:
        return "else"
    elif state == 41:
        return "empty"
    elif state == 47:
        return "fixed"
    elif state == 50:
        return "for"
    elif state == 53:
        return "if"
    elif state == 58:
        return "meat"
    elif state == 62:
        return "menu"
    elif state == 67:
        return "pork"
    elif state == 74:
        return "recipe"
    elif state == 80:
        return "sauce"
    elif state == 85:
        return "serve"
    elif state == 94:
        return "serveback"
    elif state == 98:
        return "stop"
    elif state == 104:
        return "switch"
    elif state == 110:
        return "taste"
    elif state == 116:
        return "while"
    elif state == 122:
        return "yummy"
    elif state == 126:
        return "yuck"
    elif state == 128:
        return "="
    elif state == 130:
        return "=="
    elif state == 132:
        return "+"
    elif state == 134:
        return "++"
    elif state == 136:
        return "+="
    elif state == 138:
        return "-"
    elif state == 140:
        return "--"
    elif state == 142:
        return "-="
    elif state == 144:
        return "*"
    elif state == 146:
        return "*="
    elif state == 148:
        return "/"
    elif state == 150:
        return "/="
    elif state == 152:
        return "%"
    elif state == 154:
        return "%="
    elif state == 156:
        return ">"
    elif state == 158:
        return ">="
    elif state == 160:
        return "<"
    elif state == 162:
        return "<="
    elif state == 164:
        return "!"
    elif state == 166:
        return "!="
    elif state == 168:
        return "&"
    elif state == 170:
        return "&&"
    elif state == 173:
        return "||"
    elif state == 175:
        return "{"
    elif state == 177:
        return "}"
    elif state == 179:
        return "("
    elif state == 181:
        return ")"
    elif state == 183:
        return "["
    elif state == 185:
        return "]"
    elif state == 187:
        return "."
    elif state == 189:
        return ","
    elif state == 191:
        return ":"
    elif state == 193:
        return ";"
    elif state == 195:
        return SPACE
    elif state == 197:
        return TAB
    elif state == 199:
        return NEWLINE
    elif state == 201:
        return IDENTIFIER
    elif state == 203:
        return IDENTIFIER
    elif state == 205:
        return IDENTIFIER
    elif state == 207:
        return IDENTIFIER
    elif state == 209:
        return IDENTIFIER
    elif state == 211:
        return IDENTIFIER
    elif state == 213:
        return IDENTIFIER
    elif state == 215:
        return IDENTIFIER
    elif state == 217:
        return IDENTIFIER
    elif state == 219:
        return IDENTIFIER
    elif state == 221:
        return IDENTIFIER
    elif state == 223:
        return IDENTIFIER
    elif state == 225:
        return IDENTIFIER
    elif state == 227:
        return IDENTIFIER
    elif state == 229:
        return IDENTIFIER
    elif state == 231:
        return IDENTIFIER
    elif state == 233:
        return IDENTIFIER
    elif state == 235:
        return IDENTIFIER
    elif state == 237:
        return IDENTIFIER
    elif state == 239:
        return IDENTIFIER
    elif state == 241:
        return MEAT_LITERAL
    elif state == 243:
        return MEAT_LITERAL
    elif state == 245:
        return MEAT_LITERAL
    elif state == 247:
        return MEAT_LITERAL
    elif state == 249:
        return MEAT_LITERAL
    elif state == 251:
        return MEAT_LITERAL
    elif state == 253:
        return MEAT_LITERAL
    elif state == 255:
        return MEAT_LITERAL
    elif state == 257:
        return MEAT_LITERAL
    elif state == 259:
        return MEAT_LITERAL
    elif state == 261:
        return MEAT_LITERAL
    elif state == 263:
        return MEAT_LITERAL
    elif state == 265:
        return MEAT_LITERAL
    elif state == 267:
        return MEAT_LITERAL
    elif state == 269:
        return MEAT_LITERAL
    elif state == 272:
        return SAUCE_LITERAL
    elif state == 274:
        return SAUCE_LITERAL
    elif state == 276:
        return SAUCE_LITERAL
    elif state == 278:
        return SAUCE_LITERAL
    elif state == 280:
        return SAUCE_LITERAL
    elif state == 282:
        return SAUCE_LITERAL
    elif state == 284:
        return SAUCE_LITERAL
    elif state == 289:
        return CHOP_LITERAL
    elif state == 293:
        return RECIPE_LITERAL
    elif state == 295:
        return SINGLE_LINE_COMMENT
    elif state == 299:
        return MULTI_LINE_COMMENT
    return NOT_FINAL


def transition(state, ch):
    if state == 0:
        return start_transition(ch)
    elif state <= 126:
        return keyword_transition(state, ch)
    elif state <= 199:
        return symbol_transition(state, ch)
    elif state <= 239:
        return identifier_transition(state, ch)
    elif state <= 284:
        return number_transition(state, ch)
    else:
        return literal_transition(state, ch)


@dataclass
class Token:
    type: str
    lexeme: str
    line: int
    column: int


@dataclass
class LexicalError:
    lexeme: str
    message: str
    line: int
    column: int


class PorkCCigLexer:
    def __init__(self, source, debug=False):
        self.src = source.replace("\r\n", "\n").replace("\r", "\n")
        self.n = len(self.src)
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens = []
        self.errors = []
        self.debug = debug
        # With debug on: (lexeme, states visited) for every token and error.
        self.traces = []

    def _peek(self):
        if self.pos < self.n:
            return self.src[self.pos]
        return EOF

    def _advance(self):
        ch = self.src[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    @staticmethod
    def _message(state, ch):
        if state == 0:
            return "Unavailable character" if has(UNAVAILABLE, ch) else "Invalid character"
        elif state == 171:
            return "Invalid character"
        elif state == 238 and has(ALPHA_NUM, ch):
            return "Identifier exceeds 20 characters"
        elif 240 <= state <= 268 and has(DIGITS, ch):
            return "Meat value exceeds 15 digits"
        elif 271 <= state <= 283 and has(DIGITS, ch):
            return "Sauce decimal part exceeds 7 digits"
        elif 271 <= state <= 283 and ch == ".":
            return "Multiple decimal points"
        elif (240 <= state <= 268 or 271 <= state <= 283) and has(ALPHA_ID, ch):
            return "Invalid numerical value"
        elif state == 270:
            return "Incomplete decimal value"
        elif state == 285 and ch == "'":
            return "Empty character value"
        elif state == 287 and (has(ASCII1, ch) or ch == "\\"):
            return "Too many characters in chop value"
        elif state == 285 or state == 287:
            return "Unclosed character value"
        elif state == 286 or state == 291:
            return "Invalid escape sequence"
        elif state == 290:
            return "Unclosed string value"
        elif (state == 296 or state == 297) and ch == EOF:
            return "Unclosed comment"
        elif state == 294 or state == 296 or state == 297:
            return "Invalid character in comment"
        else:
            return "Invalid delimiter"

    def scan(self):
        state = 0
        lexeme = ""
        line, col = self.line, self.col
        path = [0]
        while self.pos < self.n or state != 0:
            ch = self._peek()
            target = transition(state, ch)
            kind = NOT_FINAL
            if target != NO_TRANSITION:
                kind = token_type(target)
            if target != NO_TRANSITION and kind == NOT_FINAL:
                lexeme += self._advance()
                state = target
                path.append(state)
                continue

            if target == NO_TRANSITION:
                message = self._message(state, ch)
                if state == 0:
                    lexeme = self._advance()
                self.errors.append(LexicalError(lexeme, message, line, col))
            else:
                self.tokens.append(Token(kind, lexeme, line, col))
                path.append(target)
            if self.debug:
                self.traces.append((lexeme, path))
            state = 0
            lexeme = ""
            line, col = self.line, self.col
            path = [0]
        return self.tokens, self.errors


def tokenize(source):
    return PorkCCigLexer(source).scan()


def lex(source):
    return tokenize(source)


if __name__ == "__main__":
    def show(title, source):
        lexer = PorkCCigLexer(source, debug=True)
        tokens, errors = lexer.scan()
        print("== %s ==" % title)
        print(source)
        print("-- tokens (whitespace not shown) --")
        for token in tokens:
            if token.type != SPACE and token.type != TAB and token.type != NEWLINE:
                print("  %2d:%-3d %-20s %r" % (token.line, token.column, token.type, token.lexeme))
        print("-- %d error(s) --" % len(errors))
        for error in errors:
            print("  Line %d, Col %d: %s %r" % (error.line, error.column, error.message, error.lexeme))
        print("-- states visited by the first lexeme --")
        print("  %r: %s" % (lexer.traces[0][0], " -> ".join(str(s) for s in lexer.traces[0][1])))
        print()

    show("Valid program", (
        "serveback 0;\n"
        "// main program\n"
        "empty pork() {\n"
        "    meat servings = -5, meatball = 10;\n"
        "    sauce price = 150.50;\n"
        "    chop grade = 'A';\n"
        "    cooked ready = yummy;\n"
        "    /* loop\n"
        "       over orders */\n"
        "    while(servings <= meatball && ready) {\n"
        "        serve(\"Price: &f\\n\", price - 1);\n"
        "        servings++;\n"
        "    }\n"
        "}\n"
    ))

    show("Error recovery", (
        "meat; x = 12abc;\n"
        "sauce s = 1.12345678 + 5.;\n"
        "chop c = 'ab'; recipe r = \"unclosed\n"
        "a $ b | c;\n"
        "meat this_identifier_is_too_long = 1234567890123456;\n"
    ))
