import setuptools

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name='o365_notifications',
    version='0.0.1',
    author='Renato Damas',
    author_email='me@renatodamas.com',
    description='A small example package',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/rena2damas/o365-notifications',
    project_urls={
        'Bug Tracker': 'https://github.com/rena2damas/o365-notifications/issues',
    },
    classifiers=[
        'O365 :: Notifications',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    package_dir={'': 'src'},
    packages=setuptools.find_packages(where='src'),
    python_requires='>=3.6'
)
