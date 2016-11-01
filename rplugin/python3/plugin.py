"""Sends vim buffer to socketio server"""

import os
import sys
from subprocess import check_output
from multiprocessing import Process

import neovim
import psutil
import requests
from docutils.core import publish_string

HERE = os.path.dirname(os.path.abspath(os.path.expanduser(__file__)))
sys.path.insert(0, "{}/server".format(HERE))
import sio

# Try redirecting stdout to avoid conflicts with msgpack...
# See: https://github.com/neovim/neovim/issues/2283
sys.stdout = open(os.devnull)


@neovim.plugin
class TestPlugin(object):
    """Plugin for live-previewing RST (and other?) documents"""

    def __init__(self, nvim):
        self.nvim = nvim
        self.server_started = False
        self.html = u'Refreshing...'

    @neovim.autocmd('BufEnter',
                    pattern='*.rst',
                    eval='expand("<afile>")',
                    sync=True)
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
                check_output(['open', '-g', 'http://localhost:8123'])
                requests.put("http://localhost:8123/render", 'starting server...')
            except Exception as e:
                with open("/Users/tomdfleming/anotherthing.txt", "w") as f:
                    f.write(str(e))

    @neovim.autocmd('CursorMoved,CursorMovedI',
                    pattern='*.rst',
                    eval='expand("<afile>")',
                    sync=True)
    def on_edit(self, filename):
        """Send buffer contents to socketio server via PUT request"""
        try:
            buf = self.nvim.current.buffer
            self.html = publish_string(u"\n".join(buf[:]),
                                       writer_name='html',
                                       settings_overrides={'report_level': 4})
            #with open("/Users/tomdfleming/raw.html", "w") as f:
            #    f.write(self.html.decode('utf-8'))
        except Exception as err:
            requests.put("http://localhost:8123/render", str(err))
        try:
            requests.put("http://localhost:8123/render", self.html)
        except Exception as err:
            print(filename)
            print(err)

    #@neovim.autocmd('BufWritePost',
    #                pattern='*.rst',
    #                eval='expand("<afile>")')
    def make_html(self, filename):
        """Send html contents to socketio server via PUT request"""
        if self.has_makefile:
            try:
                check_output(['make', 'html'], cwd=self.makefile_dir)
                requests.put("http://localhost:8123/render", filename)
            except Exception as err:
                print(filename)
                try:
                    requests.put("http://localhost:8123/render", err)
                except:
                    print(err)

    @neovim.autocmd('VimLeavePre', pattern='*.rst')
    def quit_webserver(self):
        try:
            requests.put("http://localhost:8123/quit")
            thispid = os.getpid()
            thatpid = self.proc.pid
            self.proc.terminate()

            with open("/Users/tomdfleming/sidepid.txt", "w") as f:
                f.write("{} {} NA".format(thispid, thatpid))

            # Neovim seems to be launching a duplicate process for some
            # reason when the child process gets created, and doesn't
            # quit the process on exit. Foricbly remove it until the
            # root cause can be found
            for p in psutil.process_iter():
                if 'python' in p.name():
                    searchstr = "yalp-nvim/rplugin/python3/plugin.py"
                    if searchstr in "".join(p.cmdline()):
                        if p.pid != thispid:
                            with open("/Users/tomdfleming/sidepid.txt", "w") as f:
                                f.write("{} {} {}".format(thispid, thatpid, p.pid))
        except Exception as e:
            print(e)
            with open("/Users/tomdfleming/sidepid.txt", "w") as f:
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
