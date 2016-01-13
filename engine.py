import numpy as np
import scipy.ndimage

# piece byte masks
HOLE_MASK = np.uint8(0b1)
PIECE_MASK = np.uint8(0b10)
PUSHER_MASK = np.uint8(0b100)
BLACK_MASK = np.uint8(0b1000)
ANCHOR_MASK = np.uint8(0b10000)
# basic board template
BOARD_TPL = np.zeros((4, 8), dtype=np.uint8)
BOARD_TPL[0,[0,1,7]] = HOLE_MASK
BOARD_TPL[3,[0,6,7]] = HOLE_MASK


def _make_piece(black=False, pusher=False, anchor=False):
  piece = PIECE_MASK
  if black:
    piece |= BLACK_MASK
  if pusher:
    piece |= PUSHER_MASK
  if anchor:
    piece |= ANCHOR_MASK
  return piece


class BoardState(object):
  @staticmethod
  def initialize(initial_pieces):
    '''Returns an initialized BoardState object.
    initial_pieces : sequence of (i,j,piece_kwargs) tuples'''
    b = BoardState()
    b._board = BOARD_TPL.copy()
    for i,j,kwargs in initial_pieces:
      b._board[i,j] = _make_piece(**kwargs)
    b.turn = 0
    return b

  def copy(self):
    '''Returns a deep-copied BoardState object'''
    b = BoardState()
    b._board = self._board.copy()
    b.turn = self.turn
    return b

  def current_player(self):
    '''Returns 0 if white, 1 if black'''
    return self.turn % 2

  def move(self, moves):
    assert 1 <= len(moves) <= 3, 'bad number of moves'
    player = self.turn % 2
    # run standard moves
    for m in moves[:-1]:
      valid, msg = self.has_path(player, *m)
      assert valid, 'invalid move: ' + msg
      self._do_slide(player, *m)
    # do the push
    valid, result = self.can_push(player, *moves[-1])
    assert valid, 'invalid push: ' + result
    if result is True:
      # game over
      return True
    i0, j0 = moves[-1][:2]
    self._do_push(player, i0, j0, *result)
    # game continues
    self.turn += 1
    return False

  def _do_slide(self, player, i0, j0, i1, j1):
    '''Note: does no validation!'''
    self._board[i1,j1] = self._board[i0,j0]
    self._board[i0,j0] = 0

  def _do_push(self, player, i0, j0, i, j, di, dj):
    '''Note: does no validation!'''
    while i != i0 or j != j0:
      self._board[i, j] = self._board[i-di, j-dj]
      i -= di
      j -= dj
    self._board[i, j] = 0
    # clear the old anchor (wherever it is)
    self._board &= ~ANCHOR_MASK
    # set the new anchor
    self._board[i+di, j+dj] |= ANCHOR_MASK

  def can_push(self, player, i0, j0, i1, j1):
    piece = self._board[i0,j0]
    if not ((piece & PUSHER_MASK) and (piece & PIECE_MASK)):
      return False, 'not a pusher'
    if not (int(bool(piece & BLACK_MASK)) == player):
      return False, 'wrong player'
    if not (self._board[i1,j1] & PIECE_MASK):
      return False, 'not pushing a piece'
    di = i1 - i0
    dj = j1 - j0
    if not abs(di) + abs(dj) == 1:
      return False, 'move >1 distance'
    while 0 <= j1 < 8:
      if not 0 <= i1 < 4:
        return False, 'pushed against the wall'
      spot = self._board[i1,j1]
      if spot == 0:
        return True, (i1, j1, di, dj)
      if spot & HOLE_MASK:
        # TODO: make sure we aren't pushing ourselves off
        return True, True
      if spot & ANCHOR_MASK:
        return False, 'tried to push anchor'
      i1 += di
      j1 += dj
    return False, 'hit the wall'

  def has_path(self, player, i0, j0, i1, j1):
    piece = self._board[i0,j0]
    # basic sanity checks
    if not (piece & PIECE_MASK):
      return False, 'not a piece'
    if self._board[i1,j1] != 0:
      return False, 'destination not empty'
    if int(bool(piece & BLACK_MASK)) != player:
      return False, 'wrong player'
    # check for a clear path
    regions = (self._board==0).astype(int)
    regions[i0,j0] = 1
    scipy.ndimage.label(regions, output=regions)
    if regions[i0,j0] != regions[i1,j1]:
      return False, 'path is blocked'
    return True, ''

  def valid_moves(self, player=None, num_slides=0):
    assert 0 <= num_slides <= 2
    if player is None:
      player = self.turn % 2
    if num_slides == 0:
      for m in self._valid_pushes(player):
        yield [m]
    else:
      for m in self._valid_slides(player):
        board = self.copy()
        board._do_slide(player, *m)
        for mm in board.valid_moves(player, num_slides-1):
          yield [m] + mm

  def _valid_slides(self, player):
    # find all pieces of our color
    mask = (self._board & PIECE_MASK).astype(bool)
    mask &= (self._board & BLACK_MASK).astype(bool) == bool(player)
    open_spaces = (self._board==0).astype(int)
    for i0,j0 in zip(*np.where(mask)):
      regions = open_spaces.copy()
      regions[i0,j0] = 1
      scipy.ndimage.label(regions, output=regions)
      label = regions[i0,j0]
      regions[i0,j0] += 1  # to avoid null moves
      for i1,j1 in zip(*np.where(regions == label)):
        yield i0, j0, i1, j1

  def _valid_pushes(self, player):
    # find all pushers of our color
    mask = (self._board & PUSHER_MASK).astype(bool)
    mask &= (self._board & BLACK_MASK).astype(bool) == bool(player)
    for i0,j0 in zip(*np.where(mask)):
      for di,dj in [(-1,0),(1,0),(0,-1),(0,1)]:
        i1, j1 = i0+di, j0+dj
        in_bounds = 0 <= i1 < 4 and 0 <= j1 < 8
        if in_bounds and self.can_push(player, i0, j0, i1, j1)[0]:
          yield i0, j0, i1, j1

  def __str__(self):
    s = '  12345678 \n +--------+\n'
    for letter, row in zip('ABCD', self._board):
      s += letter + '|'
      for x in row:
        if x & HOLE_MASK:
          c = ' '
        elif not x & PIECE_MASK:
          c = '.'
        elif x & PUSHER_MASK:
          c = 'w' if x & BLACK_MASK else 'm'
          if x & ANCHOR_MASK:
            c = c.upper()
        else:
          c = 'v' if x & BLACK_MASK else 'n'
        s += c
      s += '|\n'
    return s + ' +--------+\n'
