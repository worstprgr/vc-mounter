#!/usr/bin/env python3
"""
VC-Mounter
This tool simplifies mounting and dismounting containers with *keyfiles* on VeraCrypt.

Copyright (C) 2023  worstprgr <adam@seishin.io> GPG Key: key.seishin.io

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import configparser
import argparse
import pathlib
import subprocess
import sys
from argparse import RawTextHelpFormatter
from dataclasses import dataclass, asdict


@dataclass
class Keywords:
    volume: str = '/v'
    tryemptypass: str = '/tryemptypass'
    keyfiles: str = '/k'
    driveletter: str = '/l'
    nowaitdlg: str = '/nowaitdlg'
    savehistory: str = '/h'


class ExpectedValues:
    expected_values: list = [
        list,
        ('yes', 'no'),
        str,
        str,
        ('yes', 'no'),
        ('yes', 'no')
    ]


class Root:
    config_file: str = 'mount.ini'
    path_config: str = 'path.conf'
    veracrypt_cmd: list[str] = ['veracrypt']
    standard_args: list[str] = ['/q', '/b']
    dismount_arg: str = '/d'


class ArgParseHelper:
    def __init__(self):
        dry_help: str = "If provided, it won't execute the VeryCrypt commands. Used for debugging."
        dismount_help: str = 'If provided, it dismounts the loaded volume(s)'
        description: str = 'This tool mounts and dismounts container, based on a configuration file.\n' \
                           'You can pass multiple configuration, separated by a whitespace.\n\n' \
                           'Further Options & Examples:\n' \
                           '`mount.py all`\t\t- Mounts all configured containers.\n' \
                           '`mount.py all -d`\t- Dismounts all configured containers.\n' \
                           '`mount.py show`\t\t- Shows all configured containers\n' \
                           '`mount.py Cont1 Cont2`\t- Mounts two of the configured containers.'
    
        parser = argparse.ArgumentParser(description=description, formatter_class=RawTextHelpFormatter)
        parser.add_argument('container', nargs='+', type=str)
        parser.add_argument('-d', '--dismount', action='store_true', help=dismount_help)
        parser.add_argument('-x', '--dry', action='store_true', help=dry_help)
        
        args = parser.parse_args()
        self.container: list = args.container
        self.dismount: bool = args.dismount
        self.dryrun: bool = args.dry
        

class Manager(Root, ArgParseHelper, ExpectedValues):
    def __init__(self):
        Root.__init__(self)
        ArgParseHelper.__init__(self)
        ExpectedValues.__init__(self)
        
        self.path_conf_fp: pathlib.Path = pathlib.Path(self.path_config)
        
        self.create_path_config()
        self.config_fp = self.read_path_config()
        
        self.config = configparser.ConfigParser()
        self.config.read(self.config_fp)
        
        self.veracrypt: str = self.veracrypt_cmd
        self.keywords: dict = asdict(Keywords())
        self.base_command: list[str] = self.veracrypt + self.standard_args
        
        self.exclude_sections: list[str] = ['Path']
        self.argparse_keywords: list[str] = ['all', 'show']
        self.exlude_reserved: list[str] = self.exclude_sections + self.argparse_keywords
        
        self.drylog('Dry Run active')

    def main(self) -> None:
        self.config_integrity_check()
        self.show_all_containers()
        sections: list[str] = self.container
        
        if len(sections) > 1:
            for section in sections:
                self.dismount_or_mount(section)
        elif sections[0] == self.argparse_keywords[0]:
            self.dismount_or_mount_all()
        else:
            self.dismount_or_mount(sections[0])

    def config_integrity_check(self) -> None:
        def check_value(index: int, _section: str, _key: str, val: str) -> bool:
            ev: list[any] = self.expected_values
            
            if type(ev[index]) == type:
                if val != '':
                    return False
                else:
                    self.err(f'{self.config_file}: Section "{_section}" contains an unexpected value. '
                             + f'Option "{_key}" is empty, please provide a value')
            elif type(ev[index]) == tuple:
                if val in ev[index]:
                    return False
                else:
                    self.err(f'{self.config_file}: Section "{_section}" contains an unexpected value. '
                             + f'Only {ev[index]} allowed in option "{_key}"')
            return True
    
        # Checking, if config file exists
        self.check_and_create_config()
    
        error: bool = False
        sections: list[str] = self.config.sections()
        
        # Checking, if user input is equal to the config sections
        for item in self.container:
            if self.ignore_sections(item):
                continue
            if item not in sections:
                self.err(f'{self.config_file}: Section "{item}" not found')
                error = True
        self.terminate(error)
             
        # Checking, if every option is present
        expected_keys: list = [x for x in self.keywords.keys()]
        options: list = []
        
        for section in sections:
            if self.ignore_sections(section):
                continue
            options = list(self.config[section])
            if len(expected_keys) != len(options):
                self.err(f'{self.config_file}: Section "{section}" is missing option(s)')
                error = True
                
        if error:
            print('\t Accepted options:')
            for option in options:
                print(f'\t\t- {option}')
        self.terminate(error)
          
        # Checking, if every option has a value
        for section in sections:
            options: list = list(self.config[section])
            
            for i, key in enumerate(options):
                value = self.config[section][key]
                error = check_value(i, section, key, value)  
        self.terminate(error)

    def check_and_create_config(self) -> None:
        if not self.config_fp.exists():
            cfg_content: list[str] = ['[MyContainerName]\n']
            cfg_content += [f'{x} = \n' for x in self.keywords.keys()]

            try:
                with open(self.config_fp, 'w+', encoding='utf8') as f:
                    f.writelines(cfg_content)
                    
                print(f'[INFO]: File "{self.config_file}" does not exist. Created config with examples.')
                print('[INFO]: Please add your configuration to it.')
            except FileNotFoundError:
                self.err(f'Can not find "{self.config_fp}". Maybe the folder does not exist.')
            sys.exit(0)

    def create_path_config(self) -> None:
        if not self.path_conf_fp.exists():
            path_conf_content: str = str(self.config_file)
            print(f'[INFO]: File "{self.path_config}" does not exist. Creating path config ...')
            
            with open(self.path_conf_fp, 'w+', encoding='utf8') as f:
                f.write(path_conf_content)
                
            print(f'[INFO]: File created. Optional: Add a custom path to your "{self.config_file}" file.')
                
    def read_path_config(self) -> pathlib.Path | None:
        if self.path_conf_fp.exists():
            with open(self.path_conf_fp, 'r', encoding='utf8') as f:
                content = f.read()
            return self.__conv_path(content.strip())
        self.err(f'Can not find {self.path_conf_fp}')
        sys.exit(0)

    def show_all_containers(self):
        if self.container[0] == self.argparse_keywords[1]:
            print('[INFO]: Configured containers:') 
            for section in self.config.sections():
                if self.ignore_sections(section):
                    continue
                print('[INFO]:\t-', section)
            sys.exit(0)

    def dismount_or_mount_all(self):
        sections = self.config.sections()
        for section in sections:
            self.dismount_or_mount(section)

    def dismount_or_mount(self, section: str) -> None:
        if self.dismount:
            self.dismount_volume(section)
        else:
            self.mount_volume(section)    

    def get_config_values(self, usr_section: str) -> list:
        values: list = []
        section = self.config[usr_section]
        
        for key in self.keywords.keys():
            value = section[key]
            values.append(value)
        return values     
        
    def dismount_volume(self, usr_section) -> None:
        if usr_section not in self.exlude_reserved:
            command: list[str] = self.base_command.copy()
            command += [self.dismount_arg, self.config[usr_section]['driveletter']]
            
            self.drylog('#'*7 + f' {usr_section} ' + '#'*7, True)
            self.drylog(' '.join(command))
            self.drylog(command)
            
            if not self.dryrun:
                subprocess.run(command)
      
    def mount_volume(self, section) -> None:
        if section not in self.exlude_reserved:
            values: list = self.get_config_values(section)
            command: list[str] = self.base_command.copy()
        
            for index, (var_name, var_value) in enumerate(self.keywords.items()):              
                command.append(var_value)
                command.append(values[index])
        
            self.drylog('#'*7 + f' {section} ' + '#'*7, True)
            self.drylog(' '.join(command) + '\n')
            self.drylog(command)
            if not self.dryrun:
                subprocess.run(command)
       
    @staticmethod
    def __conv_path(fp: str) -> pathlib.Path:
        return pathlib.Path(fp)
        
    def drylog(self, message: str, pre_newline: bool = False) -> str:
        if self.dryrun:
            if pre_newline:
                print('\n\n[Debug]:', message)
            else:
                print('[Debug]:', message)
                
    def ignore_sections(self, section: str) -> bool | None:
        return section in self.exlude_reserved
                
    @staticmethod    
    def err(message: str) -> str:
        print(f'[ERROR]: {message}')
        
    @staticmethod
    def terminate(is_err: bool) -> None:
        if is_err:
            print('[Shutdown]')
            sys.exit(1)
    
    
if __name__ == '__main__':    
    m = Manager()
    m.main()
