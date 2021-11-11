#!/usr/bin/env bash
case $1 in 
  discover)
    vdirsyncer discover "${@:2}"
    ;;

  repair)
    vdirsyncer repair "${@:2}"
    ;;

  *)
    update-phonebook.py "$@"
    ;;
esac
