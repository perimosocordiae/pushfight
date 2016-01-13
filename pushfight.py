from __future__ import print_function
from engine import BoardState
# shim for py3k support
try:
  raw_input
except NameError:
  raw_input = input


def parse_moves(move_str):
  moves = []
  for m in move_str.split():
    i0 = ord(m[0].upper()) - 65
    i1 = ord(m[2].upper()) - 65
    j0, j1 = int(m[1]) - 1, int(m[3]) - 1
    moves.append((i0,j0,i1,j1))
  return moves


def encode_moves(moves):
  parts = []
  for i0,j0,i1,j1 in moves:
    parts.append('%s%d%s%d' % (chr(i0+65), j0+1, chr(i1+65), j1+1))
  return ' '.join(parts)


def main():
  b = BoardState.initialize([
      # white pieces
      (0, 3, dict(pusher=True)),
      (1, 3, dict(pusher=False)),
      (2, 2, dict(pusher=True)),
      (2, 3, dict(pusher=True)),
      (3, 3, dict(pusher=False)),
      # black pieces
      (0, 4, dict(black=True, pusher=True)),
      (1, 4, dict(black=True, pusher=False)),
      (1, 5, dict(black=True, pusher=True)),
      (2, 4, dict(black=True, pusher=False)),
      (3, 4, dict(black=True, pusher=True)),
  ])
  players = ('White (m/n)', 'Black (w/v)')
  while True:
    print(b)
    print("%s's turn." % players[b.current_player()])
    m0 = sum(1 for _ in b.valid_moves(num_slides=0))
    m1 = sum(1 for _ in b.valid_moves(num_slides=1))
    m2 = sum(1 for _ in b.valid_moves(num_slides=2))
    print(' * %d push-only moves' % m0,
          ' * %d slide x1 + push moves' % m1,
          ' * %d slide x2 + push moves' % m2, sep='\n')
    moves = parse_moves(raw_input('Input a move sequence: '))
    if b.move(moves):
      print('Game over!')
      break

if __name__ == '__main__':
  main()
