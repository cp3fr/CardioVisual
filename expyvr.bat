@echo off
set PATH=%CD%\expyvr\lib;%CD%\python26\bin;%PATH%
set EXPYVRROOT=%CD%
cd expyvr\src\expbuilder\app
..\..\..\..\python26\python.exe builder.py