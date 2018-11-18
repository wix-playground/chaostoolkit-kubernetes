default: prepare test

prepare:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

format:
	autopep8 --in-place --recursive chaosk8s_wix

lint:
	pycodestyle --first  --max-line-length=120 chaosk8s_wix

build:
	python setup.py build

release: build
	python setup.py release
	pip install twine
	twine upload dist/* -u ${PYPI_USER_NAME} -p ${PYPI_PWD}

test: format
	python3 -m pytest
