#!/bin/bash

cd /Users/iainmuir/PycharmProjects/Desktop/PersonalProjects/Information-Aggregator || exit
source bin/activate
datapane login --token=55010cebc170ecfbeddb82838c360776bf36f6be
jupyter nbconvert --to notebook --execute aggregator.ipynb --output aggregator.ipynb
deactivate