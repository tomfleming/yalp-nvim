"""Sends vim buffer to socketio server"""

import os
import sys
from subprocess import check_output
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

    @neovim.autocmd('BufReadPost',
                    pattern='*.rst',
                    eval='expand("<afile>")')
        self.makefile_dir = os.path.expanduser(self.nvim.command_output('pwd'))
        self.makefile = os.path.join(self.makefile_dir, 'Makefile')
        self.has_makefile = os.path.isfile(self.makefile)

        self.proc = Process(target=sio.runserver)
        self.proc.start()
        check_output(['open', '-g', 'http://localhost:8000'])

    @neovim.autocmd('CursorMoved,CursorMovedI',
                    pattern='*.rst',
                    eval='expand("<afile>")')
    def on_edit(self, filename):
        """Send buffer contents to socketio server via PUT request"""
        buf = self.nvim.current.buffer
        html = publish_string("\n".join(buf[:]),
                              writer_name='html',
                              settings_overrides={'report_level':'quiet'})
        try:
            requests.put("http://localhost:8000/render", html)
        except Exception, err:
            print filename
            print err

    @neovim.autocmd('BufWritePost',
                    pattern='*.rst',
                    eval='expand("<afile>")')
    def make_html(self, filename):
        """Send html contents to socketio server via PUT request"""
        if self.has_makefile:
            try:
                check_output(['make', 'html'], cwd=self.makefile_dir)
                requests.put("http://localhost:8000/render", filename)
            except Exception, err:
                print filename
                try:
                    requests.put("http://localhost:8000/render", err)
                except:
                    print err

    @neovim.autocmd('VimLeavePre', pattern='*.rst')
    def quit_webserver(self):
        try:
            requests.put("http://localhost:8000/quit")
            self.proc.terminate()
        except:
            pass


    def parse_makefile(self):
        """Retrieve options from sphinx makefile"""
        if self.has_makefile:
            with open(self.makefile, 'r') as mf:
                options = [line for line in mf.readlines() if '=' in line]
            options = dict([
                (l[0].strip(), " ".join(l[2:]).strip())
                for l in map(str.split, options, "=")])
            return options
        else:
            return {}
