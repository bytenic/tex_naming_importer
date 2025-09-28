@echo off
REM この bat はどこから実行しても OK。bat の位置から Python/tests を探して走らせる。
setlocal

REM Python ディレクトリへ移動
pushd "%~dp0"

python -m unittest discover -s tests -p "test_*.py" -v
set "CODE=%errorlevel%"

popd
exit /b %CODE%