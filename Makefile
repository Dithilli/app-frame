.PHONY: install

run:
	 FLASK_APP="ecselfservice" FLASK_ENV="development" flask run

dev:
	python setup.py develop

install:
	python setup.py install
