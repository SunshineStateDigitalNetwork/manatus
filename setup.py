from setuptools import setup, find_packages

setup(
    name='manatus',
    version='1.0.1',
    packages=find_packages(),
    url='http://github.com/SunshineStateDigitalNetwork/manatus',
    license='MIT',
    author='Matthew Miguez',
    author_email='r.m.miguez@gmail.com',
    description='Metadata aggregation and transformation library',
    long_description=open('README.rst').read() + '\n\n' +
                     open('CHANGES.rst').read(),
    platforms='any',
    install_requires=[
        'pymods>=2.0.9',
        'sickle>=0.7.0',
        'requests'
    ],
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Text Processing :: Markup :: XML',
    ],
    test_suite='manatus.tests',
    keywords='oai-pmh metadata digital-libraries',
)
