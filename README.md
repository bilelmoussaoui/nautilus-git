# nautilus-git
Nautilus extension to add important information about the current git directory

## Screenshots

 <div align="center"><img src="screenshots/screenshot1.png" alt="Preview" /></div>


## Requirements:
### Runing dependecies
- `python2` : I would use Python3 but Nautilus extensions works only with Python2
- `nautilus-python`
- `git`

### Building dependencies
- `meson`
- `ninja`
- `intltool`
- `gtk+-3.0`
- `gobject-introspection`:
  - Debian/Ubuntu : `libgirepository1.0-dev` 
  - Fedora : `gobject-introspection-devel`

## How to install 
1- Install requirements

2- Clone the repository 
```bash
git clone https://github.com/bil-elmoussaoui/nautilus-git
```
3- Build it!
```bash
cd nautilus-git 
mkdir build
cd build
meson .. --prefix /usr
sudo ninja install
``` 
4- Restart Nautilus 
```bash
nautilus -q
```

## How to uninstall

1- Download the uninstallation file
```bash
cd /tmp && wget -O uninstall.sh https://raw.githubusercontent.com/bil-elmoussaoui/nautilus-git/master/uninstall.sh
```
2- Make the file executable
```bash
chmod +x ./uninstall.sh
```
3- Run it!
```bash
sudo ./uninstall.sh /usr

```
PS : Replace `/usr` with whatever installation prefix you have chosen before.

## Credits
The `nautilus-git-symbolic` icon was designed by gitg design team.
