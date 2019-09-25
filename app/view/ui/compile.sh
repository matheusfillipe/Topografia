#!/bin/bash
for i in *.ui; do pyuic5 -o "py/$i.py" $i; done

