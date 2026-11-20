#!/bin/zsh
# Launch from this folder so relative resources resolve correctly.
cd -- "${0:A:h}" || exit 1
if [[ ! -x .venv/bin/python ]]; then
  print "Python environment missing. Follow Setup instructions in README.md."
  read -r "reply?Press Return to close. "
  exit 1
fi
exec .venv/bin/python main.py
