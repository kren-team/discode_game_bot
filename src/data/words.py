import random

from wordfreq import zipf_frequency

WORDS: list[str] = [
    "ABOUT", "ABOVE", "ABUSE", "ACTOR", "ACUTE", "ADMIT", "ADOPT", "ADULT",
    "AFTER", "AGAIN", "AGENT", "AGREE", "AHEAD", "ALARM", "ALBUM", "ALERT",
    "ALIKE", "ALIVE", "ALLEY", "ALLOW", "ALONE", "ALONG", "ALTER", "ANGEL",
    "ANGER", "ANGLE", "ANKLE", "APART", "APPLE", "APPLY", "ARENA", "ARGUE",
    "ARISE", "ARMOR", "AROMA", "ARRAY", "ASIDE", "ASSET", "ATTIC", "AUDIO",
    "AUDIT", "AVOID", "AWAKE", "AWARD", "AWARE", "AWFUL", "BACON", "BASIC",
    "BASIS", "BATCH", "BEACH", "BEARD", "BEAST", "BEGIN", "BEING", "BELOW",
    "BENCH", "BERRY", "BIRTH", "BLAND", "BLANK", "BLAST", "BLAZE", "BLEED",
    "BLEND", "BLESS", "BLIND", "BLOCK", "BLOOD", "BLOWN", "BOARD", "BONUS",
    "BOOST", "BOUND", "BRACE", "BRAIN", "BRAND", "BRAVE", "BREAD", "BREAK",
    "BREED", "BRICK", "BRIEF", "BRING", "BROKE", "BROOK", "BROWN", "BUILD",
    "BUILT", "BURST", "BUYER", "CABIN", "CANDY", "CARGO", "CARRY", "CATCH",
    "CAUSE", "CEASE", "CHAIR", "CHAOS", "CHARM", "CHART", "CHASE", "CHEAP",
    "CHECK", "CHEEK", "CHEER", "CHEST", "CHIEF", "CHILD", "CHINA", "CHUNK",
    "CIVIC", "CIVIL", "CLAIM", "CLASS", "CLEAN", "CLEAR", "CLIFF", "CLIMB",
    "CLING", "CLOCK", "CLONE", "CLOSE", "CLOUD", "COACH", "COAST", "COLOR",
    "CORAL", "COUNT", "COURT", "COVER", "CRACK", "CRAFT", "CRANE", "CRASH",
    "CRAZY", "CREAM", "CREEK", "CRIME", "CROSS", "CROWD", "CRUEL", "CRUSH",
    "CURVE", "CYCLE", "DAILY", "DANCE", "DEATH", "DEBUT", "DEPTH", "DIRTY",
    "DODGE", "DOUBT", "DOUGH", "DRAFT", "DRAIN", "DRAMA", "DRAWN", "DREAM",
    "DRESS", "DRIFT", "DRINK", "DRIVE", "DROVE", "DYING", "EAGER", "EARLY",
    "EARTH", "EIGHT", "ELECT", "ELITE", "EMPTY", "ENJOY", "ENTER", "ENTRY",
    "EQUAL", "ERROR", "ESSAY", "EVERY", "EXACT", "EXIST", "EXTRA", "FAINT",
    "FAIRY", "FAITH", "FANCY", "FATAL", "FAULT", "FAVOR", "FEAST", "FENCE",
    "FEVER", "FIELD", "FIFTH", "FIFTY", "FIGHT", "FINAL", "FIRST", "FIXED",
    "FLAME", "FLASH", "FLEET", "FLESH", "FLOAT", "FLOOD", "FLOOR", "FORCE",
    "FORGE", "FORUM", "FOUND", "FRAME", "FRANK", "FRAUD", "FRESH", "FRONT",
    "FULLY", "FUNNY", "GHOST", "GIVEN", "GLEAM", "GLOBE", "GLORY", "GLOVE",
    "GRACE", "GRADE", "GRAIN", "GRAND", "GRANT", "GRAPE", "GRASP", "GRASS",
    "GRAVE", "GREAT", "GREEN", "GRIEF", "GRILL", "GRIND", "GROAN", "GROUP",
    "GROVE", "GROWN", "GUARD", "GUEST", "GUIDE", "GUILD", "GUILT", "GUSTO",
    "HABIT", "HAPPY", "HARSH", "HEART", "HEAVY", "HONOR", "HORSE", "HOTEL",
    "HOUSE", "HUMAN", "HUMOR", "IDEAL", "IMAGE", "INDEX", "INNER", "INPUT",
    "ISSUE", "JUDGE", "JUICE", "JUICY", "KNIFE", "KNOCK", "KNOWN", "LARGE",
    "LASER", "LATCH", "LATER", "LAUGH", "LAYER", "LEARN", "LEASE", "LEAST",
    "LEGAL", "LEMON", "LEVEL", "LIGHT", "LIMIT", "LINEN", "LIVER", "LOCAL",
    "LOGIC", "LOOSE", "LOWER", "LUCKY", "MAGIC", "MAJOR", "MAKER", "MANOR",
    "MARCH", "MARRY", "MATCH", "MAYOR", "MEDAL", "MEDIA", "MERCY", "MERIT",
    "METAL", "MIGHT", "MINOR", "MODEL", "MONEY", "MONTH", "MORAL", "MOTOR",
    "MOUNT", "MOUSE", "MOVIE", "MUSIC", "NAIVE", "NERVE", "NEVER", "NIGHT",
    "NOBLE", "NOISE", "NORTH", "NOTED", "NOVEL", "NURSE", "OCCUR", "OCEAN",
    "OFFER", "OFTEN", "ORDER", "OTHER", "OUTER", "OWNED", "OWNER", "OZONE",
    "PAINT", "PANEL", "PANIC", "PAPER", "PARTY", "PASTA", "PATCH", "PAUSE",
    "PEACE", "PHONE", "PHOTO", "PILOT", "PIZZA", "PLACE", "PLAIN", "PLANE",
    "PLANT", "PLATE", "PLAZA", "POINT", "POKER", "POWER", "PRESS", "PRICE",
    "PRIDE", "PRIME", "PRINT", "PRIOR", "PRIZE", "PROBE", "PROOF", "PROSE",
    "PROUD", "PROVE", "QUEEN", "QUERY", "QUEST", "QUICK", "QUIET", "QUOTA",
    "QUOTE", "RADAR", "RADIO", "RAISE", "RALLY", "RANCH", "RANGE", "RAPID",
    "RATIO", "REACH", "REACT", "READY", "REALM", "REFER", "REIGN", "RELAX",
    "REPLY", "RIDER", "RIDGE", "RIFLE", "RIGHT", "RISKY", "RIVER", "ROBOT",
    "ROCKY", "ROUGH", "ROUND", "ROUTE", "ROYAL", "RULER", "SCARY", "SCENE",
    "SCORE", "SCOUT", "SCREW", "SERVE", "SETUP", "SEVEN", "SHAME", "SHAPE",
    "SHARE", "SHARP", "SHEEP", "SHEER", "SHIFT", "SHINE", "SHIRT", "SHOCK",
    "SHOOT", "SHORT", "SHOUT", "SIGHT", "SILLY", "SINCE", "SIXTH", "SIXTY",
    "SKILL", "SLAVE", "SLEEP", "SLICE", "SLIDE", "SLOPE", "SMALL", "SMART",
    "SMELL", "SMILE", "SMOKE", "SNAKE", "SOLVE", "SORRY", "SOUTH", "SPACE",
    "SPEAK", "SPEED", "SPELL", "SPEND", "SPICE", "SPILL", "SPINE", "SPITE",
    "SPLIT", "SPOKE", "SPOON", "SPORT", "SQUAD", "STAFF", "STAGE", "STAKE",
    "STALE", "STAND", "START", "STATE", "STEAM", "STEEL", "STERN", "STOCK",
    "STONE", "STOOD", "STORE", "STORM", "STORY", "STRAP", "STRAW", "STRIP",
    "STUDY", "STYLE", "SUGAR", "SUPER", "SURGE", "SWAMP", "SWEAR", "SWEET",
    "SWEPT", "SWIFT", "SWORD", "TABLE", "TASTE", "TEACH", "TEETH", "THANK",
    "THEME", "THERE", "THESE", "THICK", "THINK", "THIRD", "THOSE", "THREE",
    "THREW", "THUMB", "TIGER", "TIGHT", "TIMER", "TITLE", "TODAY", "TOKEN",
    "TOTAL", "TOUCH", "TOUGH", "TOWEL", "TOWER", "TOXIC", "TRACK", "TRADE",
    "TRAIL", "TRAIN", "TRAIT", "TRASH", "TREAT", "TREND", "TRIAL", "TRIBE",
    "TRICK", "TRIED", "TROOP", "TROUT", "TRUCK", "TRULY", "TRUST", "TRUTH",
    "TWIST", "ULTRA", "UNCLE", "UNDER", "UNITY", "UNTIL", "UPPER", "UPSET",
    "URBAN", "USAGE", "USING", "USUAL", "UTTER", "VALID", "VALUE", "VALVE",
    "VIDEO", "VIGOR", "VIRAL", "VIRUS", "VISIT", "VITAL", "VIVID", "VOCAL",
    "VOTER", "WAGON", "WATER", "WEARY", "WEDGE", "WEIRD", "WORLD", "WORSE",
    "WORST", "WORTH", "WOULD", "WOUND", "WRATH", "WRITE", "WRONG", "YACHT",
    "YIELD", "YOUNG", "YOUTH", "ZEBRA",
    # Additional words
    "ABIDE", "ACORN", "ADORE", "ADORN", "ADEPT", "AGONY", "AMPLE", "ANNEX",
    "BAKER", "BANJO", "BEEFY", "BLUNT", "BOAST", "BOGUS", "BRAID", "BRAWL",
    "BRISK", "BROOD", "BROTH", "BUDGE", "BURLY", "CAMEL", "CAMEO", "CANNY",
    "CEDAR", "CHAIN", "CHAMP", "CHANT", "CHASM", "CHEAT", "CHEWY", "CHICK",
    "CHILL", "CHIMP", "CHIRP", "CHORD", "CINCH", "CLAMP", "CLANG", "CLANK",
    "CLASP", "CLEAT", "CLEFT", "CLERK", "CLICK", "CLINK", "CLOAK", "CLOUT",
    "CLOWN", "CLUCK", "CLUMP", "COMET", "COMIC", "COMMA", "CONCH", "CORNY",
    "COUCH", "COULD", "COVET", "CRIMP", "CRISP", "CROAK", "CROOK", "CROON",
    "CROUP", "CRUST", "CRYPT", "CURLY", "CURRY", "CYCLE", "DENIM", "DENSE",
    "DEPOT", "DERBY", "DISCO", "DIVER", "DIZZY", "DOGMA", "DOWDY", "DRANK",
    "DRAPE", "DROOL", "DROOP", "DRUID", "DUMPY", "DUNCE", "DUSTY", "DWARF",
    "EERIE", "ELBOW", "ELDER", "EMBER", "EPOCH", "ERODE", "ERUPT", "EVADE",
    "EXCEL", "EXILE", "EXPEL", "FABLE", "FARCE", "FERRY", "FIERY", "FINCH",
    "FLAIR", "FLOCK", "FLORA", "FLOUR", "FLUKE", "FLUNK", "FLUTE", "FOAMY",
    "FORAY", "FRAIL", "FREAK", "FROZE", "FUNGI", "FURRY", "GAUDY", "GAUZE",
    "GAVEL", "GECKO", "GENRE", "GLARE", "GLINT", "GLOOM", "GLOSS", "GNOME",
    "GORGE", "GRAFT", "GRAIL", "GRIMY", "GRIPE", "GROIN", "GRUEL", "GRUFF",
    "GRUMP", "GUAVA", "GUILE", "GUISE", "GULCH", "GULLY", "GUMMY", "HAMMY",
    "HANDY", "HARDY", "HAVEN", "HEADY", "HEDGE", "HEIST", "HENCE", "HINGE",
    "HIPPO", "HOARD", "HOARY", "HOMEY", "HUFFY", "HUNKY", "HYENA", "ICING",
    "IDIOM", "IGLOO", "INBOX", "INEPT", "INERT", "INFER", "INGOT", "INLET",
    "INSET", "INTRO", "IONIC", "IRATE", "IRONY", "ITCHY", "JAZZY", "JELLY",
    "JERKY", "JETTY", "JIFFY", "JOINT", "JOKER", "JOLLY", "JOUST", "JUMBO",
    "JUMPY", "KINKY", "KITTY", "KNACK", "KNAVE", "KNEEL", "KNELT", "KNOLL",
    "LAPSE", "LARVA", "LATHE", "LEAFY", "LEAKY", "LEAPT", "LEDGE", "LEFTY",
    "LETUP", "LIEGE", "LINER", "LINGO", "LITHE", "LOFTY", "LONER", "LOOPY",
    "LORRY", "LOUSY", "LOWLY", "LOYAL", "LUCID", "LUMPY", "LUSTY", "LYRIC",
    "MACAW", "MAMBO", "MANGO", "MANLY", "MAPLE", "MARSH", "MEATY", "MIRTH",
    "MISTY", "MOODY", "MOSSY", "MOURN", "MUDDY", "MUGGY", "MULCH", "MURKY",
    "MUSTY", "NASAL", "NASTY", "NATTY", "NIFTY", "NIPPY", "NOMAD", "NUTTY",
    "NYMPH", "OLIVE", "ONSET", "OVERT", "OVOID", "PADDY", "PAGAN", "PASTY",
    "PATSY", "PENAL", "PERCH", "PERKY", "PETAL", "PETTY", "PIXEL", "PLAID",
    "PLEAD", "PLUMB", "PLUME", "PLUMP", "PLUNK", "PLUSH", "POACH", "POLKA",
    "PORCH", "POUTY", "PROWL", "PRUDE", "PUDGY", "PULSE", "PUNKY", "PUPPY",
    "PYGMY", "QUIRK", "RABID", "RAINY", "RATTY", "RAVEN", "REGAL", "REMIX",
    "RENEW", "REPAY", "REPEL", "RERUN", "REVEL", "RIGID", "RIVET", "RIVAL",
    "ROOMY", "ROWDY", "RUDDY", "RUNNY", "RUSTY", "SABER", "SADLY", "SALTY",
    "SANDY", "SASSY", "SATIN", "SAVVY", "SEEDY", "SERUM", "SHADY", "SHAKY",
    "SHALE", "SHALL", "SHAFT", "SHELL", "SHINY", "SHRED", "SHREW", "SHRUB",
    "SHRUG", "SLANG", "SLANT", "SLASH", "SLATE", "SLEET", "SLICK", "SLIMY",
    "SLING", "SLINK", "SLOTH", "SLUMP", "SLURP", "SMASH", "SMEAR", "SMELT",
    "SMIRK", "SMITE", "SMOKY", "SNARE", "SNARL", "SNEAK", "SNIFF", "SNORT",
    "SOOTY", "SPANK", "SPAWN", "SPECK", "SPIED", "SPINY", "SPOOF", "SPOOL",
    "SPRAY", "SPRIG", "SPUNK", "SPURN", "STAID", "STAIN", "STAIR", "STALK",
    "STAMP", "STARK", "STASH", "STAVE", "STEAD", "STEED", "STEER", "STEIN",
    "STIFF", "STILL", "STING", "STINK", "STINT", "STOMP", "STOUT", "STOVE",
    "SULKY", "SUNNY", "SURLY", "SWILL", "SWIPE", "SYRUP", "TABBY", "TAFFY",
    "TANGY", "TATTY", "TAUNT", "TAWNY", "TEPID", "TERSE", "THUMP", "TIARA",
    "TIMID", "TIPSY", "TOAST", "TOTEM", "TRICE", "TRITE", "TROLL", "TRYST",
    "TUBBY", "TWERP", "UMBRA", "UNCUT", "UNION", "UNLIT", "UNZIP", "VAPID",
    "VAULT", "VAUNT", "VENOM", "VERGE", "VERSE", "VIPER", "VISOR", "VISTA",
    "VIXEN", "VODKA", "VOMIT", "WAKEN", "WAVER", "WHACK", "WHALE", "WHIFF",
    "WHINE", "WHILE", "WHIRL", "WHISK", "WHOSE", "WIDEN", "WIMPY", "WINDY",
    "WITTY", "WREAK", "WREST", "WRING", "ZIPPY",
]

_ANSWER_ZIPF_THRESHOLD = 4.0

# Deduplicate and ensure exactly 5 uppercase alphabetic characters
_WORD_SET: set[str] = {
    w.upper()
    for w in WORDS
    if len(w) == 5 and w.isalpha()
}

WORDS = sorted(_WORD_SET)

# Answer candidates: common words only (Zipf >= threshold)
_ANSWER_WORDS: list[str] = [
    w for w in WORDS
    if zipf_frequency(w, "en") >= _ANSWER_ZIPF_THRESHOLD
]


def get_random_word() -> str:
    """Return a random answer word (common words only)."""
    return random.choice(_ANSWER_WORDS)


def is_valid_word(word: str) -> bool:
    """Return True if the word exists in English (any difficulty)."""
    w = word.lower()
    return len(set(w)) >= 2 and zipf_frequency(w, "en") > 0
