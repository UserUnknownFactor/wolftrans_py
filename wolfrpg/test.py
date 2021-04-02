import sys, os, re, datetime, tempfile, copy, glob
from route import *
from commands import *
from maps import *
from common_events import *
from gamedats import *
from databases import *

import unittest

#sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

class TestWolfParsers(unittest.TestCase):
    def test_read_map(self):
        m = Map('Data\\Map003.mps')
        self.assertTrue(m is not None)

    def test_read_commonevents(self):
        ce = CommonEvents('Data\\CommonEvent.dat')
        self.assertTrue(ce is not None)

    def test_read_database(self):
        db = Database('Data\\SysDatabase.project', 'Data\\SysDatabase.dat') #skip SysDatabaseBasic
        self.assertTrue(db is not None)

    def test_read_gamedat(self):
        gd = GameDat('Data\\game.dat')
        self.assertTrue(gd is not None)

#if __name__ == "__main__":
#    pass
