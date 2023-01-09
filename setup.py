from setuptools import setup, find_packages

setup(
    name='base4096',
    version='1.0',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        '': ['*.py'],
    },
    description='A custom base 4096 encoding and decoding library',
    author='Josef Kulovany',
    author_email='charg.chg.wecharg@gmail.com',
    url='https://github.com/ZCHGorg/Base4096/blob/main/Base4096',
    install_requires=[base4096.py],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: ZCHG.org License',
        'Operating System :: OS Independent',
    ],
)
