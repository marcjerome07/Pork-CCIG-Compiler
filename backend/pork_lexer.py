"""Pork CCig lexical analyzer: one table-driven DFA, states 0-299.

    tokens, errors = tokenize(source)

Run this file directly for a demonstration:

    py backend/pork_lexer.py
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

# Character classes
WHITESPACE = set(" \t\n")
DIGITS = set("0123456789")
LOWERCASE = set("abcdefghijklmnopqrstuvwxyz")
UPPERCASE = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
ALPHA = LOWERCASE | UPPERCASE
ALPHA_ID = ALPHA | {"_"}
ALPHA_NUM = DIGITS | ALPHA_ID
OPERATORS = set("+-*/%<>=!&|")
UNAVAILABLE = set("$?@^")
PRINTABLE = {chr(code) for code in range(32, 127)}

DELIMS = {
    "whitespace": WHITESPACE,
    "digits": DIGITS,
    "alpha_id": ALPHA_ID,
    "alpha_num": ALPHA_NUM,
    "escape_seq": set("nt'\"\\0"),
    "ascii1": PRINTABLE - {"\\", "'"},
    "ascii2": PRINTABLE - {"\\", '"'},
    "ascii3": PRINTABLE,
    "ascii4": PRINTABLE - {" "},
    "delim1": {";"} | WHITESPACE,
    "delim2": {":"} | WHITESPACE,
    "delim3": {"{"} | WHITESPACE,
    "delim4": {"("} | WHITESPACE,
    "delim5": set(",({;") | WHITESPACE,
    "delim6": OPERATORS | set("})]:;,") | WHITESPACE,
    "delim7": ALPHA_NUM | set("+-!{('\"") | WHITESPACE,
    "delim8": ALPHA_NUM | set("+-!('\"") | WHITESPACE,
    "delim9": ALPHA_NUM | set("-!('\"") | WHITESPACE,
    "delim10": ALPHA_ID | set("()],;") | WHITESPACE,
    "delim11": ALPHA_NUM | set("+-!(") | WHITESPACE,
    "delim13": ALPHA_NUM | set("+-!{(/'\"") | WHITESPACE,
    "delim14": ALPHA_ID | set("};,") | WHITESPACE,
    "delim15": ALPHA_NUM | set("-+!()'\"") | WHITESPACE,
    "delim16": OPERATORS | set("{)[].,:;") | WHITESPACE,
    "delim17": ALPHA_NUM | set("+-!(]'\"") | WHITESPACE,
    "delim18": OPERATORS | set(")[],;") | WHITESPACE,
    "delim19": ALPHA_NUM | set("{+-&'\"") | WHITESPACE,
    "delim20": ALPHA_NUM | set("}+-") | WHITESPACE,
    "delim21": OPERATORS | set("()[].,;") | WHITESPACE,
    "delim22": OPERATORS | set(")]},:;") | WHITESPACE,
    "delim23": OPERATORS | set("):]},;") | WHITESPACE,
    "delim25": ALPHA_NUM | OPERATORS | set("{}()[]:;,'\"") | WHITESPACE,
}
ASCII3_OR_TAB = DELIMS["ascii3"] | {"\t"}
ASCII4_OR_WHITESPACE = DELIMS["ascii4"] | WHITESPACE

# Token types after which a "-" subtracts instead of signing a literal.
OPERAND_END = {IDENTIFIER, MEAT_LITERAL, SAUCE_LITERAL, CHOP_LITERAL, ")", "]"}
SKIPPED = {SPACE, TAB, NEWLINE, SINGLE_LINE_COMMENT, MULTI_LINE_COMMENT}


class TransitionState:
    def __init__(self, chars, branches=None, is_terminal=False):
        # chars: the input that enters this state. branches: next states, tried in order.
        self.chars = chars
        self.branches = branches or []
        self.is_terminal = is_terminal


TRANSITIONS = {
    0: TransitionState("initial", [
        1, 7, 22, 32, 42, 51, 54, 63, 68, 75, 105, 111, 117, 200,
        240, 127, 131, 137, 143, 147, 151, 155, 159, 163, 167, 171, 174, 176,
        178, 180, 182, 184, 186, 188, 190, 192, 194, 196, 198, 285, 290,
    ]),

    # again
    1: TransitionState("a", [2, 202, 201]),
    2: TransitionState("g", [3, 204, 203]),
    3: TransitionState("a", [4, 206, 205]),
    4: TransitionState("i", [5, 208, 207]),
    5: TransitionState("n", [6, 210]),
    6: TransitionState(DELIMS["delim1"], is_terminal=True),

    # case, chop, cooked
    7: TransitionState("c", [8, 12, 16, 202, 201]),
    8: TransitionState("a", [9, 204, 203]),
    9: TransitionState("s", [10, 206, 205]),
    10: TransitionState("e", [11, 208]),
    11: TransitionState(DELIMS["delim2"], is_terminal=True),
    12: TransitionState("h", [13, 204, 203]),
    13: TransitionState("o", [14, 206, 205]),
    14: TransitionState("p", [15, 208]),
    15: TransitionState(DELIMS["whitespace"], is_terminal=True),
    16: TransitionState("o", [17, 204, 203]),
    17: TransitionState("o", [18, 206, 205]),
    18: TransitionState("k", [19, 208, 207]),
    19: TransitionState("e", [20, 210, 209]),
    20: TransitionState("d", [21, 212]),
    21: TransitionState(DELIMS["whitespace"], is_terminal=True),

    # default, do
    22: TransitionState("d", [23, 30, 202, 201]),
    23: TransitionState("e", [24, 204, 203]),
    24: TransitionState("f", [25, 206, 205]),
    25: TransitionState("a", [26, 208, 207]),
    26: TransitionState("u", [27, 210, 209]),
    27: TransitionState("l", [28, 212, 211]),
    28: TransitionState("t", [29, 214]),
    29: TransitionState(DELIMS["delim2"], is_terminal=True),
    30: TransitionState("o", [31, 204]),
    31: TransitionState(DELIMS["delim3"], is_terminal=True),

    # else, empty
    32: TransitionState("e", [33, 37, 202, 201]),
    33: TransitionState("l", [34, 204, 203]),
    34: TransitionState("s", [35, 206, 205]),
    35: TransitionState("e", [36, 208]),
    36: TransitionState(DELIMS["delim3"], is_terminal=True),
    37: TransitionState("m", [38, 204, 203]),
    38: TransitionState("p", [39, 206, 205]),
    39: TransitionState("t", [40, 208, 207]),
    40: TransitionState("y", [41, 210]),
    41: TransitionState(DELIMS["whitespace"], is_terminal=True),

    # fixed, for
    42: TransitionState("f", [43, 48, 202, 201]),
    43: TransitionState("i", [44, 204, 203]),
    44: TransitionState("x", [45, 206, 205]),
    45: TransitionState("e", [46, 208, 207]),
    46: TransitionState("d", [47, 210]),
    47: TransitionState(DELIMS["whitespace"], is_terminal=True),
    48: TransitionState("o", [49, 204, 203]),
    49: TransitionState("r", [50, 206]),
    50: TransitionState(DELIMS["delim4"], is_terminal=True),

    # if
    51: TransitionState("i", [52, 202, 201]),
    52: TransitionState("f", [53, 204]),
    53: TransitionState(DELIMS["delim4"], is_terminal=True),

    # meat, menu
    54: TransitionState("m", [55, 202, 201]),
    55: TransitionState("e", [56, 60, 204, 203]),
    56: TransitionState("a", [57, 206, 205]),
    57: TransitionState("t", [58, 208]),
    58: TransitionState(DELIMS["whitespace"], is_terminal=True),
    59: TransitionState("e", [56, 60, 204, 203]),  # alias of 55
    60: TransitionState("n", [61, 206, 205]),
    61: TransitionState("u", [62, 208]),
    62: TransitionState(DELIMS["whitespace"], is_terminal=True),

    # pork
    63: TransitionState("p", [64, 202, 201]),
    64: TransitionState("o", [65, 204, 203]),
    65: TransitionState("r", [66, 206, 205]),
    66: TransitionState("k", [67, 208]),
    67: TransitionState(DELIMS["delim5"], is_terminal=True),

    # recipe
    68: TransitionState("r", [69, 202, 201]),
    69: TransitionState("e", [70, 204, 203]),
    70: TransitionState("c", [71, 206, 205]),
    71: TransitionState("i", [72, 208, 207]),
    72: TransitionState("p", [73, 210, 209]),
    73: TransitionState("e", [74, 212]),
    74: TransitionState(DELIMS["whitespace"], is_terminal=True),

    # sauce, serve, serveback, stop, switch
    75: TransitionState("s", [76, 81, 95, 99, 202, 201]),
    76: TransitionState("a", [77, 204, 203]),
    77: TransitionState("u", [78, 206, 205]),
    78: TransitionState("c", [79, 208, 207]),
    79: TransitionState("e", [80, 210]),
    80: TransitionState(DELIMS["whitespace"], is_terminal=True),
    81: TransitionState("e", [82, 204, 203]),
    82: TransitionState("r", [83, 206, 205]),
    83: TransitionState("v", [84, 208, 207]),
    84: TransitionState("e", [90, 85, 210]),
    85: TransitionState(DELIMS["delim4"], is_terminal=True),
    86: TransitionState("e", [87, 204, 203]),  # alias of 81
    87: TransitionState("r", [88, 206, 205]),  # alias of 82
    88: TransitionState("v", [89, 208, 207]),  # alias of 83
    89: TransitionState("e", [90, 85, 210]),  # alias of 84
    90: TransitionState("b", [91, 212, 211]),
    91: TransitionState("a", [92, 214, 213]),
    92: TransitionState("c", [93, 216, 215]),
    93: TransitionState("k", [94, 218]),
    94: TransitionState(DELIMS["whitespace"], is_terminal=True),
    95: TransitionState("t", [96, 204, 203]),
    96: TransitionState("o", [97, 206, 205]),
    97: TransitionState("p", [98, 208]),
    98: TransitionState(DELIMS["delim1"], is_terminal=True),
    99: TransitionState("w", [100, 204, 203]),
    100: TransitionState("i", [101, 206, 205]),
    101: TransitionState("t", [102, 208, 207]),
    102: TransitionState("c", [103, 210, 209]),
    103: TransitionState("h", [104, 212]),
    104: TransitionState(DELIMS["delim4"], is_terminal=True),

    # taste
    105: TransitionState("t", [106, 202, 201]),
    106: TransitionState("a", [107, 204, 203]),
    107: TransitionState("s", [108, 206, 205]),
    108: TransitionState("t", [109, 208, 207]),
    109: TransitionState("e", [110, 210]),
    110: TransitionState(DELIMS["delim4"], is_terminal=True),

    # while
    111: TransitionState("w", [112, 202, 201]),
    112: TransitionState("h", [113, 204, 203]),
    113: TransitionState("i", [114, 206, 205]),
    114: TransitionState("l", [115, 208, 207]),
    115: TransitionState("e", [116, 210]),
    116: TransitionState(DELIMS["delim4"], is_terminal=True),

    # yummy, yuck
    117: TransitionState("y", [118, 202, 201]),
    118: TransitionState("u", [119, 124, 204, 203]),
    119: TransitionState("m", [120, 206, 205]),
    120: TransitionState("m", [121, 208, 207]),
    121: TransitionState("y", [122, 210]),
    122: TransitionState(DELIMS["delim6"], is_terminal=True),
    123: TransitionState("u", [119, 124, 204, 203]),  # alias of 118
    124: TransitionState("c", [125, 206, 205]),
    125: TransitionState("k", [126, 208]),
    126: TransitionState(DELIMS["delim6"], is_terminal=True),

    # =, ==
    127: TransitionState("=", [129, 128]),
    128: TransitionState(DELIMS["delim7"], is_terminal=True),
    129: TransitionState("=", [130]),
    130: TransitionState(DELIMS["delim8"], is_terminal=True),

    # +, ++, +=
    131: TransitionState("+", [133, 135, 132]),
    132: TransitionState(DELIMS["delim9"], is_terminal=True),
    133: TransitionState("+", [134]),
    134: TransitionState(DELIMS["delim10"], is_terminal=True),
    135: TransitionState("=", [136]),
    136: TransitionState(DELIMS["delim11"], is_terminal=True),

    # -, --, -=
    137: TransitionState("-", [139, 141, 240, 138]),
    138: TransitionState(DELIMS["delim11"], is_terminal=True),
    139: TransitionState("-", [140]),
    140: TransitionState(DELIMS["delim10"], is_terminal=True),
    141: TransitionState("=", [142]),
    142: TransitionState(DELIMS["delim11"], is_terminal=True),

    # *, *=
    143: TransitionState("*", [145, 144]),
    144: TransitionState(DELIMS["delim11"], is_terminal=True),
    145: TransitionState("=", [146]),
    146: TransitionState(DELIMS["delim11"], is_terminal=True),

    # /, /=
    147: TransitionState("/", [149, 294, 296, 148]),
    148: TransitionState(DELIMS["delim11"], is_terminal=True),
    149: TransitionState("=", [150]),
    150: TransitionState(DELIMS["delim11"], is_terminal=True),

    # %, %=
    151: TransitionState("%", [153, 152]),
    152: TransitionState(DELIMS["delim11"], is_terminal=True),
    153: TransitionState("=", [154]),
    154: TransitionState(DELIMS["delim11"], is_terminal=True),

    # >, >=
    155: TransitionState(">", [157, 156]),
    156: TransitionState(DELIMS["delim8"], is_terminal=True),
    157: TransitionState("=", [158]),
    158: TransitionState(DELIMS["delim8"], is_terminal=True),

    # <, <=
    159: TransitionState("<", [161, 160]),
    160: TransitionState(DELIMS["delim8"], is_terminal=True),
    161: TransitionState("=", [162]),
    162: TransitionState(DELIMS["delim8"], is_terminal=True),

    # !, !=
    163: TransitionState("!", [165, 164]),
    164: TransitionState(DELIMS["delim8"], is_terminal=True),
    165: TransitionState("=", [166]),
    166: TransitionState(DELIMS["delim8"], is_terminal=True),

    # &, &&
    167: TransitionState("&", [169, 168]),
    168: TransitionState(DELIMS["delim8"], is_terminal=True),
    169: TransitionState("&", [170]),
    170: TransitionState(DELIMS["delim8"], is_terminal=True),

    # ||
    171: TransitionState("|", [172]),
    172: TransitionState("|", [173]),
    173: TransitionState(DELIMS["delim8"], is_terminal=True),

    # { } ( ) [ ]
    174: TransitionState("{", [175]),
    175: TransitionState(DELIMS["delim13"], is_terminal=True),
    176: TransitionState("}", [177]),
    177: TransitionState(DELIMS["delim14"], is_terminal=True),
    178: TransitionState("(", [179]),
    179: TransitionState(DELIMS["delim15"], is_terminal=True),
    180: TransitionState(")", [181]),
    181: TransitionState(DELIMS["delim16"], is_terminal=True),
    182: TransitionState("[", [183]),
    183: TransitionState(DELIMS["delim17"], is_terminal=True),
    184: TransitionState("]", [185]),
    185: TransitionState(DELIMS["delim18"], is_terminal=True),

    # . , : ;
    186: TransitionState(".", [187]),
    187: TransitionState(DELIMS["alpha_id"], is_terminal=True),
    188: TransitionState(",", [189]),
    189: TransitionState(DELIMS["delim19"], is_terminal=True),
    190: TransitionState(":", [191]),
    191: TransitionState(DELIMS["whitespace"], is_terminal=True),
    192: TransitionState(";", [193]),
    193: TransitionState(DELIMS["delim20"], is_terminal=True),

    # space, tab, newline
    194: TransitionState(" ", [195]),
    195: TransitionState(DELIMS["delim25"], is_terminal=True),
    196: TransitionState("\t", [197]),
    197: TransitionState(DELIMS["delim25"], is_terminal=True),
    198: TransitionState("\n", [199]),
    199: TransitionState(DELIMS["delim25"], is_terminal=True),

    # id
    200: TransitionState(DELIMS["alpha_id"], [202, 201]),
    201: TransitionState(DELIMS["delim21"], is_terminal=True),
    202: TransitionState(DELIMS["alpha_num"], [204, 203]),
    203: TransitionState(DELIMS["delim21"], is_terminal=True),
    204: TransitionState(DELIMS["alpha_num"], [206, 205]),
    205: TransitionState(DELIMS["delim21"], is_terminal=True),
    206: TransitionState(DELIMS["alpha_num"], [208, 207]),
    207: TransitionState(DELIMS["delim21"], is_terminal=True),
    208: TransitionState(DELIMS["alpha_num"], [210, 209]),
    209: TransitionState(DELIMS["delim21"], is_terminal=True),
    210: TransitionState(DELIMS["alpha_num"], [212, 211]),
    211: TransitionState(DELIMS["delim21"], is_terminal=True),
    212: TransitionState(DELIMS["alpha_num"], [214, 213]),
    213: TransitionState(DELIMS["delim21"], is_terminal=True),
    214: TransitionState(DELIMS["alpha_num"], [216, 215]),
    215: TransitionState(DELIMS["delim21"], is_terminal=True),
    216: TransitionState(DELIMS["alpha_num"], [218, 217]),
    217: TransitionState(DELIMS["delim21"], is_terminal=True),
    218: TransitionState(DELIMS["alpha_num"], [220, 219]),
    219: TransitionState(DELIMS["delim21"], is_terminal=True),
    220: TransitionState(DELIMS["alpha_num"], [222, 221]),
    221: TransitionState(DELIMS["delim21"], is_terminal=True),
    222: TransitionState(DELIMS["alpha_num"], [224, 223]),
    223: TransitionState(DELIMS["delim21"], is_terminal=True),
    224: TransitionState(DELIMS["alpha_num"], [226, 225]),
    225: TransitionState(DELIMS["delim21"], is_terminal=True),
    226: TransitionState(DELIMS["alpha_num"], [228, 227]),
    227: TransitionState(DELIMS["delim21"], is_terminal=True),
    228: TransitionState(DELIMS["alpha_num"], [230, 229]),
    229: TransitionState(DELIMS["delim21"], is_terminal=True),
    230: TransitionState(DELIMS["alpha_num"], [232, 231]),
    231: TransitionState(DELIMS["delim21"], is_terminal=True),
    232: TransitionState(DELIMS["alpha_num"], [234, 233]),
    233: TransitionState(DELIMS["delim21"], is_terminal=True),
    234: TransitionState(DELIMS["alpha_num"], [236, 235]),
    235: TransitionState(DELIMS["delim21"], is_terminal=True),
    236: TransitionState(DELIMS["alpha_num"], [238, 237]),
    237: TransitionState(DELIMS["delim21"], is_terminal=True),
    238: TransitionState(DELIMS["alpha_num"], [239]),
    239: TransitionState(DELIMS["delim21"], is_terminal=True),

    # meat_lit
    240: TransitionState(DELIMS["digits"], [242, 270, 241]),
    241: TransitionState(DELIMS["delim22"], is_terminal=True),
    242: TransitionState(DELIMS["digits"], [244, 270, 243]),
    243: TransitionState(DELIMS["delim22"], is_terminal=True),
    244: TransitionState(DELIMS["digits"], [246, 270, 245]),
    245: TransitionState(DELIMS["delim22"], is_terminal=True),
    246: TransitionState(DELIMS["digits"], [248, 270, 247]),
    247: TransitionState(DELIMS["delim22"], is_terminal=True),
    248: TransitionState(DELIMS["digits"], [250, 270, 249]),
    249: TransitionState(DELIMS["delim22"], is_terminal=True),
    250: TransitionState(DELIMS["digits"], [252, 270, 251]),
    251: TransitionState(DELIMS["delim22"], is_terminal=True),
    252: TransitionState(DELIMS["digits"], [254, 270, 253]),
    253: TransitionState(DELIMS["delim22"], is_terminal=True),
    254: TransitionState(DELIMS["digits"], [256, 270, 255]),
    255: TransitionState(DELIMS["delim22"], is_terminal=True),
    256: TransitionState(DELIMS["digits"], [258, 270, 257]),
    257: TransitionState(DELIMS["delim22"], is_terminal=True),
    258: TransitionState(DELIMS["digits"], [260, 270, 259]),
    259: TransitionState(DELIMS["delim22"], is_terminal=True),
    260: TransitionState(DELIMS["digits"], [262, 270, 261]),
    261: TransitionState(DELIMS["delim22"], is_terminal=True),
    262: TransitionState(DELIMS["digits"], [264, 270, 263]),
    263: TransitionState(DELIMS["delim22"], is_terminal=True),
    264: TransitionState(DELIMS["digits"], [266, 270, 265]),
    265: TransitionState(DELIMS["delim22"], is_terminal=True),
    266: TransitionState(DELIMS["digits"], [268, 270, 267]),
    267: TransitionState(DELIMS["delim22"], is_terminal=True),
    268: TransitionState(DELIMS["digits"], [270, 269]),
    269: TransitionState(DELIMS["delim22"], is_terminal=True),

    # sauce_lit
    270: TransitionState(".", [271]),
    271: TransitionState(DELIMS["digits"], [273, 272]),
    272: TransitionState(DELIMS["delim22"], is_terminal=True),
    273: TransitionState(DELIMS["digits"], [275, 274]),
    274: TransitionState(DELIMS["delim22"], is_terminal=True),
    275: TransitionState(DELIMS["digits"], [277, 276]),
    276: TransitionState(DELIMS["delim22"], is_terminal=True),
    277: TransitionState(DELIMS["digits"], [279, 278]),
    278: TransitionState(DELIMS["delim22"], is_terminal=True),
    279: TransitionState(DELIMS["digits"], [281, 280]),
    280: TransitionState(DELIMS["delim22"], is_terminal=True),
    281: TransitionState(DELIMS["digits"], [283, 282]),
    282: TransitionState(DELIMS["delim22"], is_terminal=True),
    283: TransitionState(DELIMS["digits"], [284]),
    284: TransitionState(DELIMS["delim22"], is_terminal=True),

    # chop_lit
    285: TransitionState("'", [286, 287]),
    286: TransitionState("\\", [(DELIMS["escape_seq"], 287)]),
    287: TransitionState(DELIMS["ascii1"], [288]),
    288: TransitionState("'", [289]),
    289: TransitionState(DELIMS["delim22"], is_terminal=True),

    # recipe_lit
    290: TransitionState('"', [291, 292, (DELIMS["ascii2"], 290)]),
    291: TransitionState("\\", [(DELIMS["escape_seq"], 290)]),
    292: TransitionState('"', [293]),
    293: TransitionState(DELIMS["delim23"], is_terminal=True),

    # Single-Line Comment
    294: TransitionState("/", [295, (ASCII3_OR_TAB, 294)]),
    295: TransitionState("\n", is_terminal=True),

    # Multi-Line Comment
    296: TransitionState("*", [297, (ASCII4_OR_WHITESPACE, 296)]),
    297: TransitionState("*", [298, 297, (ASCII4_OR_WHITESPACE, 296)]),
    298: TransitionState("/", [299]),
    299: TransitionState(DELIMS["whitespace"], is_terminal=True),
}

ACCEPTING = {
    6: "again", 11: "case", 15: "chop", 21: "cooked", 29: "default", 31: "do",
    36: "else", 41: "empty", 47: "fixed", 50: "for", 53: "if", 58: "meat",
    62: "menu", 67: "pork", 74: "recipe", 80: "sauce", 85: "serve",
    94: "serveback", 98: "stop", 104: "switch", 110: "taste", 116: "while",
    122: "yummy", 126: "yuck",
    128: "=", 130: "==", 132: "+", 134: "++", 136: "+=", 138: "-", 140: "--",
    142: "-=", 144: "*", 146: "*=", 148: "/", 150: "/=", 152: "%", 154: "%=",
    156: ">", 158: ">=", 160: "<", 162: "<=", 164: "!", 166: "!=", 168: "&",
    170: "&&", 173: "||", 175: "{", 177: "}", 179: "(", 181: ")", 183: "[",
    185: "]", 187: ".", 189: ",", 191: ":", 193: ";",
    195: SPACE, 197: TAB, 199: NEWLINE,
    272: SAUCE_LITERAL, 274: SAUCE_LITERAL, 276: SAUCE_LITERAL, 278: SAUCE_LITERAL,
    280: SAUCE_LITERAL, 282: SAUCE_LITERAL, 284: SAUCE_LITERAL,
    289: CHOP_LITERAL, 293: RECIPE_LITERAL,
    295: SINGLE_LINE_COMMENT, 299: MULTI_LINE_COMMENT,
}
for state in range(201, 240, 2):
    ACCEPTING[state] = IDENTIFIER
for state in range(241, 270, 2):
    ACCEPTING[state] = MEAT_LITERAL


@dataclass
class Token:
    type: str
    lexeme: str
    line: int
    column: int

    def to_dict(self):
        return {"type": self.type, "lexeme": self.lexeme, "line": self.line, "column": self.column}


@dataclass
class LexicalError:
    lexeme: str
    message: str
    line: int
    column: int

    def to_dict(self):
        return {"lexeme": self.lexeme, "message": self.message, "line": self.line, "column": self.column}


class PorkCCigLexer:
    def __init__(self, source, debug=False):
        self.src = source.replace("\r\n", "\n").replace("\r", "\n")
        self.n = len(self.src)
        self.pos = 0
        self.line = 1
        self.col = 1
        # Type of the last token, whitespace and comments skipped; "" after an error.
        self.lookback = ""
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
            return "Unavailable character" if ch in UNAVAILABLE else "Invalid character"
        elif state == 171:
            return "Invalid character"
        elif state == 238 and ch in ALPHA_NUM:
            return "Identifier exceeds 20 characters"
        elif 240 <= state <= 268 and ch in DIGITS:
            return "Meat value exceeds 15 digits"
        elif 271 <= state <= 283 and ch in DIGITS:
            return "Sauce decimal part exceeds 7 digits"
        elif 271 <= state <= 283 and ch == ".":
            return "Multiple decimal points"
        elif (240 <= state <= 268 or 271 <= state <= 283) and ch in ALPHA_ID:
            return "Invalid numerical value"
        elif state == 270:
            return "Incomplete decimal value"
        elif state == 285 and ch == "'":
            return "Empty character value"
        elif state == 287 and (ch in DELIMS["ascii1"] or ch == "\\"):
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
            target = None
            for branch in TRANSITIONS[state].branches:
                if isinstance(branch, tuple):
                    chars, following = branch
                else:
                    chars, following = TRANSITIONS[branch].chars, branch
                if TRANSITIONS[following].is_terminal if ch == EOF else ch in chars:
                    target = following
                    break
            if state == 137 and ch in DIGITS and self.lookback in OPERAND_END:
                target = 138
            if target is not None and not TRANSITIONS[target].is_terminal:
                lexeme += self._advance()
                state = target
                path.append(state)
                continue

            if target is None:
                message = self._message(state, ch)
                if state == 0:
                    lexeme = self._advance()
                self.errors.append(LexicalError(lexeme, message, line, col))
                self.lookback = ""
            else:
                self.tokens.append(Token(ACCEPTING[target], lexeme, line, col))
                path.append(target)
                if ACCEPTING[target] not in SKIPPED:
                    self.lookback = ACCEPTING[target]
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
        print(f"== {title} ==")
        print(source)
        print("-- tokens (whitespace not shown) --")
        for token in tokens:
            if token.type != SPACE and token.type != TAB and token.type != NEWLINE:
                print(f"  {token.line:>2}:{token.column:<3} {token.type:<20} {token.lexeme!r}")
        print(f"-- {len(errors)} error(s) --")
        for error in errors:
            print(f"  Line {error.line}, Col {error.column}: {error.message} {error.lexeme!r}")
        print("-- states visited by the first lexeme --")
        print(f"  {lexer.traces[0][0]!r}: {' -> '.join(str(s) for s in lexer.traces[0][1])}")
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
