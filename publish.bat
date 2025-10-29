rd /s /q  dist
rd /s /q  build
rd /s /q  pytest_assist.egg-info

python -m build --wheel && twine upload dist/*.whl

pause