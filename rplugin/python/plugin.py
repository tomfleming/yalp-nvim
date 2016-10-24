"""Sends vim buffer to socketio server"""

import os
import sys
from multiprocessing import Process

import neovim
import requests
from docutils.core import publish_string

HERE = os.path.dirname(os.path.abspath(os.path.expanduser(__file__)))
sys.path.insert(0, HERE)
import sio

@neovim.plugin
class TestPlugin(object):
    """Plugin for live-previewing RST (and other?) documents"""

    def __init__(self, nvim):
        self.nvim = nvim

        proc = Process(target=sio.runserver)
        proc.start()

    @neovim.autocmd('CursorMoved,CursorMovedI',
                    pattern='*.rst',
                    eval='expand("<afile>")',
                    sync=True)
    def on_edit(self, filename):
        """Send buffer contents to socketio server via PUT request"""
        self.nvim.out_write("Stuff and junk")
        buf = self.nvim.current.buffer
        html = publish_string("\n".join(buf[:]),
                              writer_name='html',
                              settings_overrides={'report_level':'quiet'})
        try:
            requests.put("http://localhost:8000/render", html)
        except Exception, err:
            print filename
            print err
