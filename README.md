# nautilus-git
Nautilus extension to add important information about the current git directory

## Screenshots

 <div align="center"><img src="screenshots/screenshot1.png" alt="Preview" /></div>


## Requirements:
### Runing dependecies
`python2` : I would use Python3 but Nautilus extensions works only with Python2

`nautilus-python`

`git`
### Building dependehttps://github.com/bil-elmoussaoui/nautilus-gitncies
`meson`

`ninja`


## How to install 
1. Install requirements
2. Clone the repository 
	```bash
	git clone https://github.com/bil-elmoussaoui/nautilus-git
	```
3. Build it!
	```bash
	cd nautilus-git 
	mkdir build
	cd build
	meson .. --prefix /usr
	ninja
	sudo ninja install
	``` 
4. Restart Nauitlus 
	```bash
	nautilus -q
	```

## Credits
The `nautilus-git-symbolic` icon was designed by gitg design team.