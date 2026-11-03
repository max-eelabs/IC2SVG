@echo off
REM Copyright 2026 Maxim Pavlov pavlov.web@gmail.com
REM
REM Licensed under the Apache License, Version 2.0 (the "License");
REM you may not use this file except in compliance with the License.
REM You may obtain a copy of the License at
REM
REM     http://www.apache.org/licenses/LICENSE-2.0
REM
REM Unless required by applicable law or agreed to in writing, software
REM distributed under the License is distributed on an "AS IS" BASIS,
REM WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
REM See the License for the specific language governing permissions and
REM limitations under the License.
REM
REM SPDX-License-Identifier: Apache-2.0

setlocal EnableExtensions DisableDelayedExpansion
pushd "%~dp0..\..\.."
if errorlevel 1 exit /b 1

set "IC_PYTHON=python"
if exist ".venv\Scripts\python.exe" set "IC_PYTHON=.venv\Scripts\python.exe"

"%IC_PYTHON%" -m components.input "%~dp0ap2151dwg-7.json" "%~dp0ap2151dwg-7-horizontal.svg" --orientation landscape
if errorlevel 1 goto failed

"%IC_PYTHON%" -m components.input "%~dp0ap2151dwg-7.json" "%~dp0ap2151dwg-7-vertical.svg" --orientation portrait --content-scale 0.5
if errorlevel 1 goto failed

popd
exit /b 0

:failed
popd
exit /b 1
