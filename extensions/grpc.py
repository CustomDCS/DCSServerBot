import luadata
import os
import re

from core import Extension, Server
from typing import Optional, Any, TextIO


class gRPC(Extension):

    def __init__(self, server: Server, config: dict):
        self.home = os.path.join(server.instance.home, 'Mods', 'tech', 'DCS-gRPC')
        super().__init__(server, config)

    @property
    def name(self):
        return 'DCS-gRPC'

    @staticmethod
    def parse(value: str) -> Any:
        if value.startswith('{'):
            return value[1:-1].split(',')
        elif value.startswith('"'):
            return value.strip('"')
        elif value == 'true':
            return True
        elif value == 'false':
            return False
        elif '.' in value:
            return float(value)
        else:
            return int(value)

    def load_config(self) -> Optional[dict]:
        def read_file(file: TextIO, cfg: dict):
            for line in file.readlines():
                match = exp.match(line)
                if match:
                    key = match.group('key').strip()
                    if key.startswith('--'):
                        continue
                    value = match.group('value').strip(' ,')
                    cfg[key] = self.parse(value)

        exp = re.compile(r'(?P<key>.*) = (?P<value>.*)')
        path = os.path.join(self.server.instance.home, 'Config', 'dcs-grpc.lua')
        cfg = dict()
        if os.path.exists(path):
            with open(path, 'r') as file:
                read_file(file, cfg)
        return cfg

    async def prepare(self) -> bool:
        config = self.config.copy()
        if 'enabled' in config:
            del config['enabled']
        if len(config):
            config = self.locals | config
            config['autostart'] = True
            path = os.path.join(self.server.instance.home, 'Config', 'dcs-grpc.lua')
            data = luadata.serialize(config, indent='', indent_level=0).encode('utf8')[1:-1]
            with open(path, 'wb') as outfile:
                outfile.write(data)
        return await super().prepare()

    def is_installed(self) -> bool:
        if not self.config.get('enabled', True):
            return False
        if not os.path.exists(os.path.join(self.server.instance.home, 'Config', 'dcs-grpc.lua')):
            self.log.error(f"  => {self.server.name}: Can't load extension, DCS-gRPC not correctly installed.")
            return False
        if not os.path.exists(os.path.join(self.home, 'dcs_grpc.dll')):
            self.log.error(f"  => {self.server.name}: Can't load extension, DCS-gRPC not correctly installed.")
            return False
        return True
