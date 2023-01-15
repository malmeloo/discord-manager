import logging
import os
import subprocess
import threading
from enum import Enum
from typing import Optional
import selectors

import psutil

import util
from instance import DiscordInstance

logging.getLogger(__name__)


class ProcessError(Exception):
    pass


class ProcessState(Enum):
    RUNNING = 1
    STOPPED = 0


def _prepare_instance(instance: DiscordInstance):
    """
    Prepares an instance by symlinking its config directory
    :param instance: the instance to prepare
    :return: boolean
    """
    orig_conf = util.get_original_discord_config_dir(instance.edition)
    if os.path.islink(orig_conf):  # is linked, so presumably managed by us. Safe to re-link.
        os.unlink(orig_conf)
    elif os.path.exists(orig_conf):  # there's something here but it isn't linked... likely existing installation
        raise ProcessError(f'Path exists, unsafe to continue: {orig_conf}')

    # re-link to our custom config directory (and create it if not exists)
    os.symlink(instance.data_dir, orig_conf)
    os.makedirs(instance.data_dir, exist_ok=True)

    return True


class DiscordProcess:
    def __init__(self, instance: DiscordInstance):
        self.instance = instance
        self._proc: Optional[subprocess.Popen] = None

        self._thread = threading.Thread(target=self._process_loop)

    def _try_kill_others(self):
        """
        Tries to gracefully stop other Discord processes running as the same edition (to prevent conflicts)
        :return: True if success
        """
        # first gather all processes, sorting them by create time so we target the parent process first
        processes = []
        for proc in psutil.process_iter():
            if proc.name() == self.instance.edition.executable:
                processes.append(proc)
        processes = sorted(processes, key=lambda p: p.create_time())

        # now actually kill them
        for proc in processes:
            if not proc.is_running():
                continue

            proc.terminate()
            try:
                proc.wait(timeout=5)
            except psutil.TimeoutExpired:  # we asked nicely...
                proc.kill()

    def _process_loop(self):
        # use selectors for stdout/stderr multiplexing
        sel = selectors.DefaultSelector()
        sel.register(self._proc.stdout, selectors.EVENT_READ)
        sel.register(self._proc.stderr, selectors.EVENT_READ)

        while (ret := self._proc.poll()) is None:
            for key, _ in sel.select():
                line = key.fileobj.readline().decode('utf-8').strip()
                if not line:
                    continue

                if key.fileobj is self._proc.stdout:  # is stdout
                    print(f'STDOUT - {line}')
                else:
                    print(f'STDERR - {line}')

        print('Exittt')
        logging.info(f'Process exited - {ret}')

    def start(self):
        self._try_kill_others()
        _prepare_instance(self.instance)

        self._proc = subprocess.Popen([
            f'{self.instance.app_dir}/{self.instance.edition.executable}'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self._thread.start()
