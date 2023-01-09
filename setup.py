from setuptools import setup, find_packages

setup(
    name='base4096',
    version='1.0',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        '': ['*.py'],
    },
    description='Base4096 encoding and decoding functions',
    author='Josef Kulovany',
    author_email='charg.chg.wecharg@gmail.com',
    url='https://github.com/ZCHGorg/base4096',
    license='MIT',
    keywords='base4096 encoder decoder',
    install_requires=[],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: ZCHG.ORG LICENSE',
        'Operating System :: OS Independent',
    ],
)
