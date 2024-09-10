from .filecoder import FileCoder
from io import BytesIO
from enum import IntEnum

HAS_SOLVER = True
try:
    from .randomgen import generate_randoms
except:
    HAS_SOLVER = False

class MidiSource(IntEnum):
    HARDWARE = 0
    SOFTWARE = 1
    DISABLED = 2

class VEnable(IntEnum):
    DISABLED = 0
    ENABLED = 1

class InactiveBehavior(IntEnum):
    PAUSE = 0
    RUNNING = 1

class AntiAliasing(IntEnum):
    ENABLED = 0
    DISABLED = 1
    DISABLED_DOUBLE_WIDTH = 2

class ImageScale(IntEnum):
    ROUGH = 0
    SMOOTH = 1

class VersionHeader(IntEnum):
    V2 = 0
    V3 = 85

class CharacterMovementWidth(IntEnum):
    SQUARE0_5 = 0
    SQUARE1 = 1

class CharacterAnimationPatterns(IntEnum):
    P3 = 3
    P5 = 5

class CharacterDirections(IntEnum):
    D4 = 4
    D8 = 8

class TileSize(IntEnum):
    T16X16 = 16
    T32X32 = 32
    T40X40 = 40
    T48X48 = 48

class Fps(IntEnum):
    F30 = 30
    F60 = 60

class SpecialFunctionType(IntEnum):
    DISABLED = 0
    LOAD_FROM_FILE = 1
    LOAD_FROM_DATABASE = 2
    MANUAL = 3

class VersionFooter(IntEnum):
    V2 = 194
    V3_0 = 195
    V3_3 = 196

class Language(IntEnum):
    DEFAULT = 0
    JAPANESE = 1
    HANGUL = 2
    TRADITIONAL_CHINESE = 3
    SIMPLIFIED_CHINESE = 4
    ENGLISH = 5
    WESTERN_EUROPEAN = 6

class Operator(IntEnum):
    GREATER_THAN = 0
    GREATER_OR_EQUAL = 1
    EQUAL = 2
    LESS_OR_EQUAL = 3
    LESS_THAN = 4
    NOT_EQUAL = 5
    BITWISE_AND = 6

class GraphicRenderMode(IntEnum):
    NORMAL = 0
    MULTIPLY = 1
    ADD = 2
    SUBSTRACT = 3

class CharacterAnimation(IntEnum):
    BACK_AND_FORTH = 0
    LOOP = 1

class MoveSpeed(IntEnum):
    SPEED_1X = 4
    SPEED_1_25X = 5
    SPEED_1_5X = 6
    SPEED_1_75X = 7
    SPEED_2X = 8
    CUSTOM = 9

class Frequency(IntEnum):
    EVERY_FRAME = 0
    VERY_SHORT = 1
    SHORT = 2
    MEDIUM = 3
    LONG = 4
    VERY_LONG = 5

class ScreenScale(IntEnum):
    SCALE_1X = 1
    SCALE_2X = 2
    SCALE_3X = 3

class DataIdMethod(IntEnum):
    MANUAL = 0
    SAME_AS_FIRST_STRING_DATA = 1
    SAME_AS_PRECEDING_TYPE_DATA_ID = 2
    FROM_TYPE_IN_DB = 10000


class StringSettings():
    def __init__(self, coder):
        self._string_count  = coder.read_u4()
        self.title          = coder.read_string()
        self.serial         = coder.read_string()
        encryption_key_len = coder.read_u4()
        self.encryption_key = coder.read(encryption_key_len)

        self.font = coder.read_string()
        self.subfonts = [coder.read_string() for _ in range(3)]

        self.starting_hero_graphic = coder.read_string()

        if self._string_count >= 9:
            self.version = coder.read_string()

        if self._string_count > 9:
            self.pro_loading_pic   = coder.read_string()
            self.pro_loading_gauge = coder.read_string()
            self.pro_title_during_loading  = coder.read_string()
            self.pro_title_during_gameplay = coder.read_string()

        if self._string_count > 13:
            self.unknown_strings = []
            for i in range(self._string_count - 13):
                self.unknown_strings.append(coder.read_string())

    def write(self, coder):
        coder.write_u4(self._string_count)
        coder.write_string(self.title)
        coder.write_string(self.serial)
        coder.write_u4(len(self.encryption_key))
        coder.write(self.encryption_key)

        coder.write_string(self.font)
        for subfont in self.subfonts:
            coder.write_string(subfont)

        coder.write_string(self.starting_hero_graphic)

        if self._string_count >= 9:
            coder.write_string(self.version)

        if self._string_count > 9:
            coder.write_string(self.pro_loading_pic)
            coder.write_string(self.pro_loading_gauge)
            coder.write_string(self.pro_title_during_loading)
            coder.write_string(self.pro_title_during_gameplay)

        if self._string_count > 13:
            for string in self.unknown_strings:
                coder.write_string(string)

    def byte_size(self, coder):
        size = 4  # for _string_count
        size += coder.calc_string_size(self.title) + 4
        size += coder.calc_string_size(self.serial) + 4
        size += len(self.encryption_key) + 4

        size += coder.calc_string_size(self.font) + 4
        for subfont in self.subfonts:
            size += coder.calc_string_size(subfont) + 4

        size += coder.calc_string_size(self.starting_hero_graphic) + 4

        if self._string_count >= 9:
            size += coder.calc_string_size(self.version) + 4

        if self._string_count > 9:
            size += coder.calc_string_size(self.pro_loading_pic) + 4
            size += coder.calc_string_size(self.pro_loading_gauge) + 4
            size += coder.calc_string_size(self.pro_title_during_loading) + 4
            size += coder.calc_string_size(self.pro_title_during_gameplay) + 4

        if self._string_count > 13:
            for string in self.unknown_strings:
                size += coder.calc_string_size(string) + 4

        return size

class ByteSettings():
    def __init__(self, coder):
        self._u1_count = coder.read_u4()
        self.tile_size = TileSize(coder.read_u1())
        self.character_directions_image = CharacterDirections(coder.read_u1())
        self.character_directions_move = CharacterDirections(coder.read_u1())
        self.guruguru_enabled = VEnable(coder.read_u1())
        self.fps = Fps(coder.read_u1())
        self.character_shadow = VEnable(coder.read_u1())
        self.midi_source = MidiSource(coder.read_u1())
        self.character_animation_patterns = CharacterAnimationPatterns(coder.read_u1())
        self.character_movement_width = CharacterMovementWidth(coder.read_u1())
        self.character_movement_hitbox = CharacterMovementWidth(coder.read_u1())
        self.text_horizontal_padding = coder.read_u1()
        self.text_line_spacing = coder.read_u1()
        self.choice_line_spacing = coder.read_u1()
        self.unknown = coder.read_u1()
        self.anti_aliasing = AntiAliasing(coder.read_u1())
        self.move_speed_event = MoveSpeed(coder.read_u1())
        self.move_speed_hero_allies = MoveSpeed(coder.read_u1())
        self.in_game_language = Language(coder.read_u1())
        self.image_scaling_method = ImageScale(coder.read_u1())
        self.inactive_window_behavior = InactiveBehavior(coder.read_u1())
        self.system_language = Language(coder.read_u1())
        if self._u1_count > 21:
            self.unknown_2 = coder.read_u1()
            self.pro_enable_f4 = VEnable(coder.read_u1())
            self.pro_enable_f5 = VEnable(coder.read_u1())
            self.pro_enable_f8 = VEnable(coder.read_u1())
            self.pro_enable_f11 = VEnable(coder.read_u1())
            self.pro_enable_f12 = VEnable(coder.read_u1())
            self.pro_enable_prtscr = VEnable(coder.read_u1())
            self.unknown_3 = coder.read_u1()
            self.unknown_4 = coder.read_u1()
            self.unknown_5 = coder.read_u1()
            self.unknown_6 = coder.read_u1()
            self.pro_screen_scale = ScreenScale(coder.read_u1())
            self.pro_loading_fadein = VEnable(coder.read_u1())
            self.pro_loading_fadeout = VEnable(coder.read_u1())
        if self._u1_count > 35:
            self.settings_new = coder.read_byte_array(self._u1_count - 35)

    def write(self, coder):
        coder.write_u4(self._u1_count)
        coder.write_u1(self.tile_size)
        coder.write_u1(self.character_directions_image)
        coder.write_u1(self.character_directions_move)
        coder.write_u1(self.guruguru_enabled)
        coder.write_u1(self.fps)
        coder.write_u1(self.character_shadow)
        coder.write_u1(self.midi_source)
        coder.write_u1(self.character_animation_patterns)
        coder.write_u1(self.character_movement_width)
        coder.write_u1(self.character_movement_hitbox)
        coder.write_u1(self.text_horizontal_padding)
        coder.write_u1(self.text_line_spacing)
        coder.write_u1(self.choice_line_spacing)
        coder.write_u1(self.unknown)
        coder.write_u1(self.anti_aliasing)
        coder.write_u1(self.move_speed_event)
        coder.write_u1(self.move_speed_hero_allies)
        coder.write_u1(self.in_game_language)
        coder.write_u1(self.image_scaling_method)
        coder.write_u1(self.inactive_window_behavior)
        coder.write_u1(self.system_language)
        if self._u1_count > 21:
            coder.write_u1(self.unknown_2)
            coder.write_u1(self.pro_enable_f4)
            coder.write_u1(self.pro_enable_f5)
            coder.write_u1(self.pro_enable_f8)
            coder.write_u1(self.pro_enable_f11)
            coder.write_u1(self.pro_enable_f12)
            coder.write_u1(self.pro_enable_prtscr)
            coder.write_u1(self.unknown_3)
            coder.write_u1(self.unknown_4)
            coder.write_u1(self.unknown_5)
            coder.write_u1(self.unknown_6)
            coder.write_u1(self.pro_screen_scale)
            coder.write_u1(self.pro_loading_fadein)
            coder.write_u1(self.pro_loading_fadeout)
        if self._u1_count > 35:
            for setting in self.settings_new:
                coder.write_u1(setting)

    def byte_size(self):
        return 4 + self._u1_count

class WordSettings():
    def __init__(self, coder):
        self._u2_count = coder.read_u4()
        self.unknown_1 = coder.read_u2()
        self.custom_move_speed_hero_allies_0 = coder.read_u2()
        self.custom_move_speed_events_0 = coder.read_u2()
        self.custom_move_speed_hero_allies_1 = coder.read_u2()
        self.custom_move_speed_events_1 = coder.read_u2()
        self.custom_move_speed_hero_allies_2 = coder.read_u2()
        self.custom_move_speed_events_2 = coder.read_u2()
        self.custom_move_speed_hero_allies_3 = coder.read_u2()
        self.custom_move_speed_events_3 = coder.read_u2()
        self.custom_move_speed_hero_allies_4 = coder.read_u2()
        self.custom_move_speed_events_4 = coder.read_u2()
        self.custom_move_speed_hero_allies_5 = coder.read_u2()
        self.custom_move_speed_events_5 = coder.read_u2()
        self.custom_move_speed_hero_allies_6 = coder.read_u2()
        self.custom_move_speed_events_6 = coder.read_u2()
        self.unknown_2 = coder.read_u2()
        if self._u2_count > 16:
            self.screen_dimensions_w = coder.read_u2()
            self.screen_dimensions_h = coder.read_u2()
            self.wolf_rpg_version = coder.read_u2()
        if self._u2_count > 19:
            self.pro_loading_gauge_x = coder.read_u2()
        if self._u2_count > 20:
            self.pro_loading_gauge_y = coder.read_u2()
        if self._u2_count > 21:
            self.unknown_3 = coder.read_u2()
        if self._u2_count > 22:
            self.pro_default_screen_scale = coder.read_u2()
        if self._u2_count > 23:
            self.settings_new = coder.read_word_array(self._u2_count - 23)

    def write(self, coder):
        coder.write_u4(self._u2_count)
        coder.write_u2(self.unknown_1)
        coder.write_u2(self.custom_move_speed_hero_allies_0)
        coder.write_u2(self.custom_move_speed_events_0)
        coder.write_u2(self.custom_move_speed_hero_allies_1)
        coder.write_u2(self.custom_move_speed_events_1)
        coder.write_u2(self.custom_move_speed_hero_allies_2)
        coder.write_u2(self.custom_move_speed_events_2)
        coder.write_u2(self.custom_move_speed_hero_allies_3)
        coder.write_u2(self.custom_move_speed_events_3)
        coder.write_u2(self.custom_move_speed_hero_allies_4)
        coder.write_u2(self.custom_move_speed_events_4)
        coder.write_u2(self.custom_move_speed_hero_allies_5)
        coder.write_u2(self.custom_move_speed_events_5)
        coder.write_u2(self.custom_move_speed_hero_allies_6)
        coder.write_u2(self.custom_move_speed_events_6)
        coder.write_u2(self.unknown_2)
        if self._u2_count > 16:
            coder.write_u2(self.screen_dimensions_w)
            coder.write_u2(self.screen_dimensions_h)
            coder.write_u2(self.wolf_rpg_version)
        if self._u2_count > 19:
            coder.write_u2(self.pro_loading_gauge_x)
        if self._u2_count > 20:
            coder.write_u2(self.pro_loading_gauge_y)
        if self._u2_count > 21:
            coder.write_u2(self.unknown_3)
        if self._u2_count > 22:
            coder.write_u2(self.pro_default_screen_scale)
        if self._u2_count > 23:
            for setting in self.settings_new:
                coder.write_u2(setting)

    def byte_size(self):
        return 4 + self._u2_count * 2

class GameDat():
    SEED_INDICES = [0, 8, 6]
    #XSEED_INDICES = [3, 4, 5]

    GAMEDAT_MAGIC = b'W\0\0OL\0FM'
    SERIAL_DEFAULT = "0000-0000"

    @property
    def encrypted(self):
        return self.crypt_header != None

    def __init__(self, filename):
        with FileCoder.open(filename, 'r', self.SEED_INDICES) as coder:
            if coder.encrypted:
                self.crypt_header = coder.crypt_header
            else:
                self.crypt_header = None
                coder.verify(self.GAMEDAT_MAGIC)

            self.engine_version = VersionHeader(coder.read_u1())
            coder.is_utf8 = (self.engine_version == VersionHeader.V3)

            self.byte_settings = ByteSettings(coder)
            self.string_settings = StringSettings(coder)

            pos1 = coder.tell
            self.file_size = coder.read_u4()
            real_size = coder.filesize()
            assert self.file_size == real_size, (
                f"size is unexpected; claims {self.file_size}, got: {real_size}")

            self.hid_pos_len = coder.read_u4()
            self.word_settings = WordSettings(coder)

            self._rands_offset = coder.tell
            self.pos_random_bases = coder.read_u4()
            self.pos_obfuscations = coder.read_u4()
            pos2 = coder.tell
            self.randoms = coder.read(29000 - (pos2 - pos1))  # pos2 - pos1 = 52 for V2
            self.footer = VersionFooter(coder.read_u1())
            pass

    def write(self, filename):
        global HAS_SOLVER
        stream = BytesIO()
        with FileCoder(stream, 'w', filename, self.SEED_INDICES, self.crypt_header) as coder:
            if not self.encrypted:
                coder.write(self.GAMEDAT_MAGIC)
            coder.write_u1(self.engine_version)

            self.byte_settings.write(coder)
            self.string_settings.write(coder)

            pos1 = coder.tell
            new_size  = self.byte_size(coder)
            delta = new_size - self.file_size
            coder.write_u4(new_size)  # file_size
            coder.write_u4(self.hid_pos_len)
            self.word_settings.write(coder)

            # static randoms
            pos2 = coder.tell
            if HAS_SOLVER:
                r1, r2, new_randoms = generate_randoms(
                   self._rands_offset, self.pos_random_bases, self.pos_obfuscations, pos2, 29000 - (
                       pos2 - pos1 + 8), self.randoms, self.hid_pos_len)
                if r1 is None:
                    HAS_SOLVER = False
                else:
                    coder.write_u4(r1)
                    coder.write_u4(r2)
                    coder.write(new_randoms)
            if not HAS_SOLVER:
                assert delta == 0, "Maintain the same modded bytesize " + (
                        f"(diff: {('+' + str(delta)) if delta > 0 else delta}B) or use the Editor")
                coder.write_u4(self.pos_random_bases)
                coder.write_u4(self.pos_obfuscations)
                coder.write(self.randoms)
            coder.write_u1(self.footer)

        with open(filename, 'wb') as f:
            stream.seek(0)
            f.write(stream.getbuffer())

    def byte_size(self, coder):
        size = 0
        size += len(self.GAMEDAT_MAGIC)
        size += 1 # for engine_version
        size += self.byte_settings.byte_size()
        size += self.string_settings.byte_size(coder)
        size += 29000
        size += 1
        """
        size += 4  # for file_size
        size += 4 # for unknown1
        size += self.word_settings.byte_size()
        size += 4 # for r1
        size += 4 # for r2
        size += len(self.randoms) # 29000 - 52
        size += 1 # for footer
        """
        return size