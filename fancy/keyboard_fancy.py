## this file just stores an array of bounding boxes for 'keyboard.png' (QWERTY keyboard)

## CV2 version is TODO!

import pygame       # needed to retrieve the '.K_' jey variables
from os import path

keyboardImage = pygame.image.load(path.join(path.dirname(__file__), "keyboard.png"))

# the array is setup as: ( ((pygame_key, unicode_key), ((topleft_X,topleft_Y), (width,height))), etc.)  where XY coordinates are in pixels, origin is topleft
keyBoundingBoxes : tuple[tuple[tuple[int,int], tuple[tuple[float,float],tuple[float,float]]]] = ( \
  
  ((pygame.K_BACKQUOTE, ord('`')), ((15,62),(60,59))),
  ((pygame.K_1, ord('1')), ((83,62),(59,59))),
  ((pygame.K_2, ord('2')), ((150,62),(59,59))),
  ((pygame.K_3, ord('3')), ((218,62),(59,59))),
  ((pygame.K_4, ord('4')), ((285,62),(59,59))),
  ((pygame.K_5, ord('5')), ((352,62),(59,59))),
  ((pygame.K_6, ord('6')), ((420,62),(59,59))),
  ((pygame.K_7, ord('7')), ((487,62),(59,59))),
  ((pygame.K_8, ord('8')), ((554,62),(60,59))),
  ((pygame.K_9, ord('9')), ((622,62),(59,59))),
  ((pygame.K_0, ord('0')), ((689,62),(59,59))),
  ((pygame.K_MINUS, ord('-')), ((757,62),(59,59))),
  ((pygame.K_EQUALS, ord('=')), ((824,62),(59,59))),
  # ((pygame.K_BACKSPACE, ???), ((891,62),(94,59))),

  # ((pygame.K_TAB, ord('\t')), ((15,127),(94,59))),
  ((pygame.K_q, ord('q')), ((117,127),(59,59))),
  ((pygame.K_w, ord('w')), ((184,127),(59,59))),
  ((pygame.K_e, ord('e')), ((252,127),(59,59))),
  ((pygame.K_r, ord('r')), ((319,127),(59,59))),
  ((pygame.K_t, ord('t')), ((387,127),(59,59))),
  ((pygame.K_y, ord('y')), ((454,127),(59,59))),
  ((pygame.K_u, ord('u')), ((521,127),(59,59))),
  ((pygame.K_i, ord('i')), ((589,127),(59,59))),
  ((pygame.K_o, ord('o')), ((656,127),(59,59))),
  ((pygame.K_p, ord('p')), ((723,127),(60,59))),
  ((pygame.K_LEFTBRACKET, ord('[')), ((791,127),(59,59))),
  ((pygame.K_RIGHTBRACKET, ord(']')), ((858,127),(59,59))),
  # ((pygame.K_BACKSLASH, ord('\\')), ((926,127),(59,59))),

  # ((pygame.K_CAPSLOCK, ???), ((15,192),(117,59))),
  ((pygame.K_a, ord('a')), ((140,192),(59,59))),
  ((pygame.K_s, ord('s')), ((207,192),(59,59))),
  ((pygame.K_d, ord('d')), ((274,192),(59,59))),
  ((pygame.K_f, ord('f')), ((342,192),(59,59))),
  ((pygame.K_g, ord('g')), ((409,192),(59,59))),
  ((pygame.K_h, ord('h')), ((476,192),(59,59))),
  ((pygame.K_j, ord('j')), ((544,192),(59,59))),
  ((pygame.K_k, ord('k')), ((611,192),(59,59))),
  ((pygame.K_l, ord('l')), ((679,192),(59,59))),
  ((pygame.K_SEMICOLON, ord(';')), ((746,192),(59,59))),
  ((pygame.K_QUOTE, ord("'")), ((813,192),(59,59))),
  # ((pygame.K_RETURN, ord('\n')), ((881,192),(104,59))),

  # ((pygame.K_LSHIFT, ???), ((15,257),(59,59))),
  ((pygame.K_z, ord('z')), ((172,257),(59,59))),
  ((pygame.K_x, ord('x')), ((239,257),(60,59))),
  ((pygame.K_c, ord('c')), ((307,257),(59,59))),
  ((pygame.K_v, ord('v')), ((374,257),(59,59))),
  ((pygame.K_b, ord('b')), ((442,257),(59,59))),
  ((pygame.K_n, ord('n')), ((509,257),(59,59))),
  ((pygame.K_m, ord('m')), ((576,257),(59,59))),
  ((pygame.K_COMMA, ord(',')), ((644,257),(59,59))),
  ((pygame.K_PERIOD, ord('.')), ((711,257),(59,59))),
  ((pygame.K_SLASH, ord('/')), ((778,257),(60,59))),
  # ((pygame.K_RSHIFT, ???), ((846,257),(139,59))),

  # ((pygame.K_LCTRL, ???), ((83,321),(59,71))),
  # ((pygame.K_LALT, ???), ((150,321),(59,71))),
  ((pygame.K_SPACE, ord(' ')), ((306,321),(329,71)))
  # ((pygame.K_RALT, ???), ((732,321),(60,71))),
  # ((pygame.K_UP, ???), ((862,321),(59,35))),
  # ((pygame.K_LEFT, ???), ((798,357),(59,35))),
  # ((pygame.K_DOWN, ???), ((862,357),(59,35))),
  # ((pygame.K_RIGHT, ???), ((926,357),(59,35))),
  )
## note: not all keys may be available in CV2, not sure yet
## a potential resource might be: https://www.cita.utoronto.ca/~merz/intel_f10b/main_for/mergedProjects/lref_for/art/afckey1.gif