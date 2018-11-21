@echo off
set PATH=%CD%\expyvr\lib;%CD%\python26\bin;%PATH%
set EXPYVRROOT=%CD%
cd expyvr\src\controller
..\..\..\python26\python.exe runexperiment.py