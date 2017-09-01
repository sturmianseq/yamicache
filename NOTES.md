# Project Notes

## Deploying

1.  test: `flake8 --ignore=E501 yamicache && pytest`
1.  push to GitHub
1.  wait for Travis to show passing
1.  bump the version: `bumpversion --help`
1.  tag the version (TBD)
1.  push to GitHub
1.  wait for Travis to show passing
1.  build the packages: `python setup.py sdist bdist_wheel`
1.  upload to pypi: `twine upload dist/*`

## Coverage testing

    coverage run --source=yamicache -p -m py.test && coverage combine && coverage report -m
