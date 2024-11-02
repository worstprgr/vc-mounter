# VC Mounter
## Description
This tool simplifies mounting and dismounting containers with *keyfiles* on VeraCrypt via the CLI.

> [!Warning]  
> Place the config file to a safe space, that is encrypted too!

> [!Warning]
> This tool only supports Windows. Initially I wanted to support Linux as well, but I'm using bash scripts & aliases for my Veracrypt containers in Linux.
> And so far, this approach is sufficient enough for me. But feel free to fork it and open a PR.

## PSA
Always check, if a tool writes or reads into your container or keyfiles. Even if a tool has not a
malicious intent, file IO could corrupt files and destroy your keyfiles/containers.  

More information about that [topic](https://veracrypt.fr/en/Avoid%20Third-Party%20File%20Extensions.html).  

This tool is designed to pass arguments to VeraCrypt. It only reads and writes to its own configuration files.  

## Installation
Invoke this tool with `python main.py show`. It creates two files:  
- `path.conf`
- `mount.ini`

The `path.conf` holds the path to the `mount.ini`, so you can configure it as you like. 
And the `mount.ini` contains various configurations for mounting containers.

### mount.ini
The options are adapted from [VeraCrypt](https://www.veracrypt.fr/en/Command%20Line%20Usage.html). 
You can create multiple sections for every container you want to mount.

|                       |               |                                                                                                                     |
|-----------------------|---------------|---------------------------------------------------------------------------------------------------------------------|
| **[MyContainerName]** | string        | The config name is also the name, how you'll call it via arguments                                                  |
| **volume**            | path          | Absolute path to your container                                                                                     |
| **tryemptypass**      | *yes* or *no* | Yes: Tries an empty password first, if it fails, a password prompt appears. No: forces a password prompt.           |
| **keyfiles**          | path          | Absolute path to your keyfile or a folder, that contains (only) your keyfiles. Let it empty, if you have no keyfile |
| **driveletter**       | string        | The drive letter that should be used                                                                                |
| **nowaitdlg**         | *yes* or *no* | No: it won't display a progress bar, while mounting and dismounting                                                 |
| **savehistory**       | *yes* or *no* | No: disables saving history of mounted volumes                                                                      |
| **securedesktop**     | *yes* or *no* | No: disables the secure desktop                                                                                     |

### Example mount.ini
```ini
[Foo]
volume = C:/containers/container_foo.file
tryemptypass = yes
keyfiles = C:/containers/keys/foo/foo.key
driveletter = f
nowaitdlg = yes
savehistory = no
securedesktop = no

[Bar]
volume = C:/containers/container_bar.file
tryemptypass = no
keyfiles = 
driveletter = g
nowaitdlg = no
savehistory = no
securedesktop = yes
```

## Usage
After you set up the configuration, you can mount your container by using their configuration names:  
`python main.py MyContainerName`  

Dismount:  
`python main.py MyContainerName -d`  

Mount multiple container:  
`python main.py Foo1 Bar1 Foo2 Bar2`  

Dismount multiple container:  
`python main.py Foo1 Bar1 Foo2 Bar2 -d`  

Mount all container inside the config:  
`python main.py all`  

Dismount all:  
`python main.py all -d`  

Show all containers you configured:  
`python main.py show`  


## Available Arguments

|                  |                |                                                                           |
|------------------|----------------|---------------------------------------------------------------------------|
| \<container> ... | first position | Which configuration should be loaded                                      |
| show             | first position | Shows all configuration names                                             |
| all              | first position | Loads all configurations                                                  |
| -d, --dismount   | optional       | If provided, it dismounts the loaded volume(s)                            |
| -x, --dry        | optional       | If provided, it won't execute the VeryCrypt commands. Used for debugging. |


