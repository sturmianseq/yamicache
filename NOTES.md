# Project Notes

## Deploying

1.  Make sure all tests pass:  
`python -m flake8 --ignore=E501 yamicache && coverage run --source=yamicache -p -m py.test && coverage combine && coverage report -m`
1.  push to GitHub
1.  wait for Travis to show passing
1.  bump the version: `python manage.py ver rev`
1.  update `HISTORY.rst` with the new version information
1.  add/commit/push the new version info w/ `[skip ci] prep for release`
1.  create a tag with `python manage.py ver tag`  
    NOTE: This will push any checked-in changes and the new tag
1.  build the packages: `python manage.py build dist`
1.  upload to pypi: `twine upload dist/*`
