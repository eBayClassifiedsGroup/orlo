# Python package makefile
#
# Uses git buildpackage, which from debian rules will call dh_virtualenv

test:
	python setup.py test

sdist:
	python setup.py sdist

clean:
	debuild clean

debian:
	debuild -us -uc

changelog:
	gbp dch --ignore-branch --auto --commit

.PHONY: debian sdist test clean changelog
