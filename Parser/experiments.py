#! /usr/bin/env python

from time import sleep
# x = input('> ')
# print(list(x))

cont = True

try:
    for i in range(1000):
        sleep(1)
        if not cont:
            break
except KeyboardInterrupt:
    print("Gotcha2.")
    cont = True
