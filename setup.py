import os
import sys
from setuptools import setup, find_packages

version = '1.9.2'

if sys.version_info < (2, 6):
    sys.stderr.write("This package requires Python 2.6 or newer. "
                     "Yours is " + sys.version + os.linesep)
    sys.exit(1)

# a sufficient version of pip is needed to parse Odoo requirement file
# version 1.4.1 is the one required by reportlab anyway
# (temporary fixing to 1.5.6 to stop conflating of issues)
requires = ['setuptools', 'zc.recipe.egg', 'zc.buildout>=2.2.0', 'pip==1.5.6']

if sys.version_info < (2, 7):
    requires.append('ordereddict')
    requires.append('argparse')

setup(
    name="anybox.recipe.odoo",
    version=version,
    author="Anybox",
    author_email="contact@anybox.fr",
    description="A buildout recipe to install and configure Odoo",
    license="AGPLv3+",
    long_description='\n'.join((
        open('README.rst').read(),
        open('CHANGES.rst').read())),
    url="https://github.com/anybox/anybox.recipe.odoo",
    packages=find_packages(),
    namespace_packages=['anybox', 'anybox.recipe'],
    zip_safe=False,
    include_package_data=True,
    install_requires=requires,
    tests_require=requires + ['nose', 'bzr'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Buildout :: Recipe',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU Affero General Public License v3 or '
        'later (AGPLv3+)',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    entry_points={'zc.buildout': [
        'server = anybox.recipe.odoo.server:ServerRecipe',
    ]},
    extras_require={'bzr': ['bzr']},
)
