# Project Notes

## Deploying

1.  test: `flake8 --ignore=E501 yamicache && pytest`
1.  push to GitHub
1.  wait for Travis to show passing
1.  bump the version: `bumpversion --help` (e.g. `bumpversion minor`)  
    this will also create the tag
1.  modify the release notes
1.  push the new version & release notes (you can add `[skip ci]` for this one)  
    **NOTE**: push this with `git push --tags` to update to the new tag created
    by `bumpversion`.
1.  build the packages: `python setup.py sdist bdist_wheel`
1.  upload to pypi: `twine upload dist/*`

## Coverage testing

This command should be run before accepting a PR.  This is also ran by Travis-CI

    coverage run --source=yamicache -p -m py.test && coverage combine && coverage report -m
