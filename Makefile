# Python package makefile
#
# Uses git buildpackage, which from debian rules will call dh_virtualenv

test:
	tox

sdist:
	python setup.py sdist

clean:
	@python setup.py clean
	@debuild clean
	@rm -rf .tox

deb: clean
	debuild -us -uc

changelog:
	gbp dch --ignore-branch --auto --commit

.PHONY: debian sdist test clean changelog
