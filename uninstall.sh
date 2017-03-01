#!/bin/bash
 if [ "$(id -u)" != "0" ]; then
    echo "This script must be run as root" 1>&2
    exit 1
fi
if [ -z  "$1" ]; then
   PREFIX=/usr
else
    PREFIX=$1
fi

git_file=$PREFIX/share/nautilus-python/extensions/git.py
icon_file=$PREFIX/share/icons/hicolor/scalable/status/nautilus-git-symbolic.svg
files=($git_file $icon_file)

echo "Uninstalling nautilus-git"
for index in ${!files[*]}
do
    file=${files[$index]}
    if [ -f $file ]; then
        echo "${file} was removed successfully"
        rm -f $file
    else
        echo "${file} was not found..."
    fi
done
