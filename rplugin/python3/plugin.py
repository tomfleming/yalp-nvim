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
        self.server_started = False
        self.html = ''

    @neovim.autocmd('BufEnter',
                    pattern='*.rst',
                    eval='expand("<afile>")')
    def start_server(self, afile):
        if not self.server_started:
            self.server_started = True
            try:
                self.makefile_dir = os.path.expanduser(
                    self.nvim.command_output('pwd'))
                self.makefile = os.path.join(self.makefile_dir, 'Makefile')
                self.has_makefile = os.path.isfile(self.makefile)

                self.proc = Process(target=sio.runserver)
                self.proc.start()
                check_output(['open', '-g', 'http://localhost:8000'])
            except Exception as e:
                with open("/Users/tomdfleming/anotherthing.txt", "w") as f:
                    f.write(str(e))

    @neovim.autocmd('CursorMoved,CursorMovedI',
                    pattern='*.rst',
                    eval='expand("<afile>")')
    def on_edit(self, filename):
        """Send buffer contents to socketio server via PUT request"""
        buf = self.nvim.current.buffer
        try:
            self.html = publish_string(u"\n".join(buf[:]),
                                  writer_name='html',
                                  settings_overrides={'report_level': 'quiet'})
        except:
            pass
        try:
            requests.put("http://localhost:8000/render", self.html)
        except Exception as err:
            print(filename)
            print(err)

    @neovim.autocmd('BufWritePost',
                    pattern='*.rst',
                    eval='expand("<afile>")')
    def make_html(self, filename):
        """Send html contents to socketio server via PUT request"""
        if self.has_makefile:
            try:
                check_output(['make', 'html'], cwd=self.makefile_dir)
                requests.put("http://localhost:8000/render", filename)
            except Exception as err:
                print(filename)
                try:
                    requests.put("http://localhost:8000/render", err)
                except:
                    print(err)

    @neovim.autocmd('VimLeavePre', pattern='*.rst')
    def quit_webserver(self):
        try:
            requests.put("http://localhost:8000/quit")
            self.proc.terminate()
            with open("/Users/tomdfleming/anotherthing.txt", "w") as f:
                f.write("well, it got here. so why isn't it quitting?")
        except Exception as e:
            with open("/Users/tomdfleming/anotherthing.txt", "w") as f:
                f.write(str(e))

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
