#!/bin/bash

cd /Users/iainmuir/PycharmProjects/Desktop/PersonalProjects/Information-Aggregator || exit
source bin/activate
datapane login --token=55010cebc170ecfbeddb82838c360776bf36f6be
/Users/iainmuir/PycharmProjects/Desktop/PersonalProjects/Information-Aggregator/bin/python3.9 /Users/iainmuir/PycharmProjects/Desktop/PersonalProjects/Information-Aggregator/aggregator.py
deactivate